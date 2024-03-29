from __future__ import print_function
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict
import uuid

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

from allauth.socialaccount.models import SocialToken

from main import models
from moodle.models import (
    MdlUserEnrolments, MdlCohortMembers, MdlRoleAssignments)
from schedule_nubip.settings import DEBUG

SOURCE_NAME = 'scheduleNUBIP'


class CalendarException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Event:

    @staticmethod
    def create_from_api_dict(init_dict: Dict) -> 'Event':
        new_event = Event()

        new_event.id = init_dict.get('id')
        new_event.uuid = new_event.parseUUID(init_dict.get('iCalUID'))
        new_event.summary = init_dict.get('summary', '')
        new_event.description = init_dict.get('description', '')
        new_event.location = init_dict.get('location', '')
        new_event.start_date_time, new_event.end_date_time = (
            new_event.parse_dates(init_dict['start'].get('dateTime'),
                                  init_dict['end'].get('dateTime'))
        )
        new_event.interval, new_event.until = new_event.parse_recurrence(
            init_dict['recurrence'])

        return new_event

    @staticmethod
    def create_from_lesson(lesson: models.Lesson) -> 'Event':
        new_event = Event()

        new_event.uuid = lesson.id
        new_event.summary = lesson.subject.title
        new_event.location = lesson.location
        new_event.start_date_time = lesson.start_date_time
        new_event.end_date_time = lesson.end_date_time
        new_event.interval = 1 if lesson.weekfrequency == \
            models.WeekFrequency.EACH_WEEK else 2
        new_event.until = lesson.semester.enddate
        new_event.description = ''

        return new_event

    @staticmethod
    def parse_dates(start: str, end: str):
        start_date_time, end_date_time = None, None
        if start:
            start_date_time = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')
        if end:
            end_date_time = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S%z')
        return start_date_time, end_date_time

    @staticmethod
    def parseUUID(id: str):
        if not id:
            return None
        if '@' in id:  # 141jrtl3jin9tbssql0ndvkpf4@google.com
            id = id.split('@')[0]
        try:
            return uuid.UUID(id)
        except ValueError:
            return uuid.uuid4()

    @staticmethod
    def parse_recurrence(recurrence_list):
        if len(recurrence_list) != 1:
            return None, None

        recurrence_parts = recurrence_list[0].split(';')

        interval, until = 0, None
        for part in recurrence_parts:
            if 'INTERVAL' in part:
                interval = int(part.split('=')[1])

            if 'UNTIL' in part:
                until = part.split('=')[1]
                try:
                    until = datetime.strptime(until, '%Y%m%d').date()
                except ValueError:
                    until = datetime.strptime(until, '%Y%m%dT%H%M%S%z').date()

        return interval, until

    def api_create(self, service):
        print(f'Creating event {self.summary}')
        try:
            service.events().import_(calendarId='primary',
                                     body=self._event_dict).execute()
        except HttpError as error:
            if error.reason == 'The requested identifier already exists.':
                self.api_update(service)

    def api_update(self, service):
        print(f'Updating event {self.summary}')
        service.events().update(calendarId='primary', eventId=self.id,
                                body=self._event_dict).execute()

    def api_delete(self, service):
        print(f'deleting event {self.summary}')
        service.events().delete(calendarId='primary', eventId=self.id,
                                sendNotifications=False).execute()

    @property
    def _event_dict(self):
        return {
            'iCalUID': str(self.uuid),
            'summary': self.summary,
            'location': self.location,
            'description': self.description,
            'start': {
                'dateTime': self.start_date_time.isoformat(),
                'timeZone': 'Europe/Kyiv'
            },
            'end': {
                'dateTime': self.end_date_time.isoformat(),
                'timeZone': 'Europe/Kyiv'
            },
            'source': {
                'title': SOURCE_NAME,
                'url': 'https://localhost:8000'
            },
            'recurrence': [
                f'RRULE:FREQ=WEEKLY;INTERVAL={self.interval};'
                f'UNTIL={self.until.strftime("%Y%m%d")}'
            ]
        }

    def __hash__(self) -> int:
        return hash((self.uuid, self.summary, self.location, self.start_date_time,
                     self.end_date_time, self.interval, self.description, self.until))

    def __eq__(self, other: 'Event') -> bool:
        if not isinstance(other, Event):
            return NotImplemented

        return (self.uuid == other.uuid and
                self.summary == other.summary and
                self.location == other.location and
                self.start_date_time == other.start_date_time and
                self.end_date_time == other.end_date_time and
                self.interval == other.interval and
                self.description == other.description and
                self.until == other.until)

    def __ne__(self, other: 'Event'):
        return not self == other

    def __str__(self):
        return f'{self.uuid} {self.summary}'


class PersonBase:

    def __init__(self, user, mdl_user):
        self.user = user
        self.mdl_user = mdl_user

    def get_calendar_events(self):
        """Connect to user google calendar and return events created by this app

        Returns:
            Dict[int, Event]: Events from user calendar with defined source
        """
        if self.user:
            try:
                social_token = SocialToken.objects.get(account__user=self.user)
            except SocialToken.DoesNotExist:
                raise CalendarException(
                    f'Token was not found for Email {self.user.email}')

            creds = Credentials(token=social_token.token,
                                refresh_token=social_token.token_secret,
                                client_id=social_token.app.client_id,
                                client_secret=social_token.app.secret)
        else:
            raise CalendarException('User not authorisized')

        self.service = build('calendar', 'v3', credentials=creds)

        now = (datetime.utcnow() - timedelta(days=30)).isoformat() + 'Z'
        two_weeks_after = (datetime.utcnow() +
                           timedelta(days=14)).isoformat() + 'Z'

        try:
            events_result = self.service.events().list(calendarId='primary', timeMin=now,
                                                       timeMax=two_weeks_after,
                                                       singleEvents=False).execute()
        except RefreshError:
            raise CalendarException('Refresh Error try to login again')

        api_events = events_result.get('items', [])

        events: Dict[int, Event] = dict()
        for api_event in api_events:
            source = api_event.get('source')
            if not source or source.get('title') != SOURCE_NAME:
                continue
            event_obj = Event.create_from_api_dict(api_event)
            events[event_obj.uuid] = event_obj

        return events

    def delete_calendar(self):
        try:
            events = self.get_calendar_events()
        except CalendarException as e:
            return str(e)

        for _, event in events.items():
            event.api_delete(self.service)

        return f'deleted {len(events)} events'

    def update_calendar(self):
        try:
            events = self.get_calendar_events()
        except CalendarException as e:
            return str(e)

        checked, updated, created, deleted = list(), list(), list(), list()

        lessons = self.search_lessons()
        lessons = lessons.filter(semester__startdate__lt=datetime.now().date(),
                                 semester__enddate__gt=datetime.now().date())
        if not lessons:
            return "No active lessons found for user"
        for lesson in lessons:
            lesson_event = Event.create_from_lesson(lesson)
            lesson_event.description = self.build_description(lesson)
            if lesson.id in events:
                if events[lesson.id] != lesson_event:  # lesson info changed
                    # events created from model doesn't have id
                    lesson_event.id = events[lesson.id].id
                    lesson_event.api_update(self.service)
                    updated.append(lesson.id)
                else:
                    checked.append(lesson.id)
            else:
                events[lesson.id] = lesson_event
                lesson_event.api_create(self.service)
                created.append(lesson.id)

        for id, event in events.items():
            if id in checked or id in updated or id in created:
                continue

            event.api_delete(self.service)
            deleted.append(id)

        result = f'checked: {len(checked)}, updated: {len(updated)}, created: '\
                 f'{len(created)}, deleted: {len(deleted)}'
        return result

    def build_description(self, lesson: models.Lesson):
        return f'<a href="{lesson.meetingurl}">Meeting Url</a>\n'\
               f'type: {lesson.get_type_display()}'

    @property
    def enrolled_course_ids(self):
        return ([id for id in (MdlUserEnrolments.objects
                               .filter(userid=self.mdl_user, status=0)
                               .values_list('enrolid__courseid_id', flat=True))])


class Teacher(PersonBase):

    def search_lessons(self):
        return (models.Lesson.objects.prefetch_related('groups')
                .select_related('subject', 'lesson_number', 'semester')
                .filter(subject__course_id__in=self.enrolled_course_ids))

    def build_description(self, lesson: models.Lesson) -> str:
        description = super().build_description(lesson)
        return f'{description}\ngroups: {[group.name for group in lesson.groups.all()]}'


class Student(PersonBase):

    def search_lessons(self):
        cohorts_names = list(MdlCohortMembers.objects.filter(userid=self.mdl_user)
                             .values_list('cohortid__name', flat=True))

        return (models.Lesson.objects
                .select_related('subject', 'lesson_number', 'semester')
                .filter(groups__name__in=cohorts_names,
                        subject__course_id__in=self.enrolled_course_ids))

    def build_description(self, lesson: models.Lesson) -> str:
        if not hasattr(self, 'course_teachers') or not hasattr(self, 'user_names'):
            course_users = defaultdict(set)
            self.user_names = dict()
            for course_name, user_id, firstname, lastname in (
                MdlUserEnrolments.objects
                .filter(enrolid__courseid__in=self.enrolled_course_ids, status=0)
                .values_list('enrolid__courseid__shortname', 'userid_id',
                             'userid__firstname', 'userid__lastname')
            ):
                course_users[course_name].add(user_id)
                self.user_names[user_id] = f'{firstname} {lastname}'

            teacher_ids = set(MdlRoleAssignments.objects
                              .filter(userid__in=set().union(*course_users.values()),
                                      roleid__shortname='editingteacher')
                              .values_list('userid_id', flat=True)
                              .distinct())

            self.course_teachers = dict()
            for course_name, user_ids in course_users.items():
                self.course_teachers[course_name] = user_ids & teacher_ids

        description = super().build_description(lesson)
        return f'{description}\nteachers: {[self.user_names[name] for name in self.course_teachers.get(lesson.subject.title, [])]}'

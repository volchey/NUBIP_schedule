from __future__ import print_function
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from pprint import pprint
import uuid

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

from allauth.socialaccount.models import SocialToken

from main import models
from moodle.models import (MdlUserEnrolments, MdlCohortMembers, MdlRoleAssignments)
from schedule_nubip.settings import DEBUG

SOURCE_NAME = 'scheduleNUBIP'


class Event:

    # must be passed one of sources
    def __init__(self, init_dict, lesson: models.Lesson = None):
        if init_dict:
            self.id = init_dict.get('id')
            self.uuid = self.parseUUID(init_dict.get('iCalUID'))
            self.summary = init_dict.get('summary', '')
            self.description = init_dict.get('description', '')
            self.location = init_dict.get('location', '')
            self.start_date_time, self.end_date_time = (
                self.parse_dates(init_dict['start'].get('dateTime'),
                                 init_dict['end'].get('dateTime'))
            )
            self.interval, self.until = self.parse_recurrence(init_dict['recurrence'])
        else:
            self.uuid = lesson.id
            self.summary = lesson.subject.title
            self.location = lesson.location
            self.start_date_time = lesson.start_date_time
            self.end_date_time = lesson.end_date_time
            self.interval = 1 if lesson.weekfrequency == models.WeekFrequency.EACH_WEEK else 2
            self.until = lesson.semester.enddate
            self.description = ''

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
        if '@' in id: # 141jrtl3jin9tbssql0ndvkpf4@google.com
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


class PersonBase:

    def __init__(self, user, mdl_user):
        self.user = user
        self.mdl_user = mdl_user

    def update_calendar(self):
        if self.user:
            try:
                social_token = SocialToken.objects.get(account__user=self.user)
            except SocialToken.DoesNotExist:
                return f'Token was not found for Email {self.user.email}'

            creds = Credentials(token=social_token.token,
                                refresh_token=social_token.token_secret,
                                client_id=social_token.app.client_id,
                                client_secret=social_token.app.secret)
        else:
            return 'User not authorisized'

        self.service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z'
        two_weeks_after = (datetime.utcnow() + timedelta(days=14)).isoformat() + 'Z'

        try:
            events_result = self.service.events().list(calendarId='primary', timeMin=now,
                                                    timeMax=two_weeks_after,
                                                    singleEvents=False).execute()
        except RefreshError:
            return 'Refresh Error try to login again'

        api_events = events_result.get('items', [])

        events: Dict[int, Event] = dict()
        for api_event in api_events:
            source = api_event.get('source')
            if not source or source.get('title') != SOURCE_NAME:
                continue
            event_obj = Event(api_event)
            events[event_obj.uuid] = event_obj

        checked, updated, created, deleted = list(), list(), list(), list()

        lessons = self.search_lessons()
        for lesson in lessons:
            lesson_event = Event(None, lesson)
            lesson_event.description = self.build_description(lesson)
            if lesson.id in events:
                if events[lesson.id] != lesson_event: # lesson info changed
                    lesson_event.id = events[lesson.id].id # events created from model doesn't have id
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

        result = f'checked: {len(checked)}, updated: {len(updated)}, created: {len(created)}, deleted: {len(deleted)}'
        return result

    def build_description(self, lesson: models.Lesson):
        return f'<a href="{lesson.meetingurl}">Meeting Url</a>\n'\
               f'type: {lesson.get_type_display()}'


class Teacher(PersonBase):

    def search_lessons(self):
        courses_names = list()
        self.courses_ids = list()

        for course_id, course_name in (MdlUserEnrolments.objects
                                       .filter(userid=self.mdl_user, status=0)
                                       .values_list('enrolid__courseid_id',
                                                    'enrolid__courseid__shortname')):
            courses_names.append(course_name)
            self.courses_ids.append(course_id)

        if not course_name:
            print(f"No Enrols found for user {self.mdl_user.id}")
            return None

        return (models.Lesson.objects.prefetch_related('groups')
                .select_related('subject', 'lesson_number', 'semester')
                .filter(title__in=courses_names))

    # need to be called after search_lessons
    def build_description(self, lesson: models.Lesson) -> str:
        # if not hasattr(self, 'course_cohorts'):
        #     course_users = {
        #         name: userid for name, userid in (
        #             MdlUserEnrolments.objects.filter(enrolid__courseid__in=self.courses_ids)
        #             .values_list('enrolid__courseid__shortname', 'userid_id')
        #         )
        #     }

        #     user_cohorts = {
        #         user: cohort for user, cohort in (
        #             MdlCohortMembers.objects.filter(userid__in=course_users.values())
        #             .values_list('userid_id', 'cohortid__name')
        #         )
        #     }

        #     self.course_cohorts = defaultdict(list)
        #     for course, userid in course_users.items():
        #         self.course_cohorts[course].append(user_cohorts.get(userid))

        # return f'groups: {self.course_cohorts.get(title)}'
        description = super().build_description(lesson)
        return f'{description}\ngroups: {[group.name for group in lesson.groups.all()]}'

class Student(PersonBase):

    def search_lessons(self):
        cohorts_names = list(MdlCohortMembers.objects.filter(userid=self.mdl_user)
                             .values_list('cohortid__name', flat=True))

        return (models.Lesson.objects
                .select_related('subject', 'lesson_number', 'semester')
                .filter(groups__name__in=cohorts_names))

    def build_description(self, lesson: models.Lesson) -> str:
        if not hasattr(self, 'course_teachers') or not hasattr(self, 'user_names'):
            course_ids = list(MdlUserEnrolments.objects.filter(userid=self.mdl_user, status=0)
                          .values_list('enrolid__courseid_id', flat=True))

            course_users = defaultdict(set)
            self.user_names = dict()
            for course_name, user_id, firstname, lastname in (
                MdlUserEnrolments.objects.filter(enrolid__courseid__in=course_ids)
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

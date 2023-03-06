from __future__ import print_function
from datetime import datetime, timedelta
from typing import Dict
from pprint import pprint
import uuid

from googleapiclient.errors import HttpError

from main import models

SOURCE_NAME = 'scheduleNUBIP'


class Event:

    # must be passed one of sources
    def __init__(self, init_dict, lesson: models.Lesson = None):
        if init_dict:
            self.id = init_dict.get('id')
            self.uuid = self.parseUUID(init_dict.get('iCalUID'))
            self.summary = init_dict.get('summary', '')
            self.location = init_dict.get('location', '')
            self.start_date_time, self.end_date_time = (
                self.parse_dates(init_dict['start'].get('dateTime'),
                                 init_dict['end'].get('dateTime'))
            )
            self.interval, self.until = self.parse_recurrence(init_dict['recurrence'])
        else:
            self.uuid = lesson.id
            self.summary = lesson.title
            self.location = lesson.location
            self.start_date_time = lesson.start_date_time
            self.end_date_time = lesson.end_date_time
            self.interval = 1 if lesson.weekfrequency == models.WeekFrequency.EACH_WEEK else 2
            self.until = lesson.enddate

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
                until = datetime.strptime(until, '%Y%m%d').date()

        return interval, until

    def api_create(self, service):
        print(f'Creating event {self.uuid}')
        # pprint(self._event_dict)
        try:
            service.events().import_(calendarId='primary',
                                    body=self._event_dict).execute()
        except HttpError as error:
            if error.reason == 'The requested identifier already exists.':
                self.api_update(service)

    def api_update(self, service):
        print(f'Updating event {self.id}')
        service.events().update(calendarId='primary', eventId=self.id,
                                body=self._event_dict).execute()
    def api_delete(self, service):
        print(f'deleting event {self.id}')
        service.events().delete(calendarId='primary', eventId=self.id,
                                sendNotifications=False).execute()

    @property
    def _event_dict(self):
        return {
            'iCalUID': str(self.uuid),
            'summary': self.summary,
            'location': self.location,
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
                     self.end_date_time, self.interval, self.until))

    def __eq__(self, other: 'Event') -> bool:
        if not isinstance(other, Event):
            return NotImplemented

        # print(f'comparing {(self.uuid, self.summary, self.location, self.start_date_time,self.end_date_time, self.interval, self.until)} '
        #       f' vs {(other.uuid, other.summary, other.location, other.start_date_time, other.end_date_time, other.interval, other.until)}')
        return (self.uuid == other.uuid and
                self.summary == other.summary and
                self.location == other.location and
                self.start_date_time == other.start_date_time and
                self.end_date_time == other.end_date_time and
                self.interval == other.interval and
                self.until == other.until)

    def __ne__(self, other: 'Event'):
        return not self == other


def update(service, group: str):
    now = datetime.utcnow().isoformat() + 'Z'
    two_weeks_after = (datetime.utcnow() + timedelta(days=14)).isoformat() + 'Z'

    events_result = service.events().list(calendarId='primary', timeMin=now,
                                            timeMax=two_weeks_after,
                                            singleEvents=False).execute()
    api_events = events_result.get('items', [])

    if not api_events:
        print('No upcoming events found.')
        return

    events: Dict[int, Event] = dict()
    for api_event in api_events:
        source = api_event.get('source')
        if not source or source.get('title') != SOURCE_NAME:
            continue
        event_obj = Event(api_event)
        events[event_obj.uuid] = event_obj

    # print(api_event)
    checked, updated, created, deleted = list(), list(), list(), list()

    lessons = models.Lesson.objects.filter(groups__name=group)
    for lesson in lessons:
        lesson_event = Event(None, lesson)
        if lesson.id in events:
            if events[lesson.id] != lesson_event: # lesson info changed
                lesson_event.id = events[lesson.id].id # events created from model doesn't have id
                lesson_event.api_update(service)
                updated.append(lesson.id)
            else:
                checked.append(lesson.id)
        else:
            events[lesson.id] = lesson_event
            lesson_event.api_create(service)
            created.append(lesson.id)
        # return

    for id, event in events.items():
        if id in checked or id in updated or id in created:
            continue

        event.api_delete(service)
        deleted.append(id)

    print(f'checked: {len(checked)}, updated: {len(updated)}, created: {len(created)}, deleted: {len(deleted)}')
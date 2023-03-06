import os.path
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from main.g_calendar import Event

SCOPES = ['https://www.googleapis.com/auth/calendar.events.owned']

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('secret/token.json'):
            creds = Credentials.from_authorized_user_file('secret/token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'secret/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('secret/token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('calendar', 'v3', credentials=creds)

            self.update(service, 'ІПЗ-19-2')
            # self.list(service)

        except HttpError as error:
            print('An error occurred: %s' % error)


    def list(self, service):

        now = (datetime.utcnow()).isoformat() + 'Z'  # 'Z' indicates UTC time

        events_result = service.events().list(calendarId='primary', #iCalUID='825e1cfd-42d7-4f8e-8439-390699715e7a',
                                                singleEvents=False,
                                                showDeleted=True).execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        print(len(events))
        for event in events:
            # print(event)
            status = event.get('status')
            if status and status == 'cancelled':
                event_obj = Event(event)
                event_obj.api_delete(service)
            # source = event.get('source')
            # if not source or source.get('title') != SOURCE_NAME:
            #     continue
            # start = event['start'].get('dateTime', event['start'].get('date'))
            # print(start, event['title'])

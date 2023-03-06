from typing import Any, Dict
from django.shortcuts import render
from django.views.generic import TemplateView
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from allauth.socialaccount.models import SocialToken
from main.models import Person

from main import g_calendar
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events.owned']

class FillCalendarView(TemplateView):

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            return context

        # search user email in db
        try:
            person = Person.objects.get(email=self.request.user.email)
        except Person.DoesNotExist:
            context['message'] = f'Email {self.request.user.email} was not found in database, please use another email or contact administrator'
            return context

        if person.role == Person.Role.STUDENT:
            creds = Credentials.from_authorized_user_file('secret/token.json', SCOPES)

            try:
                social_token = SocialToken.objects.get(account__user=self.request.user)
            except SocialToken.DoesNotExist:
                context['message'] = f'Token was not found for Email {self.request.user.email}'
                return context

            creds = Credentials(token=social_token.token,
                                refresh_token=social_token.token_secret,
                                client_id=social_token.app.client_id,
                                client_secret=social_token.app.secret)
            service = build('calendar', 'v3', credentials=creds)

            g_calendar.update(service, person.group.name)
        # create google calendar events for user
        return context


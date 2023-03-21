from typing import Any, Dict
from django.shortcuts import render
from django.views.generic import TemplateView

from main.models import Person

from main.g_calendar import Student, Teacher
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
            person_obj = Student(self.request.user)
        else:
            person_obj = Teacher(self.request.user)

        context['message'] = person_obj.update_calendar(person)

        # create google calendar events for user
        return context


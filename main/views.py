from typing import Any, Dict
from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Q, Count
from schedule_nubip.settings import DEBUG

from main.models import Person
from moodle.models import MdlUser, MdlRoleAssignments

from main.g_calendar import Student, Teacher
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events.owned']


class FillCalendarView(TemplateView):

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            if DEBUG:
                email = self.request.GET.get('email')
                if not email:
                    return context
            else:
                return context
        else:
            email = self.request.GET.get('email', self.request.user.email)

        # search user email in db
        try:
            user = MdlUser.objects.get(email=email)
        except MdlUser.DoesNotExist:
            context['message'] = f'Email {self.request.user.email} was not found in database, please use another email or contact administrator'
            return context

        role_assignments = (
            MdlRoleAssignments.objects.filter(userid=user)
            .annotate(teaches=Count(1, filter=Q(roleid__shortname='editingteacher')),
                      studying=Count(1, filter=Q(roleid__shortname='student')))
            .first()
        )

        if role_assignments.teaches > role_assignments.studying:
            person_obj = Teacher(self.request.user, user)
        else:
            person_obj = Student(self.request.user, user)

        # create google calendar events for user
        context['message'] = person_obj.update_calendar()

        return context


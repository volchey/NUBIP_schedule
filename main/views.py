from typing import Any, Dict

from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Q, Count
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from schedule_nubip.settings import DEBUG

from main.models import Lesson
from moodle.models import MdlUser, MdlRoleAssignments

from main.g_calendar import Student, Teacher

SCOPES = ['https://www.googleapis.com/auth/calendar.events.owned']

class MeetUrlForm(forms.Form):
    meeting_url = forms.CharField(max_length=256)

class ButchMeetUrlSetView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name='admin/meet_url_form.html'

    def test_func(self):
        user = self.request.user
        return user.has_perm('main.can_view_Lesson')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = MeetUrlForm()
        return context

    def post(self, request, *args, **kwargs):
        lesson_ids = request.GET.get('ids')
        if lesson_ids:
            lesson_ids = lesson_ids.split(',')
            form = MeetUrlForm(request.POST)
            if form.is_valid():
                custom_data = form.cleaned_data['meeting_url']
                Lesson.objects.filter(id__in=lesson_ids).update(meetingurl=custom_data)
                return HttpResponseRedirect('/admin/main/lesson/')

        return HttpResponse(status=406)

class FillCalendarView(TemplateView):

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if not self.request.GET.get('update'):
            return context

        email = self.request.GET.get('test_email') or self.request.user.email

        # search user email in db
        try:
            user = MdlUser.objects.get(email=email)
        except MdlUser.DoesNotExist:
            context['message'] = f'Email {email} was not found in database, please use another email or contact administrator'
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


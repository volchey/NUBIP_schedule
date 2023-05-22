from typing import Any, Dict

from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.db.models import Q, Count
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from allauth.socialaccount.models import SocialAccount

from schedule_nubip.settings import DEBUG

from main.models import Lesson
from moodle.models import MdlUser, MdlRoleAssignments

from main.g_calendar import Student, Teacher

SCOPES = ['https://www.googleapis.com/auth/calendar.events.owned']

class MeetUrlForm(forms.Form):
    meeting_url = forms.CharField(max_length=256)

class BatchMeetUrlSetView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
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

class FillCalendarView(LoginRequiredMixin, TemplateView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and \
            not SocialAccount.objects.filter(user=self.request.user).exists():
            return redirect('/admin')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['debug'] = DEBUG
        update = self.request.GET.get('update')
        delete = self.request.GET.get('delete')
        if not update and not delete:
            return context

        email = self.request.user.email
        if DEBUG:
            email = self.request.GET.get('test_email')
            if not email:
                email = self.request.user.email

        # search user email in db
        try:
            user = MdlUser.objects.get(email=email)
        except MdlUser.DoesNotExist:
            context['message'] = f'Email {email} was not found in database, please use another email or contact administrator'
            return context

        person_obj = self.create_person(user)
        # create google calendar events for user
        if update:
            context['message'] = person_obj.update_calendar()
        elif delete:
            print('deleting calendar')
            context['message'] = person_obj.delete_calendar()

        return context

    def create_person(self, user):
        role_assignments = (
            MdlRoleAssignments.objects.filter(userid=user)
            .annotate(teaches=Count(1, filter=Q(roleid__shortname='editingteacher')),
                      studying=Count(1, filter=Q(roleid__shortname='student')))
            .first()
        )

        if role_assignments.teaches > role_assignments.studying:
            return Teacher(self.request.user, user)
        else:
            return Student(self.request.user, user)


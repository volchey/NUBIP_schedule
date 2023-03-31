from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django import forms

from main.models import Faculty, Group, Person, Lesson, Semester, ScheduleFile

@admin.action(description='Set Meeting Url', permissions=['change'])
def set_meeting_url(modeladmin, request, queryset):
    ids = queryset.values_list('id', flat=True)
    return redirect('/butch_meet_url_set/?ids=' + ','.join(str(id) for id in ids))


@admin.action(description='Mark as Practice', permissions=['change'])
def make_practice(modeladmin, request, queryset):
    queryset.update(type=Lesson.Type.PRACTICE)

@admin.action(description='Mark as Lecture', permissions=['change'])
def make_lecture(modeladmin, request, queryset):
    queryset.update(type=Lesson.Type.LECTURE)

class LessonAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    filter_horizontal = ('groups',)
    actions = [make_lecture, make_practice, set_meeting_url]

admin.site.register(Faculty)
admin.site.register(Group)
admin.site.register(Person)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Semester)
admin.site.register(ScheduleFile)

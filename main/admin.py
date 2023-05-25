from django.contrib import admin
from django.shortcuts import redirect

from main.models import (Faculty, Group, Lesson, Semester, ScheduleFile,
                         LessonNumber, Subject, Specialty, Type)


@admin.action(description='Set Meeting Url', permissions=['change'])
def set_meeting_url(modeladmin, request, queryset):
    ids = queryset.values_list('id', flat=True)
    return redirect('/batch_meet_url_set/?ids=' + ','.join(str(id) for id in ids))


@admin.action(description='Mark as Practice', permissions=['change'])
def make_practice(modeladmin, request, queryset):
    ids = list(queryset.values_list('id', flat=True))
    Lesson.objects.filter(id__in=ids).update(type=Type.PRACTICE)


@admin.action(description='Mark as Lecture', permissions=['change'])
def make_lecture(modeladmin, request, queryset):
    ids = list(queryset.values_list('id', flat=True))
    Lesson.objects.filter(id__in=ids).update(type=Type.LECTURE)


class LessonAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_filter = ('type', 'dayofweek', 'lesson_number', 'groups',)
    actions = [make_lecture, make_practice, set_meeting_url]


admin.site.register(Faculty)
admin.site.register(Group)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(LessonNumber)
admin.site.register(Semester)
admin.site.register(ScheduleFile)
admin.site.register(Subject)
admin.site.register(Specialty)

from django.contrib import admin
from main.models import Faculty, Group, Person, Lesson, Semester, ScheduleFile

class LessonAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    filter_horizontal = ('groups',)

admin.site.register(Faculty)
admin.site.register(Group)
admin.site.register(Person)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Semester)
admin.site.register(ScheduleFile)

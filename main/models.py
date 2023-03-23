import uuid
from django.db import models

from datetime import datetime, date, timezone, timedelta

from main.schedule_file_parser import ScheduleFileParser

YEAR_CHOICES = [(r,r) for r in range(2015, date.today().year+1)]
COURSES = [(r,r) for r in range(1, 5)]

class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, 'Понеділок'
    TUESDAY = 1, 'Вівторок'
    WEDNESDAY = 2, 'Середа'
    THURSDAY = 3, 'Четвер'
    FRIDAY = 4, 'Пʼятниця'
    SATURDAY = 5, 'Субота'
    SUNDAY = 6, 'Неділя'

class WeekFrequency(models.IntegerChoices):
    EACH_WEEK = 1
    NUMERATOR = 2
    DENOMINATOR = 3

class Semester(models.Model):
    startdate = models.DateField()
    enddate = models.DateField()

    class WeekType(models.IntegerChoices):
        NUMERATOR = 2
        DENOMINATOR = 3

    weektype = models.IntegerField(choices=WeekType.choices)

    class Meta:
        db_table = 'Semesters'

    def __str__(self) -> str:
        return f'{self.startdate} - {self.enddate}'

class Faculty(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    class Meta:
        db_table = 'Faculties'

    def __str__(self) -> str:
        return self.name

class ScheduleFile(models.Model):
    id = models.AutoField(primary_key=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')

    def save(self, *args, **kwargs) -> None:
        result = super().save(*args, **kwargs)
        parser = ScheduleFileParser(self.file.path, self.faculty, self.semester)
        parser.serialize_to_db()
        return result

    class Meta:
        db_table = 'ScheduleFiles'
        unique_together = (("semester", "faculty"),)

    def __str__(self) -> str:
        return self.file.name

class Group(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=datetime.now().year)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=False)

    class Type(models.IntegerChoices):
        BACHELOR = 1
        MASTER = 2
        REDUCED = 3

    type = models.IntegerField(choices=Type.choices)

    class Meta:
        db_table = 'Groups'

    def __str__(self):
        return self.name

class Person(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    patronymic = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, primary_key=True)

    class Role(models.IntegerChoices):
        TEACHER = 1
        STUDENT = 2

    role = models.IntegerField(choices=Role.choices)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'Persons'

    def __str__(self) -> str:
        return f'{self.lastname} {self.firstname} ({self.email})'

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    starttime = models.TimeField()
    endtime = models.TimeField()
    dayofweek = models.IntegerField(choices=DayOfWeek.choices)

    weekfrequency = models.IntegerField(choices=WeekFrequency.choices,
                                        default=WeekFrequency.EACH_WEEK)
    lesson_number = models.IntegerField()
    startdate = models.DateField()
    enddate = models.DateField()
    groups = models.ManyToManyField(Group)
    teacher = models.ForeignKey(Person, on_delete=models.CASCADE, db_column="teacher_email",
                                null=True, blank=True, default=None)
    meetingurl = models.URLField(blank=True)
    location = models.CharField(max_length=255)

    class Type(models.IntegerChoices):
        UNKNOWN = 0
        LECTURE = 1
        PRACTICE = 2

    type = models.IntegerField(choices=Type.choices, default=Type.UNKNOWN)
    courseurl = models.URLField(blank=True)

    @property
    def start_date_time(self):
        return datetime.combine(self.startdate, self.starttime).replace(
            tzinfo=timezone(timedelta(hours=2))
        )

    @property
    def end_date_time(self):
        return datetime.combine(self.startdate, self.endtime).replace(
            tzinfo=timezone(timedelta(hours=2))
        )

    class Meta:
        db_table = 'Lessons'

    def __str__(self):
        name = self.title
        if self.weekfrequency == WeekFrequency.NUMERATOR:
            name = f'{self.title} (чисельник)'
        if self.weekfrequency == WeekFrequency.DENOMINATOR:
            name = f'{self.title} (знаменник)'
        return f'{self.get_dayofweek_display()} {self.starttime}: {name}'

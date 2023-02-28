from django.db import models

import datetime
YEAR_CHOICES = [(r,r) for r in range(2015, datetime.date.today().year+1)]
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

class Faculty(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    class Meta:
        db_table = 'Faculties'

class Group(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=datetime.datetime.now().year)
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
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=False)

    class Meta:
        db_table = 'Persons'

class Lesson(models.Model):
    id = models.AutoField(primary_key=True)
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
                                null=True, blank=False, default=None)
    meetingurl = models.URLField()
    location = models.CharField(max_length=255)

    class Type(models.IntegerChoices):
        UNKNOWN = 0
        LECTURE = 1
        PRACTICE = 2

    type = models.IntegerField(choices=Type.choices, default=Type.UNKNOWN)
    courseurl = models.URLField()

    class Meta:
        db_table = 'Lessons'

    def __str__(self):
        name = self.title
        if self.weekfrequency == WeekFrequency.NUMERATOR:
            name = f'{self.title} (чисельник)'
        if self.weekfrequency == WeekFrequency.DENOMINATOR:
            name = f'{self.title} (знаменник)'
        # return f'{DayOfWeek[self.dayofweek]} {name}'
        return f'{self.get_dayofweek_display()} {self.starttime}: {name}'

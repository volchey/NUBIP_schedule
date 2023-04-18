import uuid
from django.db import models

from datetime import datetime, date, timezone, timedelta

from main.schedule_file_parser import ScheduleFileParser

YEAR_CHOICES = [(r,r) for r in range(2015, date.today().year+1)]

class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, 'Понеділок'
    TUESDAY = 1, 'Вівторок'
    WEDNESDAY = 2, 'Середа'
    THURSDAY = 3, 'Четвер'
    FRIDAY = 4, 'Пʼятниця'
    SATURDAY = 5, 'Субота'
    SUNDAY = 6, 'Неділя'

class Type(models.IntegerChoices):
    UNKNOWN = 0, 'Невідомо'
    LECTURE = 1, 'Лекція'
    PRACTICE = 2, 'Практика'

class WeekFrequency(models.IntegerChoices):
    EACH_WEEK = 1
    NUMERATOR = 2
    DENOMINATOR = 3

class Semester(models.Model):
    id = models.AutoField(primary_key=True)
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
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, blank=False)
    code = models.CharField(max_length=128, blank=True, default='')

    class Meta:
        db_table = 'Faculties'

    def __str__(self) -> str:
        return self.name

class ScheduleFile(models.Model):
    id = models.AutoField(primary_key=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')

    class Status(models.IntegerChoices):
        NEW = 1
        PROCESSED = 2

    status = models.IntegerField(choices=Status.choices, default=Status.NEW)


    def save(self, *args, **kwargs) -> None:
        result = super().save(*args, **kwargs)
        # parser = ScheduleFileParser(self.file.path, self.faculty, self.semester)
        # parser.serialize_to_db()
        return result

    class Meta:
        db_table = 'ScheduleFiles'
        unique_together = (("semester", "faculty"),)

    def __str__(self) -> str:
        return self.file.name

class Specialty(models.Model):
    code = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=False)

    class Meta:
        db_table = 'Specialties'

class Group(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=datetime.now().year)
    number = models.PositiveSmallIntegerField()
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)

    class Type(models.IntegerChoices):
        BACHELOR = 1
        MASTER = 2
        REDUCED = 3

    type = models.IntegerField(choices=Type.choices)

    class Meta:
        db_table = 'Groups'

    def __str__(self):
        return self.name

class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=128)
    courseurl = models.URLField(blank=True)

    class Meta:
        db_table = 'Subjects'

    def __str__(self):
        return self.title

class SubjectTeachers(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher_id = models.IntegerField()

    class Meta:
        db_table = 'SubjectTeachers'

class LessonNumber(models.Model):
    lesson_number = models.IntegerField(primary_key=True)
    starttime = models.TimeField()
    endtime = models.TimeField()

    class Meta:
        db_table = 'LessonNumbers'

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dayofweek = models.IntegerField(choices=DayOfWeek.choices)
    weekfrequency = models.IntegerField(choices=WeekFrequency.choices,
                                        default=WeekFrequency.EACH_WEEK)
    lesson_number = models.ForeignKey(LessonNumber, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group)
    meetingurl = models.URLField(blank=True)
    location = models.CharField(max_length=255)

    type = models.IntegerField(choices=Type.choices, default=Type.UNKNOWN)

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
        name = self.subject.title
        if self.weekfrequency == WeekFrequency.NUMERATOR:
            name += ' (чисельник)'
        if self.weekfrequency == WeekFrequency.DENOMINATOR:
            name += ' (знаменник)'
        return f'{self.get_dayofweek_display()} {self.starttime}: {name}'

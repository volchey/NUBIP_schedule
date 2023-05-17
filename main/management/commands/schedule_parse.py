from django.core.management.base import BaseCommand
from main.schedule_file_parser import ScheduleFileParser
from main.models import ScheduleFile, Lesson
import time

SLEEP_SECONDS = 30

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        # process new files in infinite loop
        while True:
            new_files = ScheduleFile.objects.filter(status=ScheduleFile.Status.NEW)
            for new_file in new_files:
                lessons = Lesson.objects.filter(groups__specialty__faculty=new_file.faculty,
                                semester=new_file.semester)
                lessons.delete()
                parser = ScheduleFileParser(new_file.file, new_file.faculty, new_file.semester)
                parser.serialize_to_db()
                new_file.status = ScheduleFile.Status.PROCESSED
                new_file.save()

            time.sleep(SLEEP_SECONDS)

from django.core.management.base import BaseCommand
from main.schedule_file_parser import ScheduleFileParser
from main.models import ScheduleFile
import time

SLEEP_SECONDS = 30

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        # process new files in infinite loop
        while True:
            new_files = ScheduleFile.objects.filter(status=ScheduleFile.Status.NEW)
            for new_file in new_files:
                parser = ScheduleFileParser(new_file.file, new_file.faculty, new_file.semester)
                parser.serialize_to_db()
                new_file.status = ScheduleFile.Status.PROCESSED

            time.sleep(SLEEP_SECONDS)

from django.core.management.base import BaseCommand
from main.schedule_file_parser import ScheduleFileParser

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        parser = ScheduleFileParser('fakultet_informaciynih_tehnologiy_10.02.23.xlsx')
        parser.serialize_to_db()

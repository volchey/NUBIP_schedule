from collections import defaultdict
from datetime import datetime, time, timedelta
import re
import string
import os
from typing import List

from openpyxl import load_workbook

from main import models

ALPHABET_LIST = list(string.ascii_uppercase)

FACULTY_NAME_CELL = 'Q1'

TITLE_COLUMNS = 2 # titles, weekday names, lessons number fit here
TITLE_ROWS = 6 # faculty, course, group

COURSES_ROW = 3

SPECIALTY_ROW = 4

GROUP_ROW = 5

DAYS_START_ROW = 7

LESSON_NUMBER_COLUMN = 2

MAX_COL = None # horisontal limit
MAX_ROW = None # vertical limit

LESSON_TIME = {1: (time(hour=8, minute=30), time(hour=9, minute=50)),
               2: (time(hour=10, minute=10), time(hour=11, minute=30)),
               3: (time(hour=11, minute=50), time(hour=13, minute=10)),
               4: (time(hour=14, minute=0), time(hour=15, minute=20)),
               5: (time(hour=15, minute=40), time(hour=17, minute=0)),
               6: (time(hour=17, minute=20), time(hour=18, minute=40)),
               7: (time(hour=19, minute=0), time(hour=20, minute=20)),}

days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

class Group:

    def __init__(self, course_name, spec_name, name, faculty=None):
        self.course_name = course_name
        self.spec_name = spec_name
        self.name = name.replace('\n', '')
        self.year = self.get_course_year(course_name)
        self.faculty = faculty or models.Faculty.objects.all().first() # TODO: parse from file
        self.db_object = models.Group.objects.filter(name=self.__str__()).first()
        if not self.db_object:
            self.db_object = models.Group(name=self.__str__(), year=self.year,
                                          faculty=self.faculty,
                                          type=models.Group.Type.BACHELOR) # TODO: parse from file
            self.db_object.save()

    def __hash__(self) -> int:
        return hash(self.__str__())

    @staticmethod
    def get_course_year(course_name):
        m = re.search(r"\d", course_name)
        if m:
            year = datetime.now().year - int(m.group(0))
            if datetime.now().month > 10: # second semester
                year += 1
            return year

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.spec_name}-{self.year - 2000}-{self.name}'

class Lesson:

    def __init__(self, week_day: str, number: str, info: str, freq, semester=None):
        self.week_day = week_day
        self.number = int(number)
        self.info = info
        self.name, self.location = self.parse_info(info)
        self.freq = freq
        self.semester = semester or models.Semester.objects.all().first()
        self.groups = []

    @staticmethod
    def parse_info(info):
        m = re.match(r'^((.|\n)+)\s+(\d+(\s+)?к\..+)$', info, re.M)

        if m:
            name, location = m.group(1), m.group(3)
            name = name.replace('\n', ' ')
            return name, location
        return info, ""

    def serialize_to_db(self):
        print(f'serializing lesson {self.__str__()}')
    #     return
        if not self.semester:
            print("Error!! semester not found")
            return
        if not self.groups:
            print("Error!! groups not found")
            return

        days_to_add = self.week_day
        if (self.freq != models.WeekFrequency.EACH_WEEK and
            self.semester.weektype != self.freq):
            days_to_add += 7

        startdate = self.semester.startdate + timedelta(days=days_to_add)

        db_lesson = (models.Lesson.objects.
                     filter(title=self.name, dayofweek=self.week_day,
                            lesson_number=self.number, startdate=startdate)
                     .first())
        if not db_lesson:
            db_lesson = models.Lesson() # create new
        db_lesson.title = self.name
        db_lesson.starttime, db_lesson.endtime = LESSON_TIME[self.number]
        db_lesson.dayofweek = self.week_day
        db_lesson.weekfrequency = self.freq
        db_lesson.lesson_number = self.number
        db_lesson.startdate = startdate
        db_lesson.enddate = self.semester.enddate
        db_lesson.location = self.location
        db_lesson.save()

        for group in self.groups:
            db_lesson.groups.add(group.db_object)

    def __eq__(self, __o: object) -> bool:
        return (self.info == __o.info and self.week_day == __o.week_day and
                self.number == __o.number)

    def __hash__(self) -> int:
        return hash(self.__str__())

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        name = self.name
        if self.freq == models.WeekFrequency.NUMERATOR:
            name = f'{self.name} (чисельник)'
        if self.freq == models.WeekFrequency.DENOMINATOR:
            name = f'{self.name} (знаменник)'
        return f'{days[self.week_day]} {self.number} lesson - {name} for groups {self.groups}'

class ScheduleFileParser:

    def __init__(self, path, faculty=None, semester=None) -> None:
        wb = load_workbook(path)
        self.ws = wb.active
        self.faculty = faculty
        self.semester = semester

        self.define_week_days_ranges()
        self.lessons = self.parse_lessons()

    def define_week_days_ranges(self):
        self.week_day_ranges = dict()
        week_day = 0
        for cols in self.ws.iter_cols(min_row=DAYS_START_ROW, min_col=1,
                                      max_row=None, max_col=1):
            for cell in cols:
                if not cell.value:
                    continue
                merged_range = self.get_merged_range(cell.coordinate)
                for row in range(merged_range.min_row, merged_range.max_row + 1):
                    self.week_day_ranges[row] = week_day
                week_day += 1

    def parse_group(self, column: int) -> Group | None:
        # print(column)
        course_cell = self.ws.cell(COURSES_ROW, column)
        course_name = self.get_cell_value(course_cell)
        if not course_name:
            return None

        speciality_cell = self.ws.cell(SPECIALTY_ROW, column)
        speciality_name = self.get_cell_value(speciality_cell)
        if not speciality_name:
            return None

        group_cell = self.ws.cell(GROUP_ROW, column)
        group_name = self.get_cell_value(group_cell)
        if not group_name:
            return None

        return Group(course_name, speciality_name, group_name, self.faculty)


    def parse_lessons(self) -> List[Lesson]:
        lessons = list()
        for column_cells in self.ws.iter_cols(min_row=TITLE_ROWS + 1, min_col=TITLE_COLUMNS + 1,
                                      max_row=MAX_ROW, max_col=MAX_COL):
            if not column_cells:
                continue

            group = self.parse_group(column_cells[0].column)
            if not group:
                print(f'Error!! group not found for column {column_cells[0].column}')
                continue

            for cell in column_cells:
                lesson_info = self.get_cell_value(cell)
                if not lesson_info:
                    continue

                cell_merged_range = self.get_merged_range(cell.coordinate)
                if (not cell.value and cell_merged_range and
                    cell_merged_range.min_row != cell.row):
                    continue # avoid lesson duplicates (vertical merged cells)

                week_day = self.week_day_ranges[cell.row]
                if week_day is None:
                    print(f'Error!! week day not found for lesson in cell {cell.row}')
                    continue

                lesson_number_cell = self.ws.cell(cell.row, LESSON_NUMBER_COLUMN)
                if not lesson_number_cell:
                    print(f'Error!! lesson number cell not found for lesson in cell {cell.coordinate}')
                    continue

                # check NUMERATOR or DENOMINATOR
                freq = models.WeekFrequency.EACH_WEEK # from frequency
                if (not cell_merged_range or
                    cell_merged_range.min_row == cell_merged_range.max_row):
                    # if cell occupies only one row it meens lesson is not in each week
                    freq = models.WeekFrequency.DENOMINATOR if lesson_number_cell.value is None \
                        else models.WeekFrequency.NUMERATOR

                lesson_number = self.get_cell_value(lesson_number_cell)
                if lesson_number is None:
                    print(f'Error!! lesson number not found for lesson in cell {cell.coordinate}')
                    continue

                lesson = Lesson(week_day, lesson_number, lesson_info, freq, self.semester)
                try:
                    existed_lesson = next(x for x in lessons if x == lesson)
                    existed_lesson.groups.append(group)
                except StopIteration:
                    lesson.groups.append(group)
                    lessons.append(lesson)

        return lessons

    def serialize_to_db(self):
        for lesson in self.lessons:
            lesson.serialize_to_db()

    def get_cell_value(self, cell):
        if not cell:
            return None
        value = cell.value
        if value:
            return value
        merged_range = self.get_merged_range(cell.coordinate)
        if merged_range:
            value = merged_range.title
            if value is None:
                title_cell = self.ws.cell(merged_range.min_row, merged_range.min_col)
                return title_cell.value
            return value
        return None

    def get_cell_column_range(self, cell):
        if not cell:
            return None
        merged_range = self.get_merged_range(cell.coordinate)
        if merged_range:
            return merged_range.min_col, merged_range.max_col
        else:
            return cell.column, cell.column

    def get_merged_range(self, cell_name):
        if not cell_name:
            return None
        # print(cell_name)
        for merged_range in self.ws.merged_cells.ranges:
            if cell_name in merged_range:
                return merged_range
        return None

    def is_cell_merged(self, cell_name):
        range = self.get_merged_range(cell_name)
        return range is not None

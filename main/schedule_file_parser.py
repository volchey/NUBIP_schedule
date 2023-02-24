from datetime import datetime
import re
import string
import os

from openpyxl import load_workbook

from main import models

ALPHABET_LIST = list(string.ascii_uppercase)

FACULTY_NAME_CELL = 'Q1'

TITLE_COLUMNS = 38 # titles, weekday names, lessons number fit here
TITLE_ROWS = 6 # faculty, course, group

COURSES_ROW = 3

SPECIALTY_ROW = 4

GROUP_ROW = 5

DAYS_START_ROW = 7

LESSON_NUMBER_COLUMN = 2

MAX_COL = 40
MAX_ROW = 20

EACHWEEK, NUMERATOR, DENOMINATOR = 1, 2, 3

LESSON_TIME = {1: (datetime.time(8, 30), datetime.time(9, 50)),
               2: (datetime.time(10, 10), datetime.time(11, 30)),
               3: (datetime.time(11, 50), datetime.time(13, 10)),
               4: (datetime.time(14, 0), datetime.time(15, 20)),
               5: (datetime.time(15, 40), datetime.time(17, 0)),
               6: (datetime.time(17, 20), datetime.time(18, 40)),
               7: (datetime.time(19, 0), datetime.time(20, 20)),}

days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

class Group:

    def __init__(self, column, course_name, spec_name, name):
        self.column = column
        self.course_name = course_name
        self.spec_name = spec_name
        self.name = name.replace('\n', '')
        self.year = self.get_course_year(course_name)
        self.faculty = models.Faculty.objects.all().first() # TODO: parse from file

    @staticmethod
    def get_course_year(course_name):
        m = re.search(r"\d", course_name)
        if m:
            year = datetime.now().year - int(m.match)
            if datetime.now().month < 10: # second semester
                year -= 1
            return year

    def __str__(self):
        return f'{self.spec_name}-{self.name}'

class Lesson:

    def __init__(self, group: Group, week_day: str, number: str, info: str,
                 freq: int = EACHWEEK):
        self.group = group
        self.week_day = week_day
        self.number = number
        self.info = info
        self.name, self.location = self.parse_info()
        self.freq = freq
        self.semester = models.Semester.objects.all().first() # TODO: parse from file

    @staticmethod
    def parse_info(info):
        m = re.match(r'^((.|\n)+)\s+(\d+(\s+)?к\..+)$', info, re.M)

        if m:
            name, location = m.group(1), m.group(2)
            name = name.replace('\n', ' ')
            return name, location
        # print(f'Error!! Cannot parse lesson info: "{self.info}"')
        return info, ""

    def serialize_to_db(self):
        if not self.semester:
            print("Error!! semester not found")
            return

        db_lesson = models.Lesson()
        db_lesson.title = self.name
        db_lesson.starttime, db_lesson.endtime = LESSON_TIME[self.number]
        db_lesson.dayofweek = self.week_day
        if self.freq == EACHWEEK:
            db_lesson.weekfrequency = models.Lesson.WeekFrequency.EACH_WEEK
        else:
            db_lesson.weekfrequency = models.Lesson.WeekFrequency.EACH_TWO_WEEKS

        days_to_add = self.week_day
        if self.semester.weektype != self.freq:
            days_to_add += 7

        db_lesson.startdate = self.semester.startdate + datetime.timedelta(days=days_to_add)
        db_lesson.enddate = self.semester.enddate


    def __str__(self):
        name = self.name
        if self.freq == NUMERATOR:
            name = f'{self.name} (чисельник)'
        if self.freq == DENOMINATOR:
            name = f'{self.name} (знаменник)'
        return f'{days[self.week_day]} {self.number} lesson - {name} for group {self.group}'

class ScheduleFileParser:

    def __init__(self, path) -> None:
        wb = load_workbook(path)
        self.ws = wb.active
        # cell = self.ws['B14']
        # print(self.get_cell_value(cell))
        # print(self.get_merged_range('B14'))

        self.define_week_days_ranges()
        # print(self.week_day_ranges)
        self.parse_courses()
        self.serialize_to_db()

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

    def parse_courses(self):
        # iterate through courses
        for cols in self.ws.iter_rows(min_row=COURSES_ROW, min_col=TITLE_COLUMNS,
                                      max_row=COURSES_ROW, max_col=MAX_COL):
            for cell in cols:
                if not cell.value:
                    continue
                min_col, max_col = self.get_cell_column_range(cell)
                self.parse_specialities(min_col, max_col, cell.value)


    def parse_specialities(self, min_col, max_col, course_name):
        # iterate through specialities of course
        for cols in self.ws.iter_rows(min_row=SPECIALTY_ROW, min_col=min_col,
                                      max_row=SPECIALTY_ROW, max_col=max_col):
            for cell in cols:
                if not cell.value:
                    continue
                min_col, max_col = self.get_cell_column_range(cell)
                self.parse_groups(min_col, max_col, course_name, cell.value)

    def parse_groups(self, min_col, max_col, course_name, speciality_name):
        # iterate through groups of speciality
        for cols in self.ws.iter_rows(min_row=GROUP_ROW, min_col=min_col,
                                      max_row=GROUP_ROW, max_col=max_col):
            for cell in cols:
                group_name = self.get_cell_value(cell)
                if not group_name:
                    continue

                group = Group(cell.column, course_name, speciality_name, group_name)
                self.parse_group(group)

    def parse_group(self, group: Group):
        # iterate through lessons
        for cols in self.ws.iter_rows(min_row=TITLE_ROWS, min_col=group.column,
                                      max_row=MAX_ROW, max_col=group.column):
            for cell in cols:
                lesson_info = self.get_cell_value(cell)
                if not lesson_info:
                    continue

                week_day = self.week_day_ranges[cell.row]
                if week_day is None:
                    print(f'Error!! week day not found for lesson in cell {cell.row}')
                    continue

                lesson_number_cell = self.ws.cell(cell.row, LESSON_NUMBER_COLUMN)
                if not lesson_number_cell:
                    print(f'Error!! lesson number cell not found for lesson in cell {cell.coordinate}')
                    continue

                # check NUMERATOR or DENOMINATOR
                freq = EACHWEEK # from frequency
                cell_merged_range = self.get_merged_range(cell.coordinate)
                if not cell_merged_range: # if cell not merged it meens lesson is not in each week
                    freq = DENOMINATOR if lesson_number_cell.value is None else NUMERATOR

                lesson_number = self.get_cell_value(lesson_number_cell)
                if lesson_number is None:
                    print(f'Error!! lesson number not found for lesson in cell {cell.coordinate}')
                    continue

                lesson = Lesson(group, week_day, lesson_number, lesson_info, freq)
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

parser = ScheduleFileParser('fakultet_informaciynih_tehnologiy_10.02.23.xlsx')
"""
A module for creating .pdf math worksheets
"""

__author__ = 'januschung'

import argparse
import random
import math
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from functools import reduce
from typing import List, Tuple

from pathlib import Path

QuestionInfo = Tuple[int, str, int, int]


class NumberGenerator:
    def __init__(self, main_type, min_decimals, max_decimals):
        self.main_type = main_type

        self.lower_bound = 10 ** (min_decimals - 1)
        self.upper_bound = 10 ** max_decimals - 1

        self.type_question_distribution = {'+': 0, '-': 0, 'x': 0, '/': 0}

        # From https://stackoverflow.com/questions/6800193/what-is-the-most-efficient-way-of-finding-all-the-factors-of-a
        # -number-in-python

    def factors(self, n: int):
        return set(reduce(list.__add__,
                          ([i, n // i] for i in range(1, int(n ** 0.5) + 1) if n % i == 0)))

    @staticmethod
    def digits(num: int):
        if num == 0:
            return 1
        else:
            return  math.floor(math.log10(abs(num))) + 1

    def division_helper(self, num) -> [int, int, int]:
        # prevent num = 0 or divisor = 1 or divisor = dividend
        factor = 1
        while not num or factor == 1 or factor == num:
            # num = random.randint(10 ** (1 - 1), min(10 ** 2 - 1, self.upper_bound))
            # pick a factor of num; answer will always be an integer
            if num:
                factor_list=[f for f in self.factors(num) if f!=1 and NumberGenerator.digits(f)<2]
                if len(factor_list) >0:
                    factor = random.sample(factor_list, 1)[0]
        answer = int(num / factor)
        return [num, factor, answer]

    def next_number(self, can_be_zero=True, can_be_one=True):

        while True:
            n = random.randint(self.lower_bound,  self.upper_bound)
            if (not can_be_zero and n == 0) or (not can_be_one and n == 1):
                continue
            return n

    def generate(self):

        if self.main_type == 'mix':
            options = [c[0] for c in self.type_question_distribution.items() if
                       c[1] == min(self.type_question_distribution.values())]
            current_type = random.choice(options)
            self.type_question_distribution[current_type] = self.type_question_distribution[current_type] + 1
        else:
            current_type = self.main_type
        num_1 = self.next_number()

        if current_type == '/':
            num_1, num_2, _ = self.division_helper(num_1)
        else:
            num_2 = self.next_number()

        return current_type, num_1, num_2


class MathWorksheetGenerator:
    """class for generating math worksheet of specified size and main_type"""

    def __init__(self, type_: str, question_count: int, gg: NumberGenerator):
        self.main_type = type_

        self.question_count = question_count
        self.pdf = FPDF()
        self.gg = gg

        self.small_font_size = 10
        self.middle_font_size = 15
        self.large_font_size = 30
        self.size = 21
        self.tiny_pad_size = 2
        self.pad_size = 10
        self.large_pad_size = 30
        self.num_x_cell = 4
        self.num_y_cell = 2
        self.font_1 = 'Times'
        self.font_2 = 'Helvetica'

    def generate_question(self) -> QuestionInfo:
        """Generates each question and calculate the answer depending on the type_ in a list
        To keep it simple, number is generated randomly within the range of 0 to 100
        :return:  list of value1, main_type, value2, and answer for the generated question
        """
        # num_1 = random.randint(0, self.max_number)
        # num_2 = random.randint(0, self.max_number)
        # if self.main_type == 'mix':
        #     current_type = random.choice(['+', '-', 'x', '/'])
        # else:
        #     current_type = self.main_type
        current_type, num_1, num_2 = self.gg.generate()

        if current_type == '+':
            answer = num_1 + num_2
        elif current_type == '-':
            #  avoid having a negative answer which is an advanced concept
            num_1, num_2 = sorted((num_1, num_2), reverse=True)
            answer = num_1 - num_2
        elif current_type == 'x':
            answer = num_1 * num_2
        elif current_type == '/':
            answer = int(num_1 / num_2)
            # num_1, num_2, answer = self.division_helper(num_2)

        else:
            raise RuntimeError(f'Question main_type {current_type} not supported')
        return num_1, current_type, num_2, answer

    def get_list_of_questions(self, question_count: int) -> List[QuestionInfo]:
        """Generate all the questions for the worksheet in a list. Initially trying for unique questions, but
        allowing duplicates if needed (e.g. asking for 80 addition problems with max size 3 requires duplication)
        :return: list of questions
        """
        questions = []
        duplicates = 0
        while len(questions) < question_count:
            new_question = self.generate_question()
            if new_question not in questions or duplicates >= 10:
                questions.append(new_question)
            else:
                duplicates += 1
        return questions

    def make_question_page(self, data: List[QuestionInfo]):
        """Prepare a single page of questions"""
        page_area = self.num_x_cell * self.num_y_cell
        problems_per_page = self.split_arr(self.question_count, page_area)
        total_pages = len(problems_per_page)
        for page in range(total_pages):
            self.pdf.add_page(orientation='L')
            if problems_per_page[page] < self.num_x_cell:
                self.print_question_row(data, page * page_area, problems_per_page[page])
            else:
                problems_per_row = self.split_arr(problems_per_page[page], self.num_x_cell)
                total_rows = len(problems_per_row)
                self.print_question_row(data, page * page_area, problems_per_row[0])
                for row in range(1, total_rows):
                    page_row = row * self.num_x_cell
                    self.print_horizontal_separator()
                    self.print_question_row(data, page * page_area + page_row, problems_per_row[row])

    def split_arr(self, x: int, y: int):
        """Split x into x = y + y + ... + (x % y)"""
        quotient, remainder = divmod(x, y)
        if remainder != 0:
            return [y] * quotient + [remainder]

        return [y] * quotient

    def print_top_row(self, question_num: str):
        """Helper function to print first character row of a question row"""
        self.pdf.set_font(self.font_1, size=self.middle_font_size)
        self.pdf.cell(self.pad_size, self.pad_size, txt=question_num, border='LT', align='C')
        self.pdf.cell(self.size, self.pad_size, border='T')
        self.pdf.cell(self.size, self.pad_size, border='T')
        self.pdf.cell(self.pad_size, self.pad_size, border='TR')

    def print_second_row(self, num: int):
        """Helper function to print second character row of a question row"""
        self.pdf.set_font(self.font_2, size=self.large_font_size)
        self.pdf.cell(self.pad_size, self.size, border='L')
        self.pdf.cell(self.size, self.size)
        self.pdf.cell(self.size, self.size, txt=str(num), align='R')
        self.pdf.cell(self.pad_size, self.size, border='R')

    def print_second_row_division(self, num_1: int, num_2: int):
        """Helper function to print second character row of a question row for division"""
        self.pdf.set_font(self.font_2, size=self.large_font_size)
        self.pdf.cell(self.pad_size, self.size, border='L')
        self.pdf.cell(self.size, self.size, txt=str(num_1), align='R')
        # self.pdf.cell(self.size, self.size, txt=':', align='C')
        x_cor = self.pdf.get_x()
        y_cor = self.pdf.get_y() + (self.large_font_size / 2)
        # self.pdf.text(x_cor, y_cor,':')
        #        self.pdf.image(name='division.png', x=x_cor, y=y_cor)
        self.pdf.cell(self.size, self.size, txt=': ' + str(num_2), align='R')
        self.pdf.cell(self.pad_size, self.size, border='R')

    def print_third_row(self, num: int, current_type: str):
        """Helper function to print third character row of a question row"""
        self.pdf.cell(self.pad_size, self.size, border='L')
        self.pdf.cell(self.size, self.size, txt=current_type, align='L')
        self.pdf.cell(self.size, self.size, txt=str(num), align='R')
        self.pdf.cell(self.pad_size, self.size, border='R')

    def print_third_row_division(self):
        """Helper function to print third character row of a question row for division"""
        self.pdf.cell(self.pad_size, self.size, border='L')
        self.pdf.cell(self.size, self.size, align='L')
        self.pdf.cell(self.size, self.size, align='R')
        self.pdf.cell(self.pad_size, self.size, border='R')

    def print_bottom_row(self):
        """Helper function to print bottom row of question"""
        self.pdf.cell(self.pad_size, self.size, border='LB')
        self.pdf.cell(self.size, self.size, border='TB')
        self.pdf.cell(self.size, self.size, border='TB')
        self.pdf.cell(self.pad_size, self.size, border='BR')

    def print_bottom_row_division(self):
        """Helper function to print bottom row of question"""
        self.pdf.cell(self.pad_size, self.size, border='LB')
        self.pdf.cell(self.size, self.size, border='B')
        self.pdf.cell(self.size, self.size, border='B')
        self.pdf.cell(self.pad_size, self.size, border='BR')

    def print_edge_vertical_separator(self):
        """Print space between question for the top or bottom row"""
        self.pdf.cell(self.pad_size, self.pad_size)

    def print_middle_vertical_separator(self):
        """Print space between question for the second or third row"""
        self.pdf.cell(self.pad_size, self.size)

    def print_horizontal_separator(self):
        """Print line breaker between two rows of questions"""
        self.pdf.cell(self.size, self.size)
        self.pdf.ln()

    def print_question_row(self, data, offset, num_problems):
        """Print a single row of questions (total question in a row is set by num_x_cell)"""
        for x in range(0, num_problems):
            self.print_top_row(str(x + 1 + offset))
            self.print_edge_vertical_separator()
        self.pdf.ln()
        for x in range(0, num_problems):
            if data[x + offset][1] == '/':
                self.print_second_row_division(data[x + offset][0], data[x + offset][2])
            else:
                self.print_second_row(data[x + offset][0])
            self.print_middle_vertical_separator()
        self.pdf.ln()
        for x in range(0, num_problems):
            if data[x + offset][1] == '/':
                self.print_third_row_division()
            else:
                self.print_third_row(data[x + offset][2], data[x + offset][1])
            self.print_middle_vertical_separator()
        self.pdf.ln()
        for x in range(0, num_problems):
            if data[x + offset][1] == '/':
                self.print_bottom_row_division()
            else:
                self.print_bottom_row()
            self.print_edge_vertical_separator()
        self.pdf.ln()

    def make_answer_page(self, data):
        """Print answer sheet"""
        self.pdf.add_page(orientation='L')
        self.pdf.set_font(self.font_1, size=self.large_font_size)
        self.pdf.cell(self.large_pad_size, self.large_pad_size, txt='Answers', new_x=XPos.LEFT, new_y=YPos.NEXT,
                      align='C')

        for i in range(len(data)):
            self.pdf.set_font(self.font_1, size=self.small_font_size)
            self.pdf.cell(self.pad_size, self.pad_size, txt=f'{i + 1}:', border='TLB', align='R')
            self.pdf.set_font(self.font_2, size=self.small_font_size)
            self.pdf.cell(self.pad_size * 2, self.pad_size, txt=str(data[i][3]), border='TB', align='R')
            self.pdf.cell(self.tiny_pad_size, self.pad_size, border='TRB', align='R')
            self.pdf.cell(self.tiny_pad_size, self.pad_size, align='C')
            if (i + 1) % 8 == 0:
                self.pdf.ln()


def main(type_, answers, answer_standalone, question_count, filename, gg,  email_student, email_corrector):
    """main function"""
    new_pdf = MathWorksheetGenerator(type_, question_count, gg)
    seed_question = new_pdf.get_list_of_questions(question_count)
    new_pdf.make_question_page(seed_question)


    exercise_path = filename
    answer_path = filename[:-4] + '-answers.pdf'
    if answer_standalone:
        new_pdf.pdf.output(exercise_path)
        new_pdf.pdf = FPDF()
        new_pdf.make_answer_page(seed_question)
        new_pdf.pdf.output(answer_path)
    else:
        if answers:
            new_pdf.make_answer_page(seed_question)
            answer_path  = filename
        new_pdf.pdf.output(exercise_path)

    if  email_student:
        from send_email import send_attachment
        send_attachment(receiver_email=email_student,attachment_path=Path(exercise_path))

    if  email_corrector:
        from send_email import send_attachment
        send_attachment(receiver_email=email_corrector,attachment_path=Path(answer_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate Maths Addition/Subtraction/Multiplication Exercise Worksheet'
    )
    parser.add_argument(
        '--type',
        default='+',
        choices=['+', '-', 'x', '/', 'mix'],
        help='type of calculation: '
             '+: Addition; '
             '-: Subtraction; '
             'x: Multiplication; '
             '/: Division; '
             'mix: Mixed; '
             '(default: +)',
    )
    parser.add_argument(
        '--min-digits', dest='min_digits', type=int,
        default='2',

        help='range of numbers: 1: 0-9, 2: 0-99, 3: 0-999' '(default: 2 -> 0-99)',
    )
    parser.add_argument(
        '--max-digits', dest='max_digits', type=int,
        default='2',

        help='range of numbers: 1: 0-9, 2: 0-99, 3: 0-999' '(default: 2 -> 0-99)',
    )
    parser.add_argument(
        '-q',
        '--question_count',
        type=int,
        default='80',  # Must be a multiple of 40
        help='total number of questions' '(default: 80)',
    )
    parser.add_argument('--output', metavar='filename.pdf', default='worksheet.pdf',
                        help='Output file to the given filename '
                             '(default: worksheet.pdf)')

    parser.add_argument('--answers', action='store_true', help='include answers')
    parser.add_argument('--answers-standalone', dest='answer_standalone', action='store_true',
                        help='include standalone answers')

    parser.add_argument('--email-student',dest='email_student', default=None)
    parser.add_argument('--email-corrector',dest='email_corrector', default=None)

    args = parser.parse_args()

    gg = NumberGenerator(args.type, args.min_digits, args.max_digits)

    main(args.type, args.answers, args.answer_standalone, args.question_count, args.output, gg, args.email_student, args.email_corrector)

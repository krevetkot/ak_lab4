#!/usr/bin/python3
"""Транслятор brainfuck в машинный код."""

import base64
import os
import re
import sys

from isa import Opcode, Term, opcode_to_size, to_bytes, to_hex

# комментарии разрешены только после #

class Translator:


    variables_map = None # имя - адрес
    functions_map = None
    variables_queue = None  # переменные будут сохранены в конце кода, после хальта,
    # чтобы гарантированно не мешать коду; имя - значение
    addresses_in_conditions = None  # код, куда нужно вставить аргумент - аргумент

    def __init__(self):
        self.variables_map = {}
        self.functions_map = {}
        self.variables_queue = {}
        self.addresses_in_conditions = {}

    def instructions(self):
        return {
            "@",
            "!",
            "VARIABLE",
            "IF",
            "ELSE",
            "THEN",
            "BEGIN",
            "WHILE",
            "REPEAT",
            ":",
            ";",
            "+",
            "-",
            "*",
            "/",
            "%",
            "AND",
            "OR",
            "NOT",
            "=",
            ">",
            "<",
            "DUP",
            "HALT",
        }


    def math_instructions(self):  # на этапе трансляции они будут развернуты в POP_AC + POP_DR + INSTR
        return {
            "+",
            "-",
            "*",
            "/",
            "%",
            "AND",
            "OR",
            "=",
            ">",
            "<",
        }


    def instr_without_arg(self):  # без аргумента
        return {
            "@",
            "!",
            ";",
            "+",
            "-",
            "*",
            "/",
            "%",
            "AND",
            "OR",
            "NOT",
            "=",
            ">",
            "<",
            "DUP",
            "HALT",
        }


    def second_type_instructions(self):  # с аргументом + LOAD_IMM + CALL
        return {"!", "IF", "ELSE", "WHILE", "REPEAT"}


    def word_to_opcode(self, symbol):
        """Отображение операторов исходного кода в коды операций."""
        return {
            "@": Opcode.LOAD,
            "!": Opcode.SAVE,
            "VARIABLE": Opcode.VARIABLE,
            "IF": Opcode.IF,
            "ELSE": Opcode.ELSE,
            "THEN": Opcode.THEN,
            "BEGIN": Opcode.BEGIN,
            "WHILE": Opcode.WHILE,
            "REPEAT": Opcode.REPEAT,
            ":": Opcode.DEFINE_FUNC,
            ";": Opcode.RETURN,
            "+": Opcode.PLUS,
            "-": Opcode.MINUS,
            "*": Opcode.MULT,
            "/": Opcode.DIV,
            "%": Opcode.MOD,
            "AND": Opcode.AND,
            "OR": Opcode.OR,
            "NOT": Opcode.NOT,
            "=": Opcode.EQUAL,
            ">": Opcode.GREATER,
            "<": Opcode.LESS,
            "DUP": Opcode.DUP,
            "HALT": Opcode.HALT,
        }.get(symbol)



    def text_to_terms(self, text):  # noqa: C901
        """Трансляция текста в последовательность операторов языка (токенов).

        Включает в себя:

        - отсеивание всего, что не: команда, имя переменной, имя лейбла, число;
        - проверка формальной корректности программы (if - then; while - repeat)
        """

        terms = []
        for line_num, line in enumerate(text.split("\n")):
            words = line.strip().split()
            for pos, word in enumerate(words, 1):
                if word == "#":
                    break  # если встретили хэштег, значит это комментарий, значит до конца строки все скипаем

                # слово может быть: командой, числом, лейблом, названием переменной
                # если это число, потом я его распаршу
                terms.append(Term(line_num, pos, word))  # Добавляем токен

        # pos - адрес, потом переименую

        if_flag = 0
        while_flag = 0
        for term in terms:
            if term.word == "IF":
                if_flag += 2
            if term.word == "ELSE":
                if_flag -= 1
            if term.word == "THEN":
                if_flag -= 1
            assert if_flag >= 0, "Unbalanced IF-ELSE-THEN!"

            if term.word == "BEGIN":
                while_flag += 2
            if term.word == "WHILE":
                while_flag -= 1
            if term.word == "REPEAT":
                while_flag -= 1
            assert while_flag >= 0, "Unbalanced BEGIN-WHILE-REPEAT!"
        assert if_flag == 0, "Unbalanced IF-ELSE-THEN!"
        assert while_flag == 0, "Unbalanced BEGIN-WHILE-REPEAT!"

        return terms





    def translate_stage_1(self, text):  # noqa: C901
        """Первый этап трансляции.
        Убираются все токены, которые не отображаются напрямую в команды,
        создается условная таблица линковки для лейблов функций и названий переменных.
        """
        terms = self.text_to_terms(text)

        # Транслируем термы в машинный код.
        code = []
        brackets_stack = []

        i = 0
        address = 8
        hex_number_pattern = r"^0[xX][0-9A-Fa-f]+$"
        dec_number_pattern = r"^[0-9]+$"
        last_begin = []
        while i < len(terms):
            term = terms[i]

            # если это 16 cc число - load_imm
            if re.fullmatch(hex_number_pattern, term.word):
                arg = int(term.word, 16)
                assert -2**63 <= arg <= 2**63-1, "Argument is not in range!"
                code.append(
                    {
                        "address": address,
                        "opcode": Opcode.LOAD_IMM,
                        "arg": arg,
                        "term": term,
                    }
                )
            # или 10 сс
            elif re.fullmatch(dec_number_pattern, term.word):
                arg = int(term.word)
                assert -2**63 <= arg <= 2**63-1, "Argument is not in range!"
                code.append(
                    {
                        "address": address,
                        "opcode": Opcode.LOAD_IMM,
                        "arg": arg,
                        "term": term,
                    }
                )

            elif term.word == 'S"':
                i += 1
                string = ""
                while not terms[i].word.endswith('"'):
                    string += terms[i].word
                    string += " "
                    i += 1
                string += terms[i].word[:-1]
                code.append(
                    {
                        "address": address,
                        "opcode": Opcode.LOAD_IMM,
                        "arg": string,
                        "term": term,
                    }
                )


            # если встретили определение слова
            elif self.word_to_opcode(term.word) == Opcode.VARIABLE:
                # после обработки всех термов, мы добавим его в конец
                value = code[-1]["arg"]  # берем отсюда, так как тут число уже прошло конвертацию
                label = terms[i + 1].word
                self.variables_queue[label] = value
                i += 1  # перепрыгиваем через лейбл, тк  мы его обработали
                code.pop()
                address -= 8

            # если встретили определение функции
            elif self.word_to_opcode(term.word) == Opcode.DEFINE_FUNC:
                label = terms[i + 1].word
                self.functions_map[label] = address
                i += 1
                address -= 4

            # обработка if - else - then, чтобы вставить им потом в аругменты адреса переходов
            elif self.word_to_opcode(term.word) == Opcode.IF:
                code.append({"address": address, "opcode": Opcode.POP_AC, "term": term})
                address += opcode_to_size[Opcode.POP_AC]
                brackets_stack.append({"address": address, "opcode": Opcode.IF})
                code.append({"address": address, "opcode": Opcode.IF, "arg": -1, "term": term})
            elif self.word_to_opcode(term.word) == Opcode.ELSE:
                self.addresses_in_conditions[brackets_stack.pop()["address"]] = address + 4
                brackets_stack.append({"address": address, "opcode": Opcode.ELSE})
                code.append({"address": address, "opcode": Opcode.ELSE, "arg": -1, "term": term})
            elif self.word_to_opcode(term.word) == Opcode.THEN:
                self.addresses_in_conditions[brackets_stack.pop()["address"]] = address
                address -= 4

            # обработка begin - while - repeat
            elif self.word_to_opcode(term.word) == Opcode.BEGIN:
                last_begin.append(address)
                address -= 4
            elif self.word_to_opcode(term.word) == Opcode.WHILE:
                code.append({"address": address, "opcode": Opcode.POP_AC, "term": term})
                address += opcode_to_size[Opcode.POP_AC]
                brackets_stack.append({"address": address, "opcode": Opcode.WHILE})
                code.append({"address": address, "opcode": Opcode.WHILE, "arg": -1, "term": term})
            elif self.word_to_opcode(term.word) == Opcode.REPEAT:
                self.addresses_in_conditions[brackets_stack.pop()["address"]] = address + 4
                code.append(
                    {
                        "address": address,
                        "opcode": Opcode.REPEAT,
                        "arg": last_begin.pop(),
                        "term": term,
                    }
                )

            # если встретили переменную или вызов функции
            elif term.word not in self.instructions():
                arg = term.word
                if arg in self.variables_queue:
                    code.append(
                        {
                            "address": address,
                            "opcode": Opcode.LOAD_IMM,
                            "arg": arg,
                            "term": term,
                        }
                    )
                elif arg in self.functions_map:
                    code.append(
                        {
                            "address": address,
                            "opcode": Opcode.CALL,
                            "arg": self.functions_map[arg],
                            "term": term,
                        }
                    )
                else:
                    assert arg in self.variables_map or arg in self.functions_map, "Label is not defined!"

            elif self.word_to_opcode(term.word) == Opcode.NOT:
                code.append({"address": address, "opcode": Opcode.POP_AC, "term": term})
                address += 1
                code.append({"address": address, "opcode": self.word_to_opcode(term.word), "term": term})

            elif term.word in self.math_instructions():
                code.append({"address": address, "opcode": Opcode.POP_AC, "term": term})
                address += 1
                code.append({"address": address, "opcode": Opcode.POP_DR, "term": term})
                address += 1
                code.append({"address": address, "opcode": self.word_to_opcode(term.word), "term": term})

            elif self.word_to_opcode(term.word) == Opcode.SAVE:
                code.append({"address": address, "opcode": Opcode.POP_DR, "term": term})
                address += 1
                code.append({"address": address, "opcode": Opcode.POP_AC, "term": term})
                address += 1
                code.append({"address": address, "opcode": self.word_to_opcode(term.word), "term": term})

            elif self.word_to_opcode(term.word) == Opcode.LOAD:
                code.append({"address": address, "opcode": Opcode.POP_AC, "term": term})
                address += 1
                code.append({"address": address, "opcode": self.word_to_opcode(term.word), "term": term})

            else:
                code.append({"address": address, "opcode": self.word_to_opcode(term.word), "term": term})

            if term.word in self.instr_without_arg():
                address -= 3

            i += 1
            address += 4

        return code


    def translate_stage_2(self, code):  # noqa: C901
        """
        Вместо лейблов подставляются адреса,
        в if и while подставляются адреса переходов,
        переменные сохраняются после halt.
        """
        # сначала сохраним переменные в конце кода, чтобы потом подставлять их адреса
        curr_address = code[-1]["address"] + 1
        for label, value in self.variables_queue.items():
            self.variables_map[label] = curr_address
            code.append({"address": curr_address, "arg": value})
            if isinstance(value, int):
                if -2**31 <= value <= 2**31-1:
                    size = 4
                else:
                    size = 8
            elif isinstance(value, str):
                size = len(value)*4
            curr_address += size

        for instruction in code:
            if "arg" in instruction:
                arg = instruction["arg"]
                if arg == -1:
                    instruction["arg"] = self.addresses_in_conditions[instruction["address"]]
                elif isinstance(arg, str) and "opcode" in instruction:
                    instruction["arg"] = self.variables_map[arg]
                    # если переменной с таким именем нет, транслятор выдаст ошибку еще на первом этапе

        return code


    def get_first_executable_instr(self, code):
        address = 8
        for instr in code:
            if "opcode" in instr:
                if instr["opcode"] == Opcode.RETURN:
                    address = instr["address"] + 1
        return address


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    translator = Translator()
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translator.translate_stage_1(source)
    code = translator.translate_stage_2(code)
    first_ex_instr = translator.get_first_executable_instr(code)
    binary_code = to_bytes(code, first_ex_instr)
    hex_code = to_hex(code, translator.variables_map)

    # Убедимся, что каталог назначения существует
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)

    # Запишем выходные файлы
    with open(target, "wb") as f:
        f.write(binary_code)
    with open(target + ".hex", "w") as f:
        f.write(hex_code)
    with open(target + ".base64", "w") as f:
        f.write(base64.b64encode(binary_code).decode("utf-8"))

    print("source LoC:", len(source.split(" ")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

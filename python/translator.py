#!/usr/bin/python3
"""Транслятор brainfuck в машинный код."""

import os
import re
import sys

from isa import Opcode, Term, to_bytes, to_hex

# комментарии разрешены только после #


def instructions():
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
        "and",
        "or",
        "not",
        "=",
        ">",
        "<",
        "HALT",
    }


def math_instructions(): # на этапе трансляции они будут развернуты в POP_AC + POP_DR + INSTR
    return {
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
    }



def instr_without_arg():  # без аргумента
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
        "HALT",
    }


def second_type_instructions():  # с аргументом + LOAD_IMM + LOAD_ADDR + CALL
    return {"!", "IF", "ELSE", "WHILE", "REPEAT"}


def word_to_opcode(symbol):
    """Отображение операторов исходного кода в коды операций."""
    return {
        "@": Opcode.LOAD,
        "!": Opcode.SAVE,
        "VARIABLE": Opcode.VARIABLE,
        "IF": Opcode.IF,
        "THEN": Opcode.THEN,
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
        "HALT": Opcode.HALT,
    }.get(symbol)


def text_to_terms(text):
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

    ifFlag = 0
    whileFlag = 0
    for term in terms:
        if term.word == "IF":
            ifFlag += 2
        if term.word == "ELSE":
            ifFlag -= 1
        if term.word == "THEN":
            ifFlag -= 1
        assert ifFlag >= 0, "Unbalanced IF-ELSE-THEN!"

        if term.word == "BEGIN":
            whileFlag += 2
        if term.word == "WHILE":
            whileFlag -= 1
        if term.word == "REPEAT":
            whileFlag -= 1
        assert whileFlag >= 0, "Unbalanced BEGIN-WHILE-REPEAT!"
    assert ifFlag == 0, "Unbalanced IF-ELSE-THEN!"
    assert whileFlag == 0, "Unbalanced BEGIN-WHILE-REPEAT!"

    return terms


variables_map = {}  # имя - адрес
functions_map = {}
variables_queue = {}  # переменные будут сохранены в конце кода, после хальта,
# чтобы гарантированно не мешать коду; имя - значение
addresses_in_conditions = {}  # код, куда нужно вставить аргумент - аргумент


def translate_stage_1(text):
    """Первый этап трансляции.
    Убираются все токены, которые не отображаются напрямую в команды,
    переменные заносятся в память (после кода),
    создается условная таблица линковки для лейблов функций и названий переменных.
    """
    terms = text_to_terms(text)

    # Транслируем термы в машинный код.
    code = []
    brackets_stack = []
    # надо бы сделать отдельный файлик который управляет памятью. инициализирует например
    # стек у нас стопроц в общей памяти, просто с конца добавляется
    # или память это просто битовый файл?

    i = 0
    address = 8
    hex_number_pattern = r"^0[xX][0-9A-Fa-f]+$"
    dec_number_pattern = r"^[0-9]+$"
    last_begin = 0
    while i < len(terms):
        term = terms[i]

        # если это 16 cc число - load_imm
        if re.fullmatch(hex_number_pattern, term.word):
            arg = int(term.word, 16)
            assert arg <= 67108863 and arg >= -67108864, "Argument is not in range!"
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
            assert arg <= 67108863 and arg >= -67108864, "Argument is not in range!"
            code.append(
                {
                    "address": address,
                    "opcode": Opcode.LOAD_IMM,
                    "arg": arg,
                    "term": term,
                }
            )

        # если встретили определение слова
        elif term.word == "VARIABLE":
            # после обработки всех термов, мы добавим его в конец
            value = code[-1][
                "arg"
            ]  # берем отсюда, так как тут число уже прошло конвертацию
            label = terms[i + 1].word
            variables_queue[label] = value
            i += 1  # перепрыгиваем через лейбл, тк  мы его обработали
            code.pop()
            address -= 8

        # если встретили определение функции
        elif term.word == ":":
            label = terms[i + 1].word
            functions_map[label] = address
            i += 1
            address -= 4

        # обработка if - else - then, чтобы вставить им потом в аругменты адреса переходов
        elif term.word == "IF":
            brackets_stack.append({"address": address, "opcode": Opcode.IF})
            code.append(
                {"address": address, "opcode": Opcode.IF, "arg": -1, "term": term}
            )
        elif term.word == "ELSE":
            addresses_in_conditions[brackets_stack.pop()["address"]] = address + 1
            brackets_stack.append({"address": address, "opcode": Opcode.ELSE})
            code.append(
                {"address": address, "opcode": Opcode.ELSE, "arg": -1, "term": term}
            )
        elif term.word == "THEN":
            addresses_in_conditions[brackets_stack.pop()["address"]] = address
            address -= 4

        elif term.word == "BEGIN":
            last_begin = address
            address -= 4
        elif term.word == "WHILE":
            brackets_stack.append({"address": address, "opcode": Opcode.WHILE})
            code.append(
                {"address": address, "opcode": Opcode.WHILE, "arg": -1, "term": term}
            )
        elif term.word == "REPEAT":
            addresses_in_conditions[brackets_stack.pop()["address"]] = address
            code.append(
                {
                    "address": address,
                    "opcode": Opcode.REPEAT,
                    "arg": last_begin,
                    "term": term,
                }
            )

        # если встретили переменную или вызов функции
        elif term.word not in instructions():
            arg = term.word
            if arg in variables_queue:
                code.append(
                    {
                        "address": address,
                        "opcode": Opcode.LOAD_ADDR,
                        "arg": arg,
                        "term": term,
                    }
                )
            elif arg in functions_map:
                code.append(
                    {
                        "address": address,
                        "opcode": Opcode.CALL,
                        "arg": functions_map[arg],
                        "term": term,
                    }
                )
            else:
                assert (
                    arg in variables_map or arg in functions_map
                ), "Label is not defined!"

        elif term.word in math_instructions():
            code.append(
                {
                    "address": address,
                    "opcode": Opcode.POP_AC,
                    "term": term,
                },
            )  
            address += 1
            code.append(
                {
                    "address": address,
                    "opcode": Opcode.POP_DR,
                    "term": term,
                },
            )  
            address += 1
            code.append(
                {
                    "address": address,
                    "opcode": word_to_opcode(term.word),
                    "term": term,
                },
            ) 

        elif word_to_opcode(term.word) == Opcode.SAVE:
            code.append(
                {
                    "address": address,
                    "opcode": Opcode.POP_DR,
                    "term": term,
                },
            )  
            address += 1
            code.append(
                {
                    "address": address,
                    "opcode": Opcode.POP_AC,
                    "term": term,
                },
            )  
            address += 1
            code.append(
                {
                    "address": address,
                    "opcode": word_to_opcode(term.word),
                    "term": term,
                },
            )

        elif word_to_opcode(term.word) == Opcode.LOAD:
            code.append(
                {
                    "address": address,
                    "opcode": Opcode.POP_AC,
                    "term": term,
                },
            )  
            address += 1
            code.append(
                {
                    "address": address,
                    "opcode": word_to_opcode(term.word),
                    "term": term,
                },
            ) 
        
             
        else:
            code.append(
                {"address": address, "opcode": word_to_opcode(term.word), "term": term}
            )

        if term.word in instr_without_arg():
            address -= 3

        i += 1
        address += 4

    return code


def translate_stage_2(code):
    """
    Вместо лейблов подставляются адреса,
    в if и while подставляются адреса переходов,
    переменные сохраняются после halt.
    """
    # сначала сохраним переменные в конце кода, чтобы потом подставлять их адреса
    curr_address = code[-1]["address"] + 1
    for label, value in variables_queue.items():
        variables_map[label] = curr_address
        code.append({"address": curr_address, "arg": value})
        curr_address += 4

    for instruction in code:
        if "arg" in instruction:
            arg = instruction["arg"]
            if arg == -1:
                instruction["arg"] = addresses_in_conditions[instruction["address"]]
            elif isinstance(arg, str):
                instruction["arg"] = variables_map[arg]
                # если переменной с таким именем нет, транслятор выдаст ошибку еще на первом этапе

    return code


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate_stage_1(source)
    code = translate_stage_2(code)
    for el in code:
        print(el)
    binary_code = to_bytes(code)
    hex_code = to_hex(code, variables_map)

    # Убедимся, что каталог назначения существует
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)

    # Запишем выходные файлы
    with open(target, "wb") as f:
        f.write(binary_code)
    with open(target + ".hex", "w") as f:
        f.write(hex_code)


if __name__ == "__main__":
    assert (
        len(sys.argv) == 3
    ), "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

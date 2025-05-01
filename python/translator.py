#!/usr/bin/python3
"""Транслятор brainfuck в машинный код.
"""

import os
import re
import sys

from isa import Opcode, Term, to_bytes, to_hex
from memory import Memory 

# у нас должна быть таблица линковки!!!!!!!!!!
# комментарии если и будут разрешены, то только после #
# нужен двухэтапный проход транслятора: сначала вычленяем инструкции, потом подставляем адреса


def instructions():
    return {"@", "@@", "!", "VARIABLE", "IF", "ELSE", "THEN", "BEGIN", "WHILE", "REPEAT", ":", ";", "+", "-", "*", "/", "%",
            "and", "or", "not", "=", ">", "<", "HALT"}

def first_type_instructions(): # без аргумента
    return {"@", "!", ";", "+", "-", "*", "/", "%","and", "or", "not", "=", ">", "<", "HALT"}

def seconf_type_instructions(): # с аргументом + LOAD_IMM
    return {"@@", "!", "IF", "ELSE", "WHILE", "REPEAT", ":", ";", "+", "-", "*", "/", "%",
        "and", "or", "not", "=", ">", "<"}



def word_to_opcode(symbol):
    """Отображение операторов исходного кода в коды операций."""
    return {
        "@": Opcode.LOAD,
        "@@": Opcode.LOAD_ADDR,
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
        "and": Opcode.AND,
        "or": Opcode.OR,
        "not": Opcode.NOT,
        "=": Opcode.EQUAL,
        ">": Opcode.GREATER,
        "<": Opcode.LESS
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
                break #если встретили хэштег, значит это комментарий, значит до конца строки все скипаем

            # слово может быть: командой, числом, лейблом, названием переменной
            # если это число, потом я его распаршу
            terms.append(Term(line_num, pos, word))  # Добавляем токен
            
    # pos - адрес, потом переименую

    ifFlag = 0
    whileFlag = 0
    for term in terms:
        if term.word == "IF":
            ifFlag += 1
        if term.word == "THEN":
            ifFlag -= 1
        assert ifFlag >= 0, "Unbalanced IF-THEN!"

        if term.word == "WHILE":
            whileFlag += 1
        if term.word == "REPEAT":
            whileFlag -= 1
        assert whileFlag >= 0, "Unbalanced WHILE-REPEAT!"
    assert ifFlag == 0, "Unbalanced IF-THEN!"
    assert whileFlag == 0, "Unbalanced WHILE-REPEAT!"

    return terms

variables_map = {} # имя - адрес
functions_map = {}
variables_queue = {} # переменные будут сохранены в конце кода, после хальта, 
# чтобы гарантированно не мешать коду

def translate_stage_1(text, memory):
    """Первый этап трансляции.
    Убираются все токены, которые не отображаются напрямую в команды, 
    переменные заносятся в память (после кода),
    создается условная таблица линковки для лейблов функций и названий переменных.
    """
    terms = text_to_terms(text)

    # Транслируем термы в машинный код.
    code = []
    brackets_stack = [] 
    addresses_in_conditions = {} # код, куда нужно вставить аргумент - аргумент
    # надо бы сделать отдельный файлик который управляет памятью. инициализирует например
    # стек у нас стопроц в общей памяти, просто с конца добавляется
    # или память это просто битовый файл?

    i = 0
    address = 0
    hex_number_pattern = r'^0[xX][0-9A-Fa-f]+$'
    dec_number_pattern = r'^[0-9]+$'
    last_begin = 0
    while i < len(terms):
        term = terms[i]

        # если это 16 cc число - load_imm
        if re.fullmatch(hex_number_pattern, term.word):
            arg = int(term.word, 16)
            assert arg <= 67108863 and arg >= -67108864, "Argument is not in range!"
            code.append({"address": address, "opcode": Opcode.LOAD_IMM, "arg": arg, "term": term})
        # или 10 сс
        elif re.fullmatch(dec_number_pattern, term.word):
            arg = int(term.word)
            assert arg <= 67108863 and arg >= -67108864, "Argument is not in range!"
            code.append({"address": address, "opcode": Opcode.LOAD_IMM, "arg": arg, "term": term})

        # если встретили определение слова
        elif term.word == "VARIABLE":
            # после обработки всех термов, мы добавим его в конец
            value = code[-1]['arg'] # берем отсюда, так как тут число уже прошло конвертацию
            label = terms[i+1].word
            variables_queue[label] = value
            i += 1 # перепрыгиваем через лейбл, тк  мы его обработали
            address -= 1

        # если встретили определение функции 
        elif term.word == ":":
            label = terms[i+1].word
            functions_map[label] = address
            i += 1

        # обработка if - else - then, чтобы вставить им потом в аругменты адреса переходов 
        elif term.word == "IF":
            brackets_stack.append({"address": address, "opcode": Opcode.IF})
            code.append({"address": address, "opcode": Opcode.IF, "arg": -1, "term": term})
        elif term.word == "ELSE":
            addresses_in_conditions[brackets_stack.pop()['address']] = address + 1
            brackets_stack.append({"address": address, "opcode": Opcode.ELSE})
            code.append({"address": address, "opcode": Opcode.ELSE, "arg": -1, "term": term})
        elif term.word == "THEN":
            addresses_in_conditions[brackets_stack.pop()['address']] = address
            address -= 1

        elif term.word == "BEGIN":
            last_begin = address
            address -= 1
        elif term.word == "WHILE":
            brackets_stack.append({"address": address, "opcode": Opcode.WHILE})
            code.append({"address": address, "opcode": Opcode.WHILE, "arg": -1, "term": term})
        elif term.word == "REPEAT":
            addresses_in_conditions[brackets_stack.pop()['address']] = address 
            code.append({"address": address, "opcode": Opcode.REPEAT, "arg": last_begin, "term": term})
        
        # если встретили переменную или вызов функции
        elif term.word not in instructions():
            arg = term.word
            if arg in variables_queue:
                code.append({"address": address, "opcode": Opcode.LOAD_ADDR, "arg": arg, "term": term})
            elif arg in functions_map:
                code.append({"address": address, "opcode": Opcode.CALL, "arg": arg, "term": term})
            else:
                assert arg in variables_map or arg in functions_map, "Label is not defined!"


        else:
            code.append({"address": address, "opcode": word_to_opcode(term.word), "term": term})

        i += 1
        address += 1

    # Добавляем инструкцию остановки процессора в конец программы.
    code.append({"index": len(code), "opcode": Opcode.HALT})
    return code


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source, encoding="utf-8") as f:
        source = f.read()

    MEMORY_SIZE = 1000
    memory = Memory(MEMORY_SIZE)
    code = translate_stage_1(source, memory)
    for el in code:
        print(el)
    exit
    binary_code = to_bytes(code)
    hex_code = to_hex(code)

    # Убедимся, что каталог назначения существует
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)

    # Запишем выходные файлы
    with open(target, "wb") as f:
        f.write(binary_code)
    with open(target + ".hex", "w") as f:
        f.write(hex_code)

    # Обратите внимание, что память данных не экспортируется в файл, так как
    # в случае brainfuck она может быть инициализирована только 0.
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

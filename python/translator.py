#!/usr/bin/python3
"""Транслятор brainfuck в машинный код.
"""

import os
import re
import sys

from isa import Opcode, Term, to_bytes, to_hex, write_json
from memory import Memory 

# у нас должна быть таблица линковки!!!!!!!!!!
# комментарии если и будут разрешены, то только после #
# нужен двухэтапный проход транслятора: сначала вычленяем инструкции, потом подставляем адреса


def instructions():
    return {"@", "@@", "!", "VARIABLE", "IF", "ELSE", "THEN", "BEGIN", "WHILE", "REPEAT", ":", ";", "+", "-", "*", "/", "%",
            "and", "or", "not", "=", ">", "<"}

def first_type_instructions(): # без аргумента
    return {"@", "!", ";", "+", "-", "*", "/", "%","and", "or", "not", "=", ">", "<"}

def seconf_type_instructions(): # с аргументом + LOAD_IMM
    return {"@@", "!", "IF", "ELSE", "WHILE", "REPEAT", ":", ";", "+", "-", "*", "/", "%",
        "and", "or", "not", "=", ">", "<"}



def symbol2opcode(symbol):
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


def text2terms(text):
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
        if term.symbol == "IF":
            ifFlag += 1
        if term.symbol == "THEN":
            ifFlag -= 1
        assert ifFlag >= 0, "Unbalanced IF-THEN!"

        if term.symbol == "WHILE":
            whileFlag += 1
        if term.symbol == "REPEAT":
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
    terms = text2terms(text)

    # Транслируем термы в машинный код.
    code = []
    brackets_stack = [] 
    addresses_in_conditious = {} # код, куда нужно вставить аргумент - аргумент
    # надо бы сделать отдельный файлик который управляет памятью. инициализирует например
    # стек у нас стопроц в общей памяти, просто с конца добавляется
    # или память это просто битовый файл?

    i = 0
    address = 0
    while i < len(terms):
        term = terms[i]
        hex_number_pattern = r'^0[xX][0-9A-Fa-f]+$'
        dec_number_pattern = r'^[0-9]+$'
        # load_imm
        if re.fullmatch(hex_number_pattern, term.word) or re.fullmatch(dec_number_pattern, term.word):
            arg = int(term.word)
            assert arg <= 67108863 and arg >= -67108864, "Argument is not in range!"
            code.append({"address": address, "opcode": Opcode.LOAD_IMM, "arg": arg, "term": term})

        # если встретили определение слова
        if term.word == "VARIABLE":
            # после обработки всех термов, мы добавим его в конец
            value = terms[i-1]
            label = terms[i+1]
            variables_queue[label] = value
            i += 1 # перепрыгиваем через лейбл, тк  мы его обработали

        # если встретили определение функции 
        if term.word == ":":
            label = terms[i+1].word
            functions_map[label] = address
            i += 1

        # обработка if - else - then, чтобы вставить им потом в аругменты адреса переходов 
        if term.word == "IF":
            brackets_stack.append({"address": address, "opcode": Opcode.IF})
            code.append({"address": address, "opcode": Opcode.IF, "arg": -1, "term": term})
        if term.word == "ELSE":
            addresses_in_conditious[brackets_stack.pop.address] = address + 1
            brackets_stack.append({"address": address, "opcode": Opcode.ELSE})
            code.append({"address": address, "opcode": Opcode.ELSE, "arg": -1, "term": term})
        if term.word == "THEN":
            addresses_in_conditious[brackets_stack.pop.address] = address
        
                
        

        # если встретили переменную или вызов функции
        if term.word not in instructions():
            arg = term.word
            if arg in variables_map:
                code.append({"address": address, "opcode": Opcode.LOAD_ADDR, "arg": arg, "term": term})
            elif arg in functions_map:
                code.append({"address": address, "opcode": Opcode.CALL, "arg": arg, "term": term})
            else:
                assert arg in variables_map or arg in functions_map, "Label is not defined!"


        else:
            code.append({"address": address, "opcode": symbol2opcode(term.symbol), "term": term})



        if term.word == "[":
            # оставляем placeholder, который будет заменён в конце цикла
            code.append(None)
            return_stack.append(pc)
        elif term.word == "]":
            # формируем цикл с началом из jmp_stack
            begin_pc = return_stack.pop()
            begin = {"opcode": Opcode.JZ, "arg": pc + 1, "term": terms[begin_pc]}
            end = {"opcode": Opcode.JMP, "arg": begin_pc, "term": term}
            code[begin_pc] = begin
            code.append(end)
        else:
            # Обработка тривиально отображаемых операций.
            code.append({"index": pc, "opcode": symbol2opcode(term.symbol), "term": term})

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
    binary_code = to_bytes(code)
    hex_code = to_hex(code)

    # Убедимся, что каталог назначения существует
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)

    # Запишим выходные файлы
    if target.endswith(".bin"):
        with open(target, "wb") as f:
            f.write(binary_code)
        with open(target + ".hex", "w") as f:
            f.write(hex_code)
    else:
        write_json(target, code)

    # Обратите внимание, что память данных не экспортируется в файл, так как
    # в случае brainfuck она может быть инициализирована только 0.
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

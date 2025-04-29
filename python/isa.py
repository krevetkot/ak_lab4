"""Представление исходного и машинного кода.

Определено два представления:
- Бинарное
- JSON
"""

import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    """Opcode для инструкций.

    Можно разделить на две группы:

    1. Непосредственно представленные на уровне языка: `RIGHT`, `LEFT`, `INC`, `DEC`, `INPUT`, `PRINT`.
    2. Инструкции для управления, где:
        - `JMP`, `JZ` -- безусловный и условный переходы:

            | Operator Position | Исходный код | Машинный код |
            |-------------------|--------------|--------------|
            | n                 | `[`          | `JZ (k+1)`   |
            | ...               | ...          |              |
            | k                 |              |              |
            | k+1               | `]`          | `JMP n`      |

        - `HALT` -- остановка машины.
    """

    VARIABLE = "variable"
    DEFINE_FUNC = "define_func" #: word code ;

    CALL = "call"
    RETURN = "return" # НИЖЕ ЕГО ЕЩЕ НЕТ. ЭТО КОД ОПЕРАЦИИ ;
    JUMP = "jmp"
    LOAD_ADDR = "loadaddr " # НИЖЕ ЕГО ЕЩЕ НЕТ. 
    # ЭТО ЗАГРУЗКА ПО лейблу / адресу

    LOAD_IMM = "loadimm" # синтаксис - просто число
    LOAD = "load" # использует @ загружает по адресу, портит DR
    SAVE = "save"

    IF = "if"
    ELSE = "else"
    THEN = "then"
    WHILE = "while"
    REPEAT = "repeat"

    # все математическиеи и логические операции вторым аргументом принимают ПЕРЕМЕННУЮ
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIV = "/"
    MOD = "%"
    AND = "and"
    OR = "or"
    NOT = "not"
    EQUAL = "="
    LESS = "<"
    GREATER = ">"

    HALT = "halt"


    def __str__(self):
        """Переопределение стандартного поведения `__str__` для `Enum`: вместо
        `Opcode.INC` вернуть `increment`.
        """
        return str(self.value)



class Term(namedtuple("Term", "line pos word")):
    """Описание выражения из исходного текста программы.

    Сделано через класс, чтобы был docstring.
    """


# Словарь соответствия кодов операций их бинарному представлению
opcode_to_binary = {
    Opcode.VARIABLE: 0x0, #00000
    Opcode.DEFINE_FUNC: 0x1,  # 00001
    Opcode.LOAD_IMM: 0x2,  # 00010
    Opcode.LOAD: 0x3,  # 00011
    Opcode.SAVE: 0x4,  # 00100

    Opcode.IF: 0x5,  # 00101
    Opcode.THEN: 0x6,    # 00110
    Opcode.WHILE: 0x7,   # 00111
    Opcode.REPEAT: 0x8,  # 01000

    Opcode.PLUS: 0x9,    # 01001
    Opcode.MINUS: 0xA,   # 01010
    Opcode.MULT: 0xB,    # 01011
    Opcode.DIV: 0xC,     # 01100
    Opcode.MOD: 0xD,     # 01101
    Opcode.AND: 0xE,     # 01110
    Opcode.OR: 0xF,      # 01111
    Opcode.NOT: 0x10,    # 10000
    Opcode.EQUAL: 0x11,  # 10001
    Opcode.LESS: 0x12,   # 10010
    Opcode.GREATER: 0x13,# 10011
    Opcode.HALT: 0x14    # 10100

    # получается : это WORD
    # а ; это jump на адрес возврата
    # и при вызове какого-то слова, мы джампимся на адрес, где оно определено
}

binary_to_opcode = {
    0x0: Opcode.VARIABLE,  # 00000
    0x1: Opcode.DEFINE_FUNC,     # 00001
    0x2: Opcode.LOAD_IMM, # 00010
    0x3: Opcode.LOAD,     # 00011
    0x4: Opcode.SAVE,     # 00100
    0x5: Opcode.IF,       # 00101
    0x6: Opcode.THEN,     # 00110
    0x7: Opcode.WHILE,    # 00111
    0x8: Opcode.REPEAT,   # 01000

    0x9: Opcode.PLUS,     # 01001
    0xA: Opcode.MINUS,    # 01010
    0xB: Opcode.MULT,     # 01011
    0xC: Opcode.DIV,      # 01100
    0xD: Opcode.MOD,      # 01101
    0xE: Opcode.AND,      # 01110
    0xF: Opcode.OR,       # 01111
    0x10: Opcode.NOT,     # 10000
    0x11: Opcode.EQUAL,   # 10001
    0x12: Opcode.LESS,    # 10010
    0x13: Opcode.GREATER, # 10011
    0x14: Opcode.HALT     # 10100
}


def to_bytes(code):
    """Преобразует машинный код в бинарное представление.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 31...27 │ 26                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      адрес перехода                         │
    └─────────┴─────────────────────────────────────────────────────────────┘
    """
    binary_bytes = bytearray()
    for instr in code:
        # Получаем бинарный код операции
        opcode_bin = opcode_to_binary[instr["opcode"]] << 27

        # Добавляем адрес перехода, если он есть
        arg = instr.get("arg", 0)

        # Формируем 32-битное слово: опкод (5 бит) + адрес (27 бит)
        binary_instr = opcode_bin | (arg & 0x07FFFFFF)

        # Преобразуем 32-битное целое число в 4 байта (big-endian)
        binary_bytes.extend(
            ((binary_instr >> 24) & 0xFF, (binary_instr >> 16) & 0xFF, (binary_instr >> 8) & 0xFF, binary_instr & 0xFF)
        )

    return bytes(binary_bytes)


def to_hex(code):
    """Преобразует машинный код в текстовый файл с шестнадцатеричным представлением.

    Формат вывода:
    <address> - <HEXCODE> - <mnemonic>
    Например:
    20 - 03340301 - add #01 <- 34 + #03
    """
    binary_code = to_bytes(code)
    result = []

    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break

        # Формируем 32-битное слово из 4 байтов
        word = (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]

        # Получаем опкод и адрес
        opcode_bin = (word >> 27) & 0xF
        arg = word & 0x07FFFFFF

        # Преобразуем опкод и адрес в мнемонику
        mnemonic = binary_to_opcode[opcode_bin].value
 
        if opcode_bin in (0x2):  # load_imm требует аргумент
            mnemonic = f"{mnemonic} {arg}"

        # Формируем строку в требуемом формате
        hex_word = f"{word:08X}"
        address = i // 4
        line = f"{address} - {hex_word} - {mnemonic}"
        result.append(line)

    return "\n".join(result)


def from_bytes(binary_code):
    """Преобразует бинарное представление машинного кода в структурированный формат.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 31...27 │ 26                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      адрес перехода                         │
    └─────────┴─────────────────────────────────────────────────────────────┘
    """
    structured_code = []
    # Обрабатываем байты по 4 за раз для получения 32-битных инструкций
    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break

        # Формируем 32-битное слово из 4 байтов
        binary_instr = (
            (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]
        )

        # Извлекаем опкод (старшие 5 бит)
        opcode_bin = (binary_instr >> 27) & 0xF8
        opcode = binary_to_opcode[opcode_bin]

        # Извлекаем адрес перехода (младшие 27 бит)
        arg = binary_instr & 0x07FFFFFF

        # Формируем структуру инструкции
        instr = {"index": i // 4, "opcode": opcode}

        # Добавляем адрес перехода только для инструкций перехода
        if opcode in (Opcode.LOAD_IMM, Opcode.LOAD, Opcode.SAVE):
            instr["arg"] = arg

        structured_code.append(instr)

    return structured_code

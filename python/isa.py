"""Представление исходного и машинного кода."""

from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    """Opcode для инструкций."""

    # спец опкод для сохранения в памяти (больше для отладки и трансляции)
    VARIABLE_IN_MEMORY = "variable_in_memory"

    # инструкции без аргумента
    LOAD = "load"
    SAVE = "save"
    PLUS = "add"
    MINUS = "sub"
    MULT = "mul"
    DIV = "div"
    MOD = "mod"
    AND = "and"
    OR = "or"
    NOT = "not"
    EQUAL = "equal"
    LESS = "less"
    GREATER = "greater"
    HALT = "halt"
    RETURN = "return"
    POP_AC = "popac"
    POP_DR = "popdr"
    PUSH = "push"

    # инструкции, которые не отображаются в память
    VARIABLE = "variable"
    DEFINE_FUNC = "define_func"
    THEN = "then"
    BEGIN = "begin"

    # инструкции с аргументом
    LOAD_IMM = "loadimm"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    REPEAT = "repeat"
    CALL = "call"

    def __str__(self):
        """Переопределение стандартного поведения `__str__` для `Enum`: вместо
        `Opcode.INC` вернуть `increment`.
        """
        return str(self.value)


class Term(namedtuple("Term", "line pos word")):
    """Описание выражения из исходного текста программы."""


# Словарь соответствия кодов операций их бинарному представлению
opcode_to_binary = {
    # с 1 или нет?
    Opcode.LOAD: 0x2,  # 00000010
    Opcode.PLUS: 0x4,  # 00000100
    Opcode.MINUS: 0x6,  # 00000110
    Opcode.MULT: 0x8,  # 00001000
    Opcode.DIV: 0x10,  # 00001010
    Opcode.MOD: 0x12,  # 00001100
    Opcode.AND: 0x14,  # 00001110
    Opcode.OR: 0x16,  # 00010000
    Opcode.NOT: 0x18,  # 00010010
    Opcode.EQUAL: 0x20,  # 00010100
    Opcode.LESS: 0x22,  # 00010110
    Opcode.GREATER: 0x24,  # 00011000
    Opcode.HALT: 0x26,  # 00011010
    Opcode.RETURN: 0x28,  # 00011100
    Opcode.SAVE: 0x30,  # 00011110
    Opcode.POP_AC: 0x32,  # 0100000
    Opcode.POP_DR: 0x34,  # 0100010
    Opcode.PUSH: 0x36,  # 0100100
    Opcode.LOAD_IMM: 0x3,  # 00000011
    Opcode.CALL: 0x5,  # 00000101
    Opcode.IF: 0x7,  # 00000111
    Opcode.ELSE: 0x9,  # 00001001
    Opcode.WHILE: 0x11,  # 00001011
    Opcode.REPEAT: 0x13,  # 00001101
}

binary_to_opcode = {binary: opcode for opcode, binary in opcode_to_binary.items()}


def to_bytes(code, first_ex_instr):
    """Преобразует машинный код в бинарное представление.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 31...24 │ 23                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      аргумент                               │
    └─────────┴─────────────────────────────────────────────────────────────┘
    """
    binary_bytes = bytearray()
    binary_bytes += bytes(4)
    binary_bytes += first_ex_instr.to_bytes(4, byteorder="big")
    for instr in code:
        if "opcode" in instr:
            opcode_bin = opcode_to_binary[instr["opcode"]]
            binary_bytes.append(opcode_bin)
        else:
            binary_bytes.append(0)

        if "arg" in instr:
            arg = instr.get("arg", 0)
            binary_bytes.extend(((arg >> 16) & 0xFF, (arg >> 8) & 0xFF, arg & 0xFF))
    return bytes(binary_bytes)


def to_hex(code, variables_map):
    addr_to_var = {addr: name for name, addr in variables_map.items()}
    """Преобразует машинный код в текстовый файл c шестнадцатеричным представлением.

    Формат вывода:
    <address> - <HEXCODE> - <mnemonic>
    """
    binary_code = to_bytes(code, 8)
    result = []
    after_halt = False

    i = 8
    while i < len(binary_code):
        has_argument = (binary_code[i]) & 0x1 == 1

        if has_argument & (not after_halt) & i + 4 >= len(binary_code):
            break

        address = i
        if after_halt:
            word = (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]
            mnemonic = addr_to_var[address]
            i += 4
        else:
            mnemonic = binary_to_opcode[binary_code[address]].value
            if binary_to_opcode[binary_code[address]] == Opcode.HALT:
                after_halt = True
            if has_argument:
                word = (
                    (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]
                )
                arg = (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]
                i += 4
            else:
                word = binary_code[i]
                i += 1

        # Формируем строку в требуемом формате
        hex_word = f"{word:10X}"  # количество символов в строке
        if has_argument:
            line = f"{hex(address)} - {hex_word} - {mnemonic} ({arg:08X})"
        else:
            line = f"{hex(address)} - {hex_word} - {mnemonic}"
        result.append(line)

    return "\n".join(result)

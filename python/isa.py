"""Представление исходного и машинного кода.
"""

from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    """Opcode для инструкций.
    """
    # спец опкод для сохранения в памяти (больше для отладки и трансляции)
    VARIABLE_IN_MEMORY = "variable_in_memory"

    # инструкции без аргумента
    LOAD = "load"
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

    # инструкции, которые не отображаются в память
    VARIABLE = "variable"
    DEFINE_FUNC = "define_func"
    THEN = "then"
    BEGIN = "begin"

    # инструкции с аргументом
    LOAD_IMM = "loadimm"
    LOAD_ADDR = "loadaddr"
    SAVE = "save"
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
    """Описание выражения из исходного текста программы.
    """


# Словарь соответствия кодов операций их бинарному представлению
opcode_to_binary = {
    # с 1 или нет?
    Opcode.LOAD: 0x2,      #00000010  
    Opcode.PLUS: 0x4,      #00000100 
    Opcode.MINUS: 0x6,     #00000110 
    Opcode.MULT: 0x8,      #00001000   
    Opcode.DIV: 0x10,      #00001010  
    Opcode.MOD: 0x12,      #00001100 
    Opcode.AND: 0x14,      #00001110 
    Opcode.OR: 0x16,       #00010000  
    Opcode.NOT: 0x18,      #00010010 
    Opcode.EQUAL: 0x20,    #00010100   
    Opcode.LESS: 0x22,     #00010110  
    Opcode.GREATER: 0x24,  #00011000 
    Opcode.HALT: 0x26,     #00011010 
    Opcode.RETURN: 0x28,   #00011100 
    Opcode.SAVE: 0x30,      #00011110

    Opcode.LOAD_IMM: 0x3,  #00000011  
    Opcode.LOAD_ADDR: 0x5, #00000101 
    Opcode.CALL: 0x7,      #00000111 
    Opcode.IF: 0x9,        #00001001   
    Opcode.ELSE: 0x11,     #00001011  
    Opcode.WHILE: 0x13,    #00001101 
    Opcode.REPEAT: 0x15,   #00001111 
}

binary_to_opcode = {binary: opcode for opcode, binary in opcode_to_binary.items()}


def to_bytes(code):
    """Преобразует машинный код в бинарное представление.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 39...32 │ 31                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      аргумент                               │
    └─────────┴─────────────────────────────────────────────────────────────┘
    """
    binary_bytes = bytearray()
    for instr in code:
        if "opcode" in instr:
            opcode_bin = opcode_to_binary[instr["opcode"]]
            binary_bytes.append(opcode_bin)

        if "arg" in instr:
            arg = instr.get("arg", 0)
            binary_bytes.extend(((arg >> 24) & 0xFF, (arg >> 16) & 0xFF, (arg >> 8) & 0xFF, arg & 0xFF))

    return bytes(binary_bytes)


def to_hex(code, variables_map):
    addr_to_var = {addr: name for name, addr in variables_map.items()}
    """Преобразует машинный код в текстовый файл с шестнадцатеричным представлением.

    Формат вывода:
    <address> - <HEXCODE> - <mnemonic>
    """
    binary_code = to_bytes(code)
    result = []
    after_halt = False

    i = 0
    while i < len(binary_code):
        has_argument = (binary_code[i]) & 0x1 == 1

        if has_argument  & (not after_halt) & i + 5 >= len(binary_code):
            break

        address = i
        if after_halt:
            word = (binary_code[i] << 24) | (binary_code[i+1] << 16) | (binary_code[i+2] << 8) | binary_code[i + 3]
            mnemonic = addr_to_var[address]
            i += 4
        else:
            mnemonic = binary_to_opcode[binary_code[address]].value
            if binary_to_opcode[binary_code[address]] == Opcode.HALT:
                after_halt = True
            if has_argument:
                word = (binary_code[i] << 32) | (binary_code[i+1] << 24) | (binary_code[i+2] << 16) | (binary_code[i+3] << 8) | binary_code[i + 4]
                arg = (binary_code[i+1] << 24) | (binary_code[i+2] << 16) | (binary_code[i+3] << 8) | binary_code[i + 4]
                i += 5
            else:
                word = binary_code[i]
                i += 1

        # Формируем строку в требуемом формате
        hex_word = f"{word:10X}" # количество символов в строке
        if has_argument:
            line = f"{hex(address)} - {hex_word} - {mnemonic} ({arg:08X})"
        else:
            line = f"{hex(address)} - {hex_word} - {mnemonic}"
        result.append(line)

    return "\n".join(result)


def from_bytes(binary_code):
    # пока не поняла для чего эта функция
    # как будто она нам и не нужна
    """Преобразует бинарное представление машинного кода в структурированный формат.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 39...32 │ 31                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      аргумент                               │
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

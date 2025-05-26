#!/usr/bin/python3
import os
import sys

from isa import Opcode

from enum import Enum


class Signal(str, Enum):
    """Управляющие сигналы процессора."""

    LPC = "lpc"  # Загрузка PC
    MUXPC = "muxpc"  # Выбор источника для PC
    LCR = "lcr"  # Загрузка CR (регистра команд)
    LIR = "lir"  # Загрузка IR (регистра инструкций)
    LBR = "lbr"  # Загрузка BR (регистра ветвления)

    MUXALU = "muxalu"  # Выбор источника для ALU (2 бита)
    ALU = "alu"  # Операция ALU (4 бита)
    LDR = "ldr"  # Загрузка DR (регистра данных)
    LAC = "lac"  # Загрузка AC (аккумулятора)

    MUXRSP = "muxrsp"  # Выбор источника для RSP
    MUXDSP = "muxdsp"  # Выбор источника для DSP
    LRSP = "lrsp"  # Загрузка RSP (указателя стека)
    LDSP = "ldsp"  # Загрузка DSP (указателя стека)
    MUXAR = "muxar"  # Выбор источника для AR
    LAR = "lar"  # Загрузка AR (регистра адреса)
    OE = "oe"  # Разрешение чтения из памяти
    WR = "wr"  # Разрешение записи в память

    MPC = "mpc"  # Загрузка MPC (счетчика микрокоманд)
    MUXMPC = "muxmpc"  # Выбор источника для MPC (2 бита)

    def __str__(self):
        """Возвращает строковое значение сигнала."""
        return str(self.value)

microcode = {
    Opcode.LOAD_IMM: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 1, Signal.MUXALU: 2, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.LOAD_ADDR: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 1, Signal.LIR: 0,
            Signal.LBR: 1, Signal.MUXALU: 2, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 0, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 1,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 1, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 3, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.CALL: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 1, Signal.MUXALU: 1, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 1, Signal.LAR: 1, Signal.MUXRSP: 1,
            Signal.LRSP: 1, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 1, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.RETURN: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 1, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 1, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 1,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 1, Signal.LIR: 0,
            Signal.LBR: 1, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 1, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.LOAD: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 1,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 1, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 3, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.SAVE: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 3, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.PLUS: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 1, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.MINUS: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 2, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.MULT: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 3, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.DIV: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 4, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.MOD: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 5, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.AND: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 6, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.OR: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 7, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.NOT: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 8, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.POP_AC: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 1, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 1,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 1, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 3, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 1, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.POP_DR: [
        {
            Signal.LPC: 1, Signal.MUXPC: 2, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 1, Signal.LDSP: 1, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 2, Signal.LAR: 1, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 1,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 1, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 3, Signal.ALU: 0, Signal.LDR: 1,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 0
        },
    ],
    Opcode.HALT: [
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0,
            Signal.LBR: 0, Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0,
            Signal.LAC: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXRSP: 0,
            Signal.LRSP: 0, Signal.MUXDSP: 0, Signal.LDSP: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 0, Signal.MUXMPC: 0
        },
    ],
}



SIGNAL_ORDER = [
    Signal.LPC,
    Signal.MUXPC,
    Signal.LCR,
    Signal.LIR,
    Signal.LBR,
    Signal.MUXALU,
    Signal.ALU,
    Signal.LDR,
    Signal.LAC,
    Signal.MUXAR,
    Signal.LAR,
    Signal.MUXRSP,
    Signal.LRSP,
    Signal.MUXDSP,
    Signal.LDSP,
    Signal.OE,
    Signal.WR,
    Signal.MPC,
    Signal.MUXMPC,
]

INSTRUCTION_ORDER = [
    Opcode.LOAD_IMM,
    Opcode.LOAD_ADDR,
    Opcode.CALL,
    Opcode.RETURN,
    Opcode.LOAD,
    Opcode.SAVE,
    Opcode.PLUS,
    Opcode.MINUS,
    Opcode.MULT,
    Opcode.DIV,
    Opcode.MOD,
    Opcode.AND,
    Opcode.OR,
    Opcode.NOT,
    Opcode.POP_AC,
    Opcode.POP_DR,
    Opcode.HALT,
]


linking_table = {
    Opcode.LOAD_IMM: 4,
    Opcode.LOAD_ADDR: 8,
    Opcode.CALL: 16,
    Opcode.RETURN: 24,
    Opcode.LOAD: 40,
    Opcode.SAVE: 48,
    Opcode.PLUS: 52,
    Opcode.MINUS: 56,
    Opcode.MULT: 60,
    Opcode.DIV: 64,
    Opcode.MOD: 68,
    Opcode.AND: 72,
    Opcode.OR: 76,
    Opcode.NOT: 80,
    Opcode.POP_AC: 84,
    Opcode.POP_DR: 96,
    Opcode.HALT: 108,
}


def encode_microinstruction(step: dict) -> int:
    """
    Кодирует один шаг микрокода в 26-битное целое число.
    muxalu — 2 бита, alu — 4 бита, muxmpc - 2 бита, muxar - 2 бита остальные сигналы 1 бит
    """
    bitstr = ""
    for name in SIGNAL_ORDER:
        val = step.get(name, 0)
        if (name == Signal.MUXALU) or (name == Signal.MUXMPC) or (name == Signal.MUXAR) or (name == Signal.MUXPC):
            bitstr += f"{val:02b}"
        elif name == Signal.ALU:
            bitstr += f"{val:04b}"
        else:
            bitstr += f"{val:01b}"
    print(bitstr)
    return int(bitstr, 2)


# попозже добавить автоматическое создание таблицы линковки
def save_to_bin(microcode: dict, filename: str):
    os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
    choose_op_instr = "11111000000000000000000110"
    steps = [int(choose_op_instr, 2)]
    address = 4
    for opcode in INSTRUCTION_ORDER:
        # Проверяем тип значения - список или словарь
        print(opcode, address)
        op_steps = microcode[opcode]
        for step in op_steps:
            encoded = encode_microinstruction(step)
            steps.append(encoded)
            address += 4

    binary_bytes = bytearray()

    with open(filename, "wb") as f:
        for code in steps:
            # Сохраняем как 4 байта (24 бита)
            binary_bytes.extend(code.to_bytes(4, byteorder="big"))
        f.write(bytes(binary_bytes))

    print(f"Saved {len(steps)} microinstructions to {filename}")


def microcode_from_byte(target):
    # одна инструкция 4 байта
    with open(target, "rb") as f:
        byte_array = list(f.read())
    return byte_array


if __name__ == "__main__":
    assert (
        len(sys.argv) == 2
    ), "Wrong arguments: translator.py <input_file> <target_file>"
    _, target = sys.argv
    save_to_bin(microcode, target)

# уже в глазах двоится, проверю правильность заполнения позже
# одна микроинструкция - 24 бита, значит mpc увеличивается на 3 каждый раз
# также нужно добавить нулевую инструкцию - цикл выборки команды
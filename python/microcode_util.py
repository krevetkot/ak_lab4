#!/usr/bin/python3
import os
import sys

from isa import Opcode

from enum import Enum

class Signal(str, Enum):
    """Управляющие сигналы процессора."""
    LPC = "lpc"          # Загрузка PC
    MUXPC = "muxpc"      # Выбор источника для PC
    LCR = "lcr"          # Загрузка CR (регистра команд)
    LIR = "lir"          # Загрузка IR (регистра инструкций)
    LBR = "lbr"          # Загрузка BR (регистра ветвления)

    MUXALU = "muxalu"    # Выбор источника для ALU (2 бита)
    ALU = "alu"          # Операция ALU (4 бита)
    LDR = "ldr"          # Загрузка DR (регистра данных)
    LAC = "lac"          # Загрузка AC (аккумулятора)

    MUXSP = "muxsp"      # Выбор источника для SP
    LSP = "lsp"          # Загрузка SP (указателя стека)
    MUXAR = "muxar"      # Выбор источника для AR
    LAR = "lar"          # Загрузка AR (регистра адреса)
    MUXMEM = "muxmem"    # Выбор источника для памяти
    OE = "oe"            # Разрешение чтения из памяти
    WR = "wr"            # Разрешение записи в память
    
    MPC = "mpc"          # Загрузка MPC (счетчика микрокоманд)
    MUXMPC = "muxmpc"    # Выбор источника для MPC (2 бита)

    def __str__(self):
        """Возвращает строковое значение сигнала."""
        return str(self.value)


# Обновленный порядок сигналов с использованием enum
SIGNAL_ORDER = [
    Signal.LPC, Signal.MUXPC, Signal.LCR, Signal.LIR, Signal.LBR,
    Signal.MUXALU, Signal.ALU, Signal.LDR, Signal.LAC,
    Signal.MUXSP, Signal.LSP, Signal.MUXAR, Signal.LAR,
    Signal.MUXMEM, Signal.OE, Signal.WR, Signal.MPC, Signal.MUXMPC
]

microcode = {
    Opcode.LOAD_IMM: {
        Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 1,
        Signal.MUXALU: 2, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
        Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
        Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
    },
    Opcode.LOAD_ADDR: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 1,
            Signal.MUXALU: 2, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 1, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 1, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 3, Signal.ALU: 0, Signal.LDR: 0, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.CALL: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 1, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 3, Signal.LDR: 0, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0, Signal.LAC: 0, Signal.MUXSP: 1,
            Signal.LSP: 1, Signal.MUXAR: 1, Signal.LAR: 1, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.RETURN: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0, Signal.LAC: 0, Signal.MUXSP: 1,
            Signal.LSP: 1, Signal.MUXAR: 1, Signal.LAR: 1, Signal.MUXMEM: 0, Signal.OE: 1,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.LOAD: {
        Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
        Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0, Signal.LAC: 0, Signal.MUXSP: 0,
        Signal.LSP: 0, Signal.MUXAR: 1, Signal.LAR: 1, Signal.MUXMEM: 0, Signal.OE: 1,
        Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
    },
    Opcode.SAVE: {
        Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
        Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 0, Signal.LAC: 0, Signal.MUXSP: 0,
        Signal.LSP: 0, Signal.MUXAR: 1, Signal.LAR: 1, Signal.MUXMEM: 0, Signal.OE: 0,
        Signal.WR: 1, Signal.MPC: 1, Signal.MUXMPC: 1
    },
    Opcode.PLUS: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 1, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.MINUS: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 2, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.MULT: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 3, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.DIV: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 4, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.MOD: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 5, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.AND: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 6, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.OR: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 7, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ],
    Opcode.NOT: [
        {
            Signal.LPC: 1, Signal.MUXPC: 1, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 0, Signal.LDR: 1, Signal.LAC: 0, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        },
        {
            Signal.LPC: 0, Signal.MUXPC: 0, Signal.LCR: 0, Signal.LIR: 0, Signal.LBR: 0,
            Signal.MUXALU: 0, Signal.ALU: 8, Signal.LDR: 1, Signal.LAC: 1, Signal.MUXSP: 0,
            Signal.LSP: 0, Signal.MUXAR: 0, Signal.LAR: 0, Signal.MUXMEM: 0, Signal.OE: 0,
            Signal.WR: 0, Signal.MPC: 1, Signal.MUXMPC: 1
        }
    ]
}

linking_table = {
    Opcode.LOAD_IMM: 3,
    Opcode.LOAD_ADDR: 6,
    Opcode.CALL: 12,
    Opcode.RETURN: 18,
    Opcode.LOAD: 24,
    Opcode.SAVE: 30,
    Opcode.PLUS: 33,
    Opcode.MINUS: 39,
    Opcode.MULT: 45,
    Opcode.DIV: 51,
    Opcode.MOD: 57,
    Opcode.AND: 63,
    Opcode.OR: 69,
    Opcode.NOT: 75,
}

# # Определение порядка управляющих сигналов
# SIGNAL_ORDER = [
#     "lpc", "muxpc", "lcr", "lir", "lbr", "muxalu", "alu", "ldr", "lac",
#     "muxsp", "lsp", "muxar", "lar", "muxmem", "oe", "wr", "mpc", "muxmpc"
# ]

def encode_microinstruction(step: dict) -> int:
    """
    Кодирует один шаг микрокода в 24-битное целое число.
    muxalu — 2 бита, alu — 4 бита, muxmpc - 2 бита, остальные сигналы 1 бит
    Остальные сигналы — 1 бит.
    """
    bitstr = ""
    for name in SIGNAL_ORDER:
        val = step.get(name, 0)
        if name == Signal.MUXALU:
            bitstr += f"{val:02b}"
        elif name == Signal.ALU:
            bitstr += f"{val:04b}"
        if name == Signal.MUXMPC:
            bitstr += f"{val:02b}"
        else:
            bitstr += f"{val:01b}"
    print(bitstr)
    return int(bitstr, 2)

def save_to_bin(microcode: dict, filename: str):
    os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
    steps = []
    for opcode in microcode:
        # Проверяем тип значения - список или словарь
        op_steps = microcode[opcode]
        if isinstance(op_steps, dict):
            # Если это словарь, добавляем его как один шаг
            encoded = encode_microinstruction(op_steps)
            steps.append(encoded)
        else:
            # Если это список, добавляем все шаги
            for step in op_steps:
                encoded = encode_microinstruction(step)
                steps.append(encoded)

    with open(filename, "wb") as f:
        for code in steps:
            # Сохраняем как 3 байта (24 бита)
            f.write(code.to_bytes(3, byteorder='big'))

    print(f"Saved {len(steps)} microinstructions to {filename}")



def microcode_from_byte(target):
    # одна инструкция 3 байта
    with open(target, 'rb') as f:
        byte_array = list(f.read())
    return byte_array


if __name__ == "__main__":
    assert len(sys.argv) == 2, "Wrong arguments: translator.py <input_file> <target_file>"
    _, target = sys.argv
    save_to_bin(microcode, target)

# уже в глазах двоится, проверю правильность заполнения позже
# одна микроинструкция - 24 бита, значит mpc увеличивается на 3 каждый раз
# также нужно добавить нулевую инструкцию - цикл выборки команды
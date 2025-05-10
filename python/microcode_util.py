#!/usr/bin/python3
import os
import sys

from isa import Opcode

microcode = {
        Opcode.LOAD_IMM: {
            "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 1,
            "muxalu": 2, "alu": 0, "ldr": 1, "lac": 1, "muxsp": 0,
            "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
            "wr": 0, "mpc": 1, "muxmpc": 1
        },
        Opcode.LOAD_ADDR: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 1,
                "muxalu": 2, "alu": 0, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 1, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 1, "lir": 0, "lbr": 0,
                "muxalu": 3, "alu": 0, "ldr": 0, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.CALL: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 1, "lbr": 0,
                "muxalu": 0, "alu": 3, "ldr": 0, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 0, "lac": 0, "muxsp": 1,
                "lsp": 1, "muxar": 1, "lar": 1, "muxmem": 0, "oe": 0,
                "wr": 1, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.RETURN: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 0, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 0, "lac": 0, "muxsp": 1,
                "lsp": 1, "muxar": 1, "lar": 1, "muxmem": 0, "oe": 1,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.LOAD: {
            "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
            "muxalu": 0, "alu": 0, "ldr": 0, "lac": 0, "muxsp": 0,
            "lsp": 0, "muxar": 1, "lar": 1, "muxmem": 0, "oe": 1,
            "wr": 0, "mpc": 1, "muxmpc": 1
        },
        Opcode.SAVE: {
            "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
            "muxalu": 0, "alu": 0, "ldr": 0, "lac": 0, "muxsp": 0,
            "lsp": 0, "muxar": 1, "lar": 1, "muxmem": 0, "oe": 0,
            "wr": 1, "mpc": 1, "muxmpc": 1
        },
        Opcode.PLUS: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 1, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.MINUS: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 2, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.MULT: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 3, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.DIV: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 4, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.MOD: [
            {
            "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
            "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
            "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
            "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 5, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.AND: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 6, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.OR: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 7, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ],
        Opcode.NOT: [
            {
                "lpc": 1, "muxpc": 1, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 0, "ldr": 1, "lac": 0, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            },
            {
                "lpc": 0, "muxpc": 0, "lcr": 0, "lir": 0, "lbr": 0,
                "muxalu": 0, "alu": 8, "ldr": 1, "lac": 1, "muxsp": 0,
                "lsp": 0, "muxar": 0, "lar": 0, "muxmem": 0, "oe": 0,
                "wr": 0, "mpc": 1, "muxmpc": 1
            }
        ]
}

# Определение порядка управляющих сигналов
SIGNAL_ORDER = [
    "lpc", "muxpc", "lcr", "lir", "lbr", "muxalu", "alu", "ldr", "lac",
    "muxsp", "lsp", "muxar", "lar", "muxmem", "oe", "wr", "mpc", "muxmpc"
]

def encode_microinstruction(step: dict) -> int:
    """
    Кодирует один шаг микрокода в 24-битное целое число.
    muxalu — 2 бита, alu — 4 бита, остальные сигналы 1 бит
    Остальные сигналы — 1 бит.
    """
    bitstr = ""
    for name in SIGNAL_ORDER:
        val = step.get(name, 0)
        if name == "muxalu":
            bitstr += f"{val:02b}"
        elif name == "alu":
            bitstr += f"{val:04b}"
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
    # тут короче я хочу преобразовать бинарный файл в массив с элементом размером 3 байт
    # [0]: [.......]
    # [1]: [.......] и тд
    # далее нужно сделать таблицу линковки. для load_imm - такой адрес, для load - такой и тд
    # это отдельная функция сделает и передаст в simulation
    return 0


if __name__ == "__main__":
    assert len(sys.argv) == 2, "Wrong arguments: translator.py <input_file> <target_file>"
    _, target = sys.argv
    save_to_bin(microcode, target)

# уже в глазах двоится, проверю правильность заполнения позже
# одна микроинструкция - 24 бита, значит mpc увеличивается на 3 каждый раз
# также нужно добавить нулевую инструкцию - цикл выборки команды
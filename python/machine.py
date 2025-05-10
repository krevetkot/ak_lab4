#!/usr/bin/python3
"""Модель процессора, позволяющая выполнить машинный код полученный из программы
на языке Brainfuck.

Модель включает в себя три основных компонента:

- `DataPath` -- работа с памятью данных и вводом-выводом.

- `ControlUnit` -- работа с памятью команд и их интерпретация.

- и набор вспомогательных функций: `simulation`, `main`.
"""

import logging
import sys

from isa import Opcode, from_bytes, opcode_to_binary
from alu import ALU

MEMORY_MAPPED_INPUT_ADDRESS = 128
MEMORY_MAPPED_INPUT_ADDRESS = 132



class DataPath:
    """Тракт данных (пассивный), включая: ввод/вывод, память и арифметику.

    - `signal_latch_data_addr` -- защёлкивание адреса в памяти данных;
    - `signal_latch_acc` -- защёлкивание аккумулятора;
    - `signal_wr` -- запись в память данных;
    - `signal_output` -- вывод в порт.

    Сигнал "исполняется" за один такт. Корректность использования сигналов --
    задача `ControlUnit`.
    """

    data_memory_size = None
    "Размер памяти данных."

    stack_size = None

    data_memory = None
    "Память данных. Инициализируется нулевыми значениями."

    data_address = None
    "чисто для симуляции хранится информация - откуда поступил адрес, иза AR или PC"

    ALU = None

    CR = None

    AC = None

    DR = None

    PC = None

    IR = None

    BR = None

    AR = None

    SP = None

    input_buffer = None
    "Буфер входных данных. Инициализируется входными данными конструктора."

    output_buffer = None
    "Буфер выходных данных."

    def __init__(self, data_memory_size, stack_size, input_buffer):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        assert stack_size > 0, "Stack size should be non-zero"
        self.data_memory_size = data_memory_size
        self.stack_size = stack_size
        self.data_memory = bytearray(data_memory_size)
        self.data_address = 0
        self.PC = 0
        self.AC = 0
        self.SP = data_memory_size
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.AlU = ALU()

    def signal_latch_PC(self, sel):
        if sel == 1:
            self.PC += 4
        elif sel == 0:
            self.PC = self.BR
        self.data_address = self.PC

    def signal_latch_CR(self):
        self.CR = self.data_memory[self.data_address] << 24
        self.CR |= self.data_memory[self.data_address+1] << 16
        self.CR |= self.data_memory[self.data_address+2] << 8
        self.CR |= self.data_memory[self.data_address+3]

    def signal_latch_IR(self):
        self.IR = (self.CR >> 24) & 0xFF

    def signal_latch_BR(self):
        self.BR = (self.CR) & 0xFFFFFF

    def signal_do_ALU(self, mux_sel, operation):
        if mux_sel == 0:
            left = self.DR
        if mux_sel == 1:
            left = self.PC
        if mux_sel == 2:
            left = self.BR
        if mux_sel == 3:
            left = self.CR
        self.ALU.do_ALU(self.AC, left, operation)
    
    def signal_latch_acc(self):
        self.AC = self.ALU.get_result()

    def signal_latch_DR(self):
        self.DR = self.AC

    def signal_latch_AR(self, sel):
        if sel == 0:
            self.AR = self.AC
        elif sel == 1:
            self.AR = self.SP
        self.data_address = self.AR

    def signal_latch_SP(self, sel):
        if sel == 0:
            self.SP -= 4
        elif sel == 1:
            self.SP += 4

    def signal_oe(self):
        self.data_address = self.AR
        assert 0 <= self.data_address < self.data_memory_size, "out of memory: {}".format(self.data_address)

    def signal_wr(self, sel):
        assert 0 <= self.AR < self.data_memory_size, "out of memory: {}".format(self.AR)
        if sel == 0:
            self.data_memory[self.AR] = self.DR
        elif sel == 1:
            self.data_memory[self.AR] = self.AC

    "пока не знаю как примонтировать ячейку памяти на ввод/вывод"


class ControlUnit:
    """Блок управления процессора. Выполняет декодирование инструкций и
    управляет состоянием модели процессора, включая обработку данных (DataPath).
    """

    microprogram = None

    mPC = None

    data_path = None
    "Блок обработки данных."

    _tick = None
    "Текущее модельное время процессора (в тактах). Инициализируется нулём."

    def __init__(self, microprogram, data_path):
        self.microprogram = microprogram
        self.mPC = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def current_tick(self):
        """Текущее модельное время процессора (в тактах)."""
        return self._tick

    def instruction_decoder(self):
        # в control unit при инициализации я загружу таблицу линковки
        # и эта функция будет просто сопоставлять опкод и адрес в памяти микрокоманд
        # если такого адреса нет - возвращать 0 (специально)
        return 0

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        state_repr = "TICK: {:3} PC: {:3}/{} ADDR: {:3} MEM_OUT: {} ACC: {}".format(
            self._tick,
            self.data_path.PC,
            self.data_path.data_address,
            self.data_path.data_memory[self.data_path.data_address],
            self.data_path.AC,
        )

        # instr = self.program[self.data_path.PC]
        # opcode = instr["opcode"]
        # instr_repr = str(opcode)

        # if "arg" in instr:
        #     instr_repr += " {}".format(instr["arg"])

        # instr_hex = f"{opcode_to_binary[opcode] << 28 | (instr.get('arg', 0) & 0x0FFFFFFF):08X}"

        # return "{} \t{} [{}]".format(state_repr, instr_repr, instr_hex)


def simulation(code, input_tokens, data_memory_size, limit):
    """Подготовка модели и запуск симуляции процессора.

    Длительность моделирования ограничена:

    - количеством выполненных тактов (`limit`);

    - количеством данных ввода (`input_tokens`, если ввод используется), через
      исключение `EOFError`;

    - инструкцией `Halt`, через исключение `StopIteration`.
    """
    data_path = DataPath(data_memory_size, input_tokens)
    control_unit = ControlUnit(code, data_path)

    logging.debug("%s", control_unit)
    try:
        while control_unit._tick < limit:
            control_unit.process_next_tick()
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit._tick >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), control_unit.current_tick()


def main(code_file, input_file):
    """Функция запуска модели процессора. Параметры -- имена файлов с машинным
    кодом и с входными данными для симуляции.
    """
    with open(code_file, "rb") as file:
        binary_code = file.read()
    code = from_bytes(binary_code)
    # у меня переменная длина инструкций, мне это не надо

    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output, ticks = simulation(
        code,
        input_tokens=input_token,
        data_memory_size=100,
        limit=2000,
    )

    print("".join(output))
    print("ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)

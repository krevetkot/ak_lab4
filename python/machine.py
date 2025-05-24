#!/usr/bin/python3
"""Модель процессора, позволяющая выполнить машинный код полученный из программы
на языке Brainfuck.

Модель включает в себя три основных компонента:

- `DataPath` -- работа с памятью и вводом-выводом.

- `ControlUnit` -- работа с памятью микрокоманд, интерпретация микрокоманд.

- и набор вспомогательных функций: `simulation`, `main`.
"""

import logging
import sys

from isa import Opcode, opcode_to_binary, binary_to_opcode, to_hex
from microcode_util import microcode_from_byte, linking_table, SIGNAL_ORDER, Signal
from alu import ALU


# хочется конечно их на 0 и 4
MEMORY_MAPPED_INPUT_ADDRESS = 128
MEMORY_MAPPED_INPUT_ADDRESS = 132


class DataPath:
    """Тракт данных (пассивный), включая: ввод/вывод, память и арифметику.

    - `signal_latch_data_addr` -- защёлкивание адреса в памяти данных;
    - `signal_latch_acc` -- защёлкивание аккумулятора;
    - `signal_Signal.WR` -- запись в память данных;
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

    def __init__(self, code, data_memory_size, stack_size, input_buffer):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        assert stack_size > 0, "Stack size should be non-zero"
        self.data_memory_size = data_memory_size
        self.stack_size = stack_size
        self.data_memory = code
        self.data_address = 0
        self.CR = 0
        self.AC = 0
        self.DR = 0
        self.PC = 0
        self.IR = 0
        self.BR = 0
        self.AR = 0
        self.SP = data_memory_size
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.ALU = ALU()

    def signal_latch_PC(self, sel):
        if sel == 1:
            self.PC += 4
        elif sel == 0:
            self.PC = self.BR
        self.data_address = self.PC

    def signal_latch_CR(self):
        self.CR = self.data_memory[self.data_address] << 24
        print(self.data_memory[self.data_address])
        self.CR |= self.data_memory[self.data_address + 1] << 16
        self.CR |= self.data_memory[self.data_address + 2] << 8
        self.CR |= self.data_memory[self.data_address + 3]

    def signal_latch_IR(self):
        self.IR = (self.CR >> 24) & 0xFF

    def signal_latch_BR(self):
        self.BR = (self.CR) & 0xFFFFFF

    def signal_do_alu(self, mux_sel, operation):
        if mux_sel == 0:
            left = self.DR
        if mux_sel == 1:
            left = self.PC
        if mux_sel == 2:
            left = self.BR
        if mux_sel == 3:
            left = self.CR
        self.ALU.do_ALU(self.AC, left, operation)

    def signal_latch_AC(self):
        self.AC = self.ALU.get_result()

    def signal_latch_DR(self):
        self.DR = self.AC

    def signal_latch_AR(self, sel):
        if sel == 0:
            self.AR = self.AC & 0xFFFFFF
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
        assert (
            0 <= self.data_address < self.data_memory_size
        ), "out of memory: {}".format(self.data_address)

    def signal_wr(self, sel):
        assert 0 <= self.AR < self.data_memory_size, "out of memory: {}".format(self.AR)
        if sel == 0:
            self.data_memory[self.AR] = self.DR
        elif sel == 1:
            self.data_memory[self.AR] = self.AC

    # пока не знаю как примонтировать ячейку памяти на ввод/вывод


class ControlUnit:
    """Блок управления процессора. Выполняет декодирование инструкций и
    управляет состоянием модели процессора, включая обработку данных (DataPath).
    """

    microprogram = None

    mpc = None

    data_path = None
    "Блок обработки данных."

    _tick = None
    "Текущее модельное время процессора (в тактах). Инициализируется нулём."

    def __init__(self, microprogram, data_path):
        self.microprogram = microprogram
        self.mpc = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def signal_latch_mpc(self, sel):
        if sel == 0:
            self.mpc = 0
        if sel == 1:
            self.mpc += 3
        if sel == 2:
            self.mpc = self.instruction_decoder()

    def current_tick(self):
        """Текущее модельное время процессора (в тактах)."""
        return self._tick

    def instruction_decoder(self):
        opcode = self.data_path.IR
        if opcode in linking_table:
            return linking_table[opcode]
        return 0

    def parse_microinstr(self, instr):
        signals = {}

        pos = 22

        for name in SIGNAL_ORDER:
            if name == Signal.MUXALU:
                # 2 бита для Signal.MUXSignal.ALU
                signals[name] = (instr >> pos) & 0b11
                pos -= 2
            elif name == Signal.ALU:
                # 4 бита для Signal.ALU
                signals[name] = (instr >> pos) & 0b1111
                pos -= 4
            elif name == Signal.MUXMPC:
                # 2 бита для Signal.MUXMPC
                signals[name] = (instr) & 0b11
                pos -= 2
            else:
                # 1 бит для остальных сигналов
                signals[name] = (instr >> pos) & 0b1
                pos -= 1

        return signals

    def process_next_tick(self):
        micro_instr = (
            (self.microprogram[self.mpc] << 16)
            | (self.microprogram[self.mpc + 1] << 8)
            | (self.microprogram[self.mpc + 2])
        )
        signals = self.parse_microinstr(micro_instr)
        if signals[Signal.LCR] == 1:
            self.data_path.signal_latch_CR()
        if signals[Signal.LPC] == 1:
            self.data_path.signal_latch_PC(signals[Signal.MUXPC])
        if signals[Signal.LIR] == 1:
            self.data_path.signal_latch_IR()
        if signals[Signal.LBR] == 1:
            self.data_path.signal_latch_BR()
        self.data_path.signal_do_alu(
            signals[Signal.MUXALU], signals[Signal.ALU]
        )
        if signals[Signal.LDR] == 1:
            self.data_path.signal_latch_DR()
        if signals[Signal.LAC] == 1:
            self.data_path.signal_latch_AC()
        if signals[Signal.LSP] == 1:
            self.data_path.signal_latch_SP(signals[Signal.MUXSP])
        if signals[Signal.LAR] == 1:
            self.data_path.signal_latch_AR(signals[Signal.MUXAR])
        if signals[Signal.OE] == 1:
            self.data_path.signal_latch_oe(signals[Signal.MUXSP])
        if signals[Signal.WR] == 1:
            self.data_path.signal_latch_wr(signals[Signal.MUXMEM])

        if signals[Signal.MPC] == 1:
            self.signal_latch_mpc(signals[Signal.MUXMPC])
        else:
            raise StopIteration()

        self._tick()

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        state_repr = "TICK: {:3} PC: {:3} ADDR: {:3} MEM_OUT: {} ACC: {} DR: {} CR: {}".format(
            self._tick,
            self.data_path.PC,
            self.data_path.data_address,
            self.data_path.data_memory[self.data_path.data_address],
            self.data_path.AC,
            self.data_path.DR,
            self.data_path.CR 
        )

        # это бинарный код
        index = self.data_path.PC
        instr = self.data_path.code[index]
        opcode = binary_to_opcode[instr]
        instr_repr = str(opcode)
        if (instr & 0x1) == 1:
            arg = ((self.data_path.code[index + 1] << 16)
                | (self.data_path.code[index + 2] << 8)
                | self.data_path.code[index + 3]
            )
            command = {"address": index, "opcode": opcode, "arg": arg}
            instr_repr += " {}".format(arg)
        else:
            command = {"address": index, "opcode": opcode}
        
        instr_hex = to_hex([command])
 

        return "{} \t{} [{}]".format(state_repr, instr_repr, instr_hex)


def simulation(binary_code, microcode, input_tokens, data_memory_size, limit):
    data_path = DataPath(binary_code, data_memory_size, 68, input_tokens)
    control_unit = ControlUnit(microcode, data_path)

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


def main(code_file, microcode_file, input_file):
    """Функция запуска модели процессора. Параметры -- имена файлов с машинным
    кодом и с входными данными для симуляции.
    """
    # файл с бинарным кодом
    with open(code_file, "rb") as file:
        binary_code = file.read()

    binary_code += bytes(68)

    # память микрокоманд
    with open(microcode_file, "rb") as mfile:
        microcode = mfile.read()

    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    # data_mem_size = len(binary_code) * 2
    # if data_mem_size > 2**24 - 1:
    #     data_mem_size = 2**24 - 1
    # пока что так, но потом я хочу перенести ячейки ввода вывода в начало и сделать как выше

    output, ticks = simulation(
        binary_code,
        microcode,
        input_tokens=input_token,
        data_memory_size=200,
        limit=2000,
    )

    print("".join(output))
    print("ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert (
        len(sys.argv) == 3
    ), "Signal.WRong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    microcode_file = "C:\\Users\\User\\VSCode\\ak\\ak_lab4\\python\\microcode.bin"
    main(code_file, microcode_file, input_file)

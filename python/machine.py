#!/usr/bin/python3
"""Модель процессора, позволяющая выполнить машинный код полученный из программы
на языке Brainfuck.

Модель включает в себя три основных компонента:

- `DataPath` -- работа с памятью и вводом-выводом.

- `ControlUnit` -- работа с памятью микрокоманд, интерпретация микрокоманд.

- и набор вспомогательных функций: `simulation`, `main`.
"""

import logging
import struct
import sys

from alu import ALU
from isa import binary_to_opcode, to_hex
from microcode_util import SIGNAL_ORDER, Signal, linking_table
from translator import variables_map

# ура ура
MEMORY_MAPPED_INPUT_ADDRESS = 0
MEMORY_MAPPED_OUTPUT_ADDRESS = 4
MICROCOMAND_SIZE = 27


class DataPath:
    """Тракт данных (пассивный), включая: ввод/вывод, память и арифметику.
    """

    data_memory_size = None
    "Размер памяти данных."

    code_size = None

    data_memory = None
    "Память данных. Инициализируется нулевыми значениями."

    DA = None

    ALU = None

    CR = None

    AC = None

    DR = None

    PC = None

    IR = None

    BR = None

    AR = None

    RSP = None

    DSP = None

    input_buffer = None
    "Буфер входных данных. Инициализируется входными данными конструктора."

    output_buffer = None
    "Буфер выходных данных."

    def __init__(self, code, data_memory_size, code_size, first_exec_instr, input_buffer: list):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.code_size = code_size
        self.data_memory_size = data_memory_size
        self.data_memory = code
        self.CR = 0
        self.AC = 0
        self.DR = 0
        self.PC = first_exec_instr
        self.DA = self.PC
        self.IR = 0
        self.BR = 0
        self.AR = 0
        self.RSP = data_memory_size - 4
        self.DSP = code_size - 4
        # data stack будет расти вверх, а return stack вниз
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.ALU = ALU()

    def signal_latch_PC(self, sel):  # noqa: N802
        if sel == 3:
            self.PC = self.PC
        elif sel == 2:
            self.PC += 1
        elif sel == 1:
            self.PC += 4
        elif sel == 0:
            self.PC = self.BR

    def signal_latch_CR(self):  # noqa: N802
        if self.DA == MEMORY_MAPPED_INPUT_ADDRESS:
            element = self.input_buffer[0]
            if isinstance(element, int):
                num = element
            elif isinstance(element, str) or isinstance(element, chr):
                num = ord(element)

            word = struct.pack(">I", num)  # Упаковываем в 4 байта (big-endian)
            self.input_buffer.pop(0)
            self.CR = (word[0] << 24) | (word[1] << 16) | (word[2] << 8) | (word[3])

        else:
            self.CR = (
                (self.data_memory[self.DA] << 24)
                | (self.data_memory[self.DA + 1] << 16)
                | (self.data_memory[self.DA + 2] << 8)
                | (self.data_memory[self.DA + 3])
            )

    def signal_latch_IR(self):  # noqa: N802
        self.IR = (self.CR >> 24) & 0xFF

    def signal_latch_BR(self):  # noqa: N802
        self.BR = (self.CR) & 0xFFFFFF

    def signal_do_alu(self, mux_sel, operation):
        if mux_sel == 0:
            left = self.DR
        elif mux_sel == 1:
            left = self.PC
        elif mux_sel == 2:
            left = self.BR
        elif mux_sel == 3:
            left = self.CR
        if left > 0:
            left = struct.unpack("i", struct.pack("I", left))[0]
        self.ALU.do_ALU(self.AC, left, operation)

    def signal_latch_AC(self):  # noqa: N802
        self.AC = self.ALU.get_result()

    def signal_latch_DR(self):  # noqa: N802
        self.DR = self.ALU.get_result()

    def signal_latch_AR(self, sel):  # noqa: N802
        if sel == 0:
            self.AR = self.AC & 0xFFFFFF
        elif sel == 1:
            self.AR = self.RSP
        elif sel == 2:
            self.AR = self.DSP
        else:
            self.AR = self.DR

    def signal_latch_DA(self, sel):  # noqa: N802
        if sel == 0:
            self.DA = self.PC
        elif sel == 1:
            self.DA = self.AR
        assert 0 <= self.DA < self.data_memory_size, "out of memory: {}".format(self.DA)

    def signal_latch_RSP(self, sel):  # noqa: N802
        if sel == 0:
            self.RSP += 4
        elif sel == 1:
            self.RSP -= 4
        assert self.RSP < self.data_memory_size, "out of memory: {}".format(self.RSP)
        assert self.DSP < self.RSP, "stack overflow: {}".format(self.RSP)

    def signal_latch_DSP(self, sel):  # noqa: N802
        if sel == 0:
            self.DSP += 4
        elif sel == 1:
            self.DSP -= 4
        assert self.DSP >= self.code_size - 4, "out of memory: {}".format(self.DSP)
        assert self.DSP < self.RSP, "stack overflow: {}".format(self.DSP)


    def signal_wr(self):
        assert 0 <= self.AR < self.data_memory_size, "out of memory: {}".format(self.AR)
        if self.AR == MEMORY_MAPPED_OUTPUT_ADDRESS:
            self.output_buffer.append(self.AC)
        else:
            self.data_memory[self.AR] = (self.AC >> 24) & 0xFF
            self.data_memory[self.AR + 1] = (self.AC >> 16) & 0xFF
            self.data_memory[self.AR + 2] = (self.AC >> 8) & 0xFF
            self.data_memory[self.AR + 3] = (self.AC) & 0xFF



class ControlUnit:
    """Блок управления процессора. Выполняет декодирование инструкций и
    управляет состоянием модели процессора, включая обработку данных (DataPath).
    """

    stack = [0, 0, 0, 0, 0]  # noqa: RUF012

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
            self.mpc += 4
        if sel == 2:
            self.mpc = self.instruction_decoder()

    def current_tick(self):
        """Текущее модельное время процессора (в тактах)."""
        return self._tick

    def instruction_decoder(self):
        opcode = binary_to_opcode[self.data_path.IR]
        if opcode in linking_table:
            return linking_table[opcode]
        return 0

    def parse_microinstr(self, instr):
        signals = {}

        pos = MICROCOMAND_SIZE

        for name in SIGNAL_ORDER:
            if (name == Signal.MUXALU) or (name == Signal.MUXAR) or (name == Signal.MUXPC):
                # 2 бита для Signal.MUXALU
                pos -= 2
                signals[name] = (instr >> pos) & 0b11
            elif name == Signal.ALU:
                # 4 бита для Signal.ALU
                pos -= 4
                signals[name] = (instr >> pos) & 0b1111
            elif name == Signal.MUXMPC:
                pos -= 2
                signals[name] = (instr) & 0b11
            else:
                pos -= 1
                # 1 бит для остальных сигналов
                signals[name] = (instr >> pos) & 0b1

        return signals

    def process_next_tick(self):  # noqa: C901
        micro_instr = (
            (self.microprogram[self.mpc] << 24)
            | (self.microprogram[self.mpc + 1] << 16)
            | (self.microprogram[self.mpc + 2] << 8)
            | (self.microprogram[self.mpc + 3])
        )
        signals = self.parse_microinstr(micro_instr)

        # по сути oe и lcr всегда равны
        PC_sel = signals[Signal.MUXPC]  # noqa: N806
        if signals[Signal.SIGNIF] == 1:
            PC_sel = 1 - self.data_path.ALU.z  # noqa: N806
            # если z == 0, значит условие ВЫПОЛНИЛОСЬ, и нужно в мультиплексоре выбрать 1 (идти дальше)
            # если z == 1, значит условие НЕ ВЫПОЛНИЛОСЬ, и нужно в мультиплексоре выбрать 0 (перепрыгнуть на else)
        if signals[Signal.MPC] == 0:
            raise StopIteration()

        signal_LDA = signals[Signal.LPC] or signals[Signal.LAR]  # noqa: N806
        if signals[Signal.LCR] == 1:
            self.data_path.signal_latch_CR()
        if signals[Signal.LPC] == 1:
            self.data_path.signal_latch_PC(PC_sel)

        if signals[Signal.LIR] == 1:
            self.data_path.signal_latch_IR()
        if signals[Signal.LBR] == 1:
            self.data_path.signal_latch_BR()

        self.data_path.signal_do_alu(
            signals[Signal.MUXALU], signals[Signal.ALU]
        )  # что подаем на левый вход и какая операция

        if signals[Signal.LDR] == 1:
            self.data_path.signal_latch_DR()
        if signals[Signal.LAC] == 1:
            self.data_path.signal_latch_AC()
        if signals[Signal.LDSP] == 1:
            self.data_path.signal_latch_DSP(signals[Signal.MUXDSP])
        if signals[Signal.LAR] == 1:
            self.data_path.signal_latch_AR(signals[Signal.MUXAR])
        if signal_LDA == 1:
            self.data_path.signal_latch_DA(signals[Signal.LAR])
        if signals[Signal.LRSP] == 1:
            self.data_path.signal_latch_RSP(signals[Signal.MUXRSP])

        # if signals[Signal.OE] == 1:
        #     self.data_path.signal_oe()
        if signals[Signal.WR] == 1:
            self.data_path.signal_wr()

        if signals[Signal.MPC] == 1:
            self.signal_latch_mpc(signals[Signal.MUXMPC])
        else:
            raise StopIteration()

        # print(" ".join(str(x) for x in self.data_path.data_memory[232:240]))
        # aboba = (self.data_path.data_memory[232] << 24) | (self.data_path.data_memory[233] << 16) | (self.data_path.data_memory[234] << 8) | (self.data_path.data_memory[235])
        # print(aboba)
        # aboba = (self.data_path.data_memory[236] << 24) | (self.data_path.data_memory[236+1] << 16) | (self.data_path.data_memory[236+2] << 8) | (self.data_path.data_memory[236+3])
        # print(aboba)
        # self.stack[0] = self.data_path.data_memory[self.data_path.DSP-9]
        # self.stack[1] = self.data_path.data_memory[self.data_path.DSP-5]
        # self.stack[2] = self.data_path.data_memory[self.data_path.DSP-1]
        # self.stack[3] = self.data_path.data_memory[self.data_path.DSP+3]
        # self.stack[4] = self.data_path.data_memory[self.data_path.DSP+7]

        self.tick()

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        state_repr = "TICK: {:3} PC: {:3} DA: {:3} AC: {} DR: {} CR: {} BR: {} RSP: {} DSP: {}".format(
            self._tick,
            self.data_path.PC,
            self.data_path.DA,
            self.data_path.AC,
            self.data_path.DR,
            self.data_path.CR,
            self.data_path.BR,
            self.data_path.RSP,
            self.data_path.DSP,
        )

        # это бинарный код
        index = self.data_path.PC
        instr = self.data_path.data_memory[index]
        opcode = binary_to_opcode[instr]
        instr_repr = str(opcode)
        if (instr & 0x1) == 1:
            arg = (
                (self.data_path.data_memory[index + 1] << 16)
                | (self.data_path.data_memory[index + 2] << 8)
                | self.data_path.data_memory[index + 3]
            )
            command = {"address": index, "opcode": opcode, "arg": arg}
            instr_repr += " {}".format(arg)
        else:
            command = {"address": index, "opcode": opcode}

        instr_hex = to_hex([command], variables_map)

        return "{} {} [{}]".format(state_repr, instr_repr, instr_hex)


def simulation(binary_code, microcode, input_tokens, data_memory_size, code_size, limit):
    first_exec_instr = (binary_code[4] << 24) | (binary_code[5] << 16) | (binary_code[6] << 8) | (binary_code[7])

    data_path = DataPath(binary_code, data_memory_size, code_size, first_exec_instr, input_tokens)
    control_unit = ControlUnit(microcode, data_path)

    prev_pc = -1

    try:
        while control_unit._tick < limit:
            if prev_pc != control_unit.data_path.PC:
                logging.debug("%s", control_unit)
                prev_pc = control_unit.data_path.PC
            control_unit.process_next_tick() 
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit._tick >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", data_path.output_buffer)
    return data_path.output_buffer, control_unit.current_tick()


def main(code_file, input_file, memory_size, symbolic_output_flag):
    """Функция запуска модели процессора. Параметры -- имена файлов с машинным
    кодом и с входными данными для симуляции.
    """

    microcode_file = "C:\\Users\\User\\VSCode\\ak\\ak_lab4\\python\\microcode.bin"

    const_data_memory_size = 1000
    # файл с бинарным кодом
    with open(code_file, "rb") as file:
        bin_code = file.read()

    code_size = len(bin_code)

    bin_code += bytes(const_data_memory_size - code_size)

    binary_code = bytearray(bin_code)

    # память микрокоманд
    with open(microcode_file, "rb") as mfile:
        microcode = mfile.read()

    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        if symbolic_output_flag:
            for char in input_text:
                input_token.append(char)
        elif "," in input_text:
            for el in input_text.split(","):
                input_token.append(int(el))
        input_token.append(0)  # чтобы сделать cstr

    output, ticks = simulation(
        binary_code,
        microcode,
        input_tokens=input_token,
        data_memory_size=memory_size,
        code_size=code_size,
        limit=20000,
    )

    if symbolic_output_flag:
        symbol_output = "".join(chr(code) for code in output)
        print(symbol_output)
    else:
        print(output)

    print("ticks:", ticks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s   machine:simulation    %(message)s",
                        filename="C:\\Users\\User\\VSCode\\ak\\ak_lab4\\python\\machine.log",
                        filemode="w")
    assert len(sys.argv) == 5, "Signal.WRong arguments: machine.py <code_file> <input_file> <memory_size> <symbolic_output_flag>"
    code_file = sys.argv[1]
    input_file = sys.argv[2]
    memory_size = int(sys.argv[3])
    if sys.argv[4] == "True" or sys.argv[4] == "1":
        symbolic_output_flag = True
    else:
        symbolic_output_flag = False

    main(code_file, input_file, memory_size, symbolic_output_flag)

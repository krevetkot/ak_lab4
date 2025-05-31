"""Golden тесты транслятора и машины.
Конфигурационнфе файлы: "golden/*.yml"
"""

import contextlib
import io
import logging
import os
import tempfile

import machine
import pytest
import translator

MAX_LOG = 4000


@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    """
    Вход:

    - `in_source` -- исходный код
    - `in_stdin` -- данные на ввод процессора для симуляции
    - `in_memory_size` -- размер памяти
    - `in_sim_mode` -- режим отображения результата: dec, sym, hex
    - `in_eam` -- режим математики (если True, то расширенный)
    - `in_output_len` -- максимальное количество строк в журнале программы

    Выход:

    - `out_hex` -- аннотированный машинный код
    - `out_binary` -- бинарный файл в base64
    - `out_stdout` -- стандартный вывод транслятора и симулятора
    - `out_log` -- журнал программы
    """
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:root:%(message)s")
    caplog.set_level(logging.DEBUG)

    def get_last_n_lines(text: str, n: int) -> str:
        lines = text.splitlines()
        last_n_lines = lines[-n:] if len(lines) > n else lines
        return "\n".join(last_n_lines)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.forth")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target_{golden.name}.bin")
        target_hex = os.path.join(tmpdirname, "target_{golden.name}.bin.hex")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        memory_size = golden["in_memory_size"]
        in_sim_mode = golden["in_sim_mode"]
        in_eam = golden["in_eam"]
        in_output_len = golden["in_output_len"]

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            print("============================================================")
            machine.main(target, input_stream, memory_size, in_sim_mode, in_eam)

        with open(target, "rb") as file:
            code_bin = file.read()
        with open(target_hex, encoding="utf-8") as file:
            code_hex = file.read()

        assert code_bin == golden.out["out_code_bin"]
        assert code_hex == golden.out["out_code_hex"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert get_last_n_lines(caplog.text, in_output_len) == golden.out["out_log"]

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
    Если вы меняете логику работы приложения -- то запускаете тесты с ключом:
    `cd python && poetry run pytest . -v --update-goldens`

    Вход:

    - `in_source` -- исходный код
    - `in_stdin` -- данные на ввод процессора для симуляции
    - `in_memory_size` -- размер памяти
    - `in_sim_mode` -- режим отображения результата: dec, sym, hex
    - `in_eam` -- режим математики (если True, то расширенный)

    Выход:

    - `out_hex` -- аннотированный машинный код
    - `out_binary` -- бинарный файл в base64
    - `out_stdout` -- стандартный вывод транслятора и симулятора
    - `out_log` -- журнал программы
    """
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:root:%(message)s")
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.bf")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.bin")
        target_hex = os.path.join(tmpdirname, "target.bin.hex")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        memory_size = golden["in_memory_size"]
        in_sim_mode = golden["in_sim_mode"]
        in_eam = golden["in_eam"]

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            print("============================================================")
            machine.main(target, input_stream, memory_size, in_sim_mode, in_eam)

        with open(target_hex, encoding="utf-8") as file:
            code_hex = file.read()

        assert code_hex == golden.out["out_code_hex"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"] + "\n"

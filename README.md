# AccForth. Транслятор и модель процессора

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [AccForth. Транслятор и модель процессора](#accforth-транслятор-и-модель-процессора)
  * [Язык программирования](#язык-программирования)     
    + [Синтаксис](#синтаксис)
    + [Семантика](#семантика)
  * [Организация памяти](#организация-памяти)
  * [Система команд](#система-команд)
    + [Особенности процессора](#особенности-процессора)
    + [Набор инструкций](#набор-инструкций)
    + [Кодирование инструкций](#кодирование-инструкций)
  * [Транслятор](#транслятор)
  * [Модель процессора](#модель-процессора)
    + [DataPath](#datapath)
    + [ControlUnit](#controlunit)
    + [Особенности работы модели](#особенности-работы-модели)

<!-- markdown-toc end -->

---

- `forth | acc | neum | mc | tick | binary | stream | mem | cstr | prob2 | superscalar`

## Язык программирования

### Синтаксис

``` ebnf
program ::= terms

terms ::= term
        | term terms

term ::= word
       | number
       | string
       | comment
       | ":" terms ";"
       | "IF" terms "ELSE" terms "THEN"
       | "BEGIN" terms "WHILE" terms "REPEAT"

word ::= <последовательность печатных символов, кроме пробелов>

number ::= <целое число>

string ::= S" <любые символы>"

comment ::= # <любые символы до конца строки>
```

### Семантика
- Стратегия вычислений - стековая.
- Постфиксная запись (обратная польская нотация).
- Стек данных и аккумулятор — основные механизмы передачи аргументов между функциями.
- Стек возвратов — хранит адреса возврата для управления потоком выполнения.
- Сначала код полностью транслируется, потом последовательно выполняется.
- Область видимости: все переменные и все функции доступны везде, с условием, что переменные и функции объявлены до исполняемого кода.
- Типизация слабая. Термом S" <последовательность_символов>" объявляются строки, любое число определяется как знаковое. Строки, записанные не в указанном формате, трактуются как названия переменных или функций. Число может быть записано в десятичном или шестнадцатиричном формате. 

## Организация памяти

Модель памяти процессора:

Память команд и данных общая (архитектура фон Неймана). Память разделена на разделы:
- функции (если они есть);
- исполняемый код;
- сохраненные переменные - статические данные;
- стек данных (растет "вверх") - динамические данные;
- стек возврата (растет "вниз" от последней ячейки памяти).

Регистры:
- PC -- program counter. Хранит указатель на ячейку с исполняемой командой. 3 байта.
- CR -- command register. Хранит исполняемую команду. 4 байта.
- IR -- instruction register. Хранит опкод исполняемой команды. 1 байт.
- BR -- buffer register. Хранит аргумент исполняемой команды. 3 байта.
- AC -- accumulator. Регистр общего назначения, из него записываются данные в память.
- DR -- data register. Хранит либо второй операнд для операции, либо адрес, по которому нужно сохранить значение из AC.
- AR -- address register. Хранит либо указатель на один из стеков, либо адрес из AC/DR.
- DSP -- data stack pointer. Хранит указатель на последнюю заполненную ячейку стека данных.
- RSP -- return stack pointer. Хранит указатель на последнюю заполненную ячейку стека возврата.
- DA -- data address. Хранит адрес, по которому мы обращаемся в память (либо из PC, либо из AR).
- mPC -- micro program counter. Хранит указатель на ячейку с исполняемой микрокомандой.

Размер машинного слова - 32 бита. Адресация только прямая, но с помощью последовательного применения команды LOAD можно добиться косвенной.

Понятия константы не существует, любую переменную можно изменить. Каждому литералу (символу) отведена целая ячейка памяти в 32 бита. Если данные (число или строка) требуют больше, чем 1 машинного слова, они размещаются по порядку в двух и более ячейках. Литерал нельзя положить на стек данных, его можно сохранить только в статическую память.
Функции хранятся там же, где и основной код, но обязательно в начале кода. После трансляции в термы, транслятор определяет адрес команды, идущей за последней командой RETURN, и записывает этот адрес в ячейку памяти под номером 0x4 (она же является memory mapped output). Таким образом, процессор понимает, откуда начинать выполнение.

## Система команд

### Особенности процессора:

- Доступ к памяти данных осуществляется по адресу, хранящемуся в специальном регистре `Data address`. Установка адреса осуществляется несколькими путями: инкрементом, прибавлением 4 или адресом перехода. Прибавление 1 или 4 происходит в зависимости от длины инструкции и управляется из микрокода.
- Обработка данных осуществляется по текущему адресу. Процессор считывает 4 байта из памяти. Даже если текущая инструкция занимает 1 байт, мы никогда не выйдем за пределы памяти, потому что на два стека отведено как минимум 8 байт. Таким образом, ненужные байты заполнятся в регистре CR "мусорными" значениями.
- Из CR опкод попадает в IR, а далее в дешифратор инструкций, где определяется команда и выполняются соответствующие микрокоманды. Дешифратор адреса - таблица, где каждой команде сопоставлен адрес первой микрокоманды. На адресах 0-4 лежат микрокоманды цикла выборки команды, которые запускаются в начале каждой новой инструкции.
- Поток управления:
    - инкремент или увеличение на 4 `PC` после каждой инструкции;
    - условный (`IF`, `WHILE`) и безусловный (`ELSE`, `REPEAT`) переходы.
- Адресация везде прямая.
- Поток ввода-вывода осуществляется через Memory-Mapped IO. 0x0 - ячейка ввода, 0x4 - ячейка вывода.

### Набор инструкций

Существует три типа команд: с аргументом, без аргумента и те, которые не транслируются. Опкод занимает 1 байт, аргумент 3 байта.

Команды с аргументом:
- `LOAD_IMM` -- загружает в аккумулятор число или адрес переменной и кладет его на стек. Синтаксис: "42" или "<имя переменной>". Аргумент: число или адрес переменной.
- `IF` -- команда ветвления. Проверяет значение в аккумуляторе: если -1, выполняет код после IF, если 0, выполняет код после ELSE. Аргумент: адрес первой инструкции после ELSE.
- `ELSE` -- перекидывает выполнение на код после THEN (если мы дошли до ELSE, значит IF было выполнено). Аргумент: адрес первой инструкции после THEN.
- `WHILE` -- команда цикла. Проверяет значение в аккумуляторе: если -1, выполняет код после WHILE, если 0, выполняет код после REPEAT. Аргумент: адрес первой инструкции после REPEAT.
- `REPEAT` -- перекидывает выполнение на код после BEGIN. Аргумент: адрес первой инструкции после BEGIN.


Команды без аргумента:
- `LOAD` -- загружает в аккумулятор значение по адресу в аккумуляторе и кладет его на вершину стека.
- `SAVE` -- сохраняет значение аккумулятора по адресу с вершины стека.
- `POP_AC` -- снимает значение с вершины стека и кладет в аккумулятор.
- `POP_DR` -- снимает значение с вершины стека и кладет в регистр DR.
- `DUP` -- дублирует значение с вершины стека.
- `PLUS` -- складывает значение аккумулятора и значение с вершины стека, результат кладет на стек.
- `MINUS` -- находит разницу между значением аккумулятора и значением с вершины стека, результат кладет на стек.
- `MULT` -- умножает значение аккумулятора и значение с вершины стека, результат кладет на стек.
- `DIV` -- делит значение аккумулятора на значение с вершины стека, результат кладет на стек.
- `MOD` -- делит по модулю значение аккумулятора на значением с вершины стека, результат кладет на стек.
- `AND` -- находит логическое И между значением аккумулятора и значением с вершины стека, результат кладет на стек.
- `OR` -- находит логическое ИЛИ между значением аккумулятора и значением с вершины стека, результат кладет на стек.
- `NOT` -- находит логическое НЕ значения аккумулятора, результат кладет на стек.
- `EQUAL` -- проверяет на равенство значение аккумулятора и значение с вершины стека, результат кладет на стек (-1 - равны, 0 - неравны).
- `LESS` -- проверяет, что значение аккумулятора меньше (знаково), чем значение с вершины стека, результат кладет на стек (-1 - меньше, 0 - не меньше).
- `GREATER` -- проверяет, что значение аккумулятора больше (знаково), чем значение с вершины стека, результат кладет на стек (-1 - больше, 0 - не больше).
- `HALT` -- команда останов.


Команды, которые не транслируются:
- `VARIABLE` -- определяет переменную (добавляет переменную в словарь переменных).
- `DEFINE_FUNC` -- определяет функцию (добавляет функцию в словарь переменных).
- `THEN` -- служит меткой конца кода ELSE.
- `BEGIN` -- служит меткой начала условия для WHILE.

### Кодирование инструкций

Типы данных в модуле [isa](./isa.py), где:

- `Opcode` -- перечисление кодов операций;
- `Term` -- структура для описания значимого фрагмента кода исходной программы.

#### Бинарное представление

Бинарное представление инструкций.

Команда с аргументом:
```text

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 31...24 │ 23                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      аргумент                               │
    └─────────┴─────────────────────────────────────────────────────────────┘
```


Команда без аргумента:
```text

    ┌─────────┐
    │  7...0  │ 
    ├─────────|
    │  опкод  │ 
    └─────────┘
```



Коды операций:

- LOAD: 0x2,  # 00000010
- PLUS: 0x4,  # 00000100
- MINUS: 0x6,  # 00000110
- MULT: 0x8,  # 00001000
- DIV: 0x10,  # 00001010
- MOD: 0x12,  # 00001100
- AND: 0x14,  # 00001110
- OR: 0x16,  # 00010000
- NOT: 0x18,  # 00010010
- EQUAL: 0x20,  # 00010100
- LESS: 0x22,  # 00010110
- GREATER: 0x24,  # 00011000
- HALT: 0x26,  # 00011010
- RETURN: 0x28,  # 00011100
- SAVE: 0x30,  # 00011110
- POP_AC: 0x32,  # 0100000
- POP_DR: 0x34,  # 0100010
- DUP: 0x36,  # 0100100
- LOAD_IMM: 0x3,  # 00000011
- CALL: 0x5,  # 00000101
- IF: 0x7,  # 00000111
- ELSE: 0x9,  # 00001001
- WHILE: 0x11,  # 00001011
- REPEAT: 0x13,  # 00001101

Микрокоманды (одна строка - один такт):
| address | command  | signal_if | latch_PC | MUX_PC(4) | latch_CR | latch_IR | latch_BR | MUX_ALU(4) | ALU(16) |
|---------|----------|-----------|----------|-----------|----------|----------|----------|------------|---------|
| 0       |          | 0         | 1        | 3         | 0        | 0        | 0        | 0          | 0       |
| 4       |          | 0         | 0        | 0         | 1        | 1        | 0        | 0          | 0       |
| 8       | LOAD_IMM | 0         | 1        | 1         | 0        | 0        | 1        | 2          | 0       |
| 12      | LOAD     | 0         | 1        | 2         | 0        | 0        | 0        | 0          | 0       |
| 16      |          | 0         | 0        | 0         | 1        | 0        | 0        | 3          | 0       |
| 20      |          | 0         | 0        | 0         | 0        | 0        | 0        | 0          | 0       |
| 24      | CALL     | 0         | 1        | 1         | 0        | 0        | 1        | 1          | 0       |
| 28      |          | 0         | 1        | 0         | 0        | 0        | 0        | 0          | 0       |
| 32 | RETURN | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| 36 |        | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 40 |        | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| 44 |        | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 48 | SAVE   | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| 52 | PLUS   | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 1 |
| 56 | MINUS  | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 2 |
| 60 | MULT    | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 3  |
| 64 | DIV     | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 4  |
| 68 | MOD     | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 5  |
| 72 | AND     | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 6  |
| 76 | OR      | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 7  |
| 80 | NOT     | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 8  |
| 84 | EQUAL   | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 9  |
| 88 | LESS    | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 10 |
| 92 | GREATER | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 11 |
| 96  | POP_AC | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| 100 |        | 0 | 0 | 0 | 1 | 0 | 0 | 3 | 0 |
| 104 | POP_DR | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| 108 |        | 0 | 0 | 0 | 1 | 0 | 0 | 3 | 0 |
| 112 | DUP    | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| 116 |        | 0 | 0 | 0 | 1 | 0 | 0 | 3 | 0 |
| 120 |        | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 124 | IF     | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 128 |        | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| 132 | ELSE   | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 136 |        | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 140 | WHILE  | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 144 |        | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| 148 | REPEAT | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 152 |        | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 156 | HALT   | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Транслятор

Интерфейс командной строки: `translator.py <input_file> <target_file>`

Реализовано в модуле: [translator](./translator.py)

Этапы трансляции:

1. Трансформирование текста в последовательность значимых термов.
2. Проверка корректности программы (парность квадратных скобок).
3. Удаление токенов, которые не отображаются напрямую в команды, создание таблицы линковки для названий функций и переменных.
4. Подстановка адресов вместо лейблов, вставка адресов переходов (в IF и WHILE)
5. Cохранение переменных после HALT.

Правила генерации машинного кода:
- встречаем число - команда LOAD_IMM.
- встречаем VARIABLE - удаляем предыдущую команду, потому что нам не нужен LOAD_IMM и сохраняем в две специальные таблицы, что нам нужно будет отобразить переменную в память.
- встречаем строку - это либо функция, либо переменная. Если ничего из этих вариантов - ошибка трансляции.
- встречаем команду, которой необходимы два аргумента - добавляем перед ней POP_AC + POP_DR (для SAVE наоборот, так как адрес лежит на стеке сверху).
- встречаем команду, которой необходим один аргумент - добавляем перед ней POP_AC.
- условный блок и блок с циклом обрабатываются по особому: при первом проходе в специальный словарь сохраняются адреса ELSE, THEN, BEGIN, REPEAT, а в команды IF, ELSE, WHILE вместо аргументов ставятся заглушки (-1). При втором проходе вместо заглушек подставляются адреса переходов.
- изменение адреса при каждой итерации тщательно управляется.

## Модель процессора

Интерфейс командной строки: ` machine.py <input_file> <memory_size> <mode> <eam>"`
input_file - адрес файла, выступающего входным буфером;
memory_size - размер памяти (для удобства конфигурации);
mode - режим отображения ответа (sym - символьный, dec - в десятичной сс, hex - в шестнадцатиричной cc);
eam - режим арифметики. 1 - расширенный, 0 - обычный.

Реализовано в модуле: [machine](./machine.py).

### DataPath

[Схема](./datapath.png).

Реализован в классе `DataPath`.

`data_memory` -- однопортовая память, поэтому либо читаем, либо пишем.

Сигналы (обрабатываются за один такт, реализованы в виде методов класса):

Мультиплексоры: 
- MUX_PC -- 2 бита. 0 - значение из BR, 1 - PC+1, 2 - PC+4. Может выставляться с помощью сигнала signal_if (см. далее).
- MUX_ALU -- 2 бита. 0 - из DR, 1 - из PC, 2 - из BR, 3 - из CR.
- MUX_AR -- 2 бита. 0 - из AC, 1 - из RSP, 2 - из DSP, 3 - из DR.
- MUX_RSP -- 1 бит. 0 - RSP+4, 1 - RSP-4.
- MUX_DSP -- 1 бит. 0 - DSP+4, 1 - DSP-4.
- MUX_MEM -- 1 бит. Идентичен сигналу latch_AR.

Сигналы защелкивания:
- latch_PC -- защелкивает значение PC, исходя из сигнала MUX_PC.
- latch_CR -- защелкивает значение CR. 
- latch_IR -- защелкивает значение IR.
- latch_BR -- защелкивает значение BR.
- latch_DR -- защелкивает значение DR.
- latch_AC -- защелкивает значение AC.
- latch_AR -- защелкивает значение AR, исходя из сигнала MUX_AR.
- latch_RSP -- защелкивает значение RSP, исходя из сигнала MUX_RSP.
- latch_DSP -- защелкивает значение DSP, исходя из сигнала MUX_DSP.

Сигнал для АЛУ:
- ALU -- сигнал команды для АЛУ. Пусть left - левый аргумент, right - правый. Тогда:
0      = left + 0        
1      = left + right   
2      = left - right    
3      = left * right    
4      = left // right   
5      = left % right       
6      = left and right  
7      = left or right   
8      = not right       
9      = left == right ? 
10     = left < right ?  
11     = left < right ?   

Другие сигналы:
- signal_if -- если этот сигнал = 1, значит это команда, проверяющая условие (IF, WHILE). Тогда по формуле выставляется сигнал в мультиплексор перед PC: `MUX_PC = 1 - ALU.z`. В аппаратуре это можно сделать с помощью логической схемы.
- oe -- output enable, разрешает чтение из памяти в CR по адресу из DA.
- wr -- write, разрешает запись в память из AC по адресу из DA.

Флаги:
- `n` -- отражает наличие отрицательного значения в аккумуляторе.
- `z` -- отражает наличие нулевого значения в аккумуляторе.
- `v` -- отражает наличие знакового переполнения при последней операции.
- `c` -- отражает наличие беззнакового переполнения при последней операции.

### ControlUnit

[Схема](./control_unit.png).

Реализован в классе `ControlUnit`.

- Microcoded.
- Метод `process_next_tick` моделирует выполнение полного цикла инструкции.

Сигналы:
- MUX_mPC -- 2 бита. 0 - 0, 1 - mpc+4, 1 - из instruction_decoder.
- latch_mPC --  защелкивает значение mPC, исходя из сигнала MUX_mPC.

### Особенности работы модели:

- Цикл симуляции осуществляется в функции `simulation`.
- Шаг моделирования соответствует одной инструкции с выводом состояния в журнал.
- Для журнала состояний процессора используется стандартный модуль `logging`.
- Количество тактов для моделирования лимитировано (20000).
- Остановка моделирования осуществляется при:
    - превышении лимита количества выполняемых инструкций;
    - исключении `EOFError` -- если нет данных для чтения из порта ввода;
    - исключении `StopIteration` -- если выполнена инструкция `HALT`.
- Результат работы (output_buffer) может выводиться в трех режимах (dec, sym, hex), описанных выше.
- АЛУ вынесено в отдельный модуль [alu.py](./alu.py).
- Для создания памяти микрокоманд был создан модуль [microcode_util.py](./microcode_util.py). В нем можно редактировать сигналы. При запуске симуляции запускать его повторно не требуется, он нужен только для сохранения изменений в память имкрокоманд.

## Тестирование

Тестирование выполняется при помощи golden test-ов.

1. Тесты для языка `AccForth` реализованы в: [golden_test.py](./golden_test.py). Конфигурации:
    - [golden/cat.yml](golden/cat.yml)
    - [golden/hello.yml](golden/hello.yml)    
    - [golden/hello_user_name.yml](golden/hello_user_name.yml)
    - [golden/euler.yml](golden/euler.yml)
    - [golden/eam_add.yml](golden/eam_add.yml)
    - [golden/eam_sub.yml](golden/eam_sub.yml)

Запустить тесты: `poetry run pytest . -v`

Обновить конфигурацию golden tests:  `poetry run pytest . -v --update-goldens`

Пример использования транслятора (бинарное и json представление машинного кода):

``` shell
$ cat examples/cat.forth
0x0 VARIABLE input_address
0x4 VARIABLE output_address

BEGIN
input_address @ @ DUP 0 >
WHILE
output_address @ !
REPEAT

HALT
$ ./translator.py examples/cat.forth examples/target.bin
source LoC: 12 code instr: 22
$ cat examples/target.bin.base64
AAAAAAAAAKADAAC9MgIDAADBNDIwAwAAAAMAAMEyAgMAAAAyNCQyEQAAUgMAAMEyAjYDAAABMjQGNgMAAAEyNAYDAADBNDIwMjQEMjQEEwAAGTYyNAgoAwAAvTICAwAAwTQyMAMAAAADAADBMgIDAAAAMjQkMhEAAJ8DAADBMgI2MjQIMjQEAwAAwTICAwAAATI0BgMAAME0MjATAABoKAUAAAgFAABXMjQGAwAAuTICNDIwJgAAAAAAAAAEAAAAZAAAAAE=
$ cat out/target.bin.hex
0x8 -    300002B - loadimm (0000002B)
0xc -         32 - popac
0xd -          2 - load
0xe -         32 - popac
0xf -          2 - load
0x10 -         36 - dup
0x11 -    3000000 - loadimm (00000000)
0x15 -         32 - popac
0x16 -         34 - popdr
0x17 -         24 - greater
0x18 -         32 - popac
0x19 -   1100002A - while (0000002A)
0x1d -    300002F - loadimm (0000002F)
0x21 -         32 - popac
0x22 -          2 - load
0x23 -         34 - popdr
0x24 -         32 - popac
0x25 -         30 - save
0x26 -   13000008 - repeat (00000008)
0x2a -         26 - halt
0x2b -          0 - input_address
0x2f -          4 - output_address
```

Пример использования модели процессора:

``` shell
$ cat examples/input_file.txt
foo
$ ./machine.py examples/target.bin examples/input_file.txt 1000 sym False
DEBUG   machine:simulation    TICK:   0 PC:   8 DA:   8 AC: 0 DR: 0 CR: 0 BR: 0 RSP: 996 DSP: 47 loadimm 43 [0x8 -    300002B - loadimm (0000002B)]
DEBUG   machine:simulation    TICK:   3 PC:  12 DA:  51 AC: 43 DR: 0 CR: 50331691 BR: 43 RSP: 996 DSP: 51 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:   6 PC:  13 DA:  51 AC: 43 DR: 0 CR: 839004674 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK:  10 PC:  14 DA:  43 AC: 43 DR: 0 CR: 36831798 BR: 43 RSP: 996 DSP: 47 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:  15 PC:  15 DA:  51 AC: 0 DR: 0 CR: 839005699 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK:  19 PC:  16 DA:   0 AC: 0 DR: 0 CR: 37094144 BR: 43 RSP: 996 DSP: 47 dup [0x8 -         36 - dup]
DEBUG   machine:simulation    TICK:  24 PC:  17 DA:  51 AC: 102 DR: 0 CR: 906166272 BR: 43 RSP: 996 DSP: 51 loadimm 0 [0x8 -    3000000 - loadimm (00000000)]
DEBUG   machine:simulation    TICK:  29 PC:  21 DA:  59 AC: 0 DR: 0 CR: 50331648 BR: 0 RSP: 996 DSP: 59 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:  32 PC:  22 DA:  59 AC: 0 DR: 0 CR: 842277938 BR: 0 RSP: 996 DSP: 59 popdr [0x8 -         34 - popdr]
DEBUG   machine:simulation    TICK:  36 PC:  23 DA:  55 AC: 0 DR: 0 CR: 874787345 BR: 0 RSP: 996 DSP: 55 greater [0x8 -         24 - greater]
DEBUG   machine:simulation    TICK:  40 PC:  24 DA:  55 AC: -1 DR: 102 CR: 607260928 BR: 0 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:  43 PC:  25 DA:  55 AC: -1 DR: 102 CR: 839974912 BR: 0 RSP: 996 DSP: 55 while 42 [0x8 -   1100002A - while (0000002A)]
DEBUG   machine:simulation    TICK:  48 PC:  29 DA:  29 AC: -1 DR: 102 CR: 285212714 BR: 42 RSP: 996 DSP: 51 loadimm 47 [0x8 -    300002F - loadimm (0000002F)]
DEBUG   machine:simulation    TICK:  51 PC:  33 DA:  55 AC: 47 DR: 102 CR: 50331695 BR: 47 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:  54 PC:  34 DA:  55 AC: 47 DR: 102 CR: 839005234 BR: 47 RSP: 996 DSP: 55 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK:  58 PC:  35 DA:  47 AC: 47 DR: 102 CR: 36975152 BR: 47 RSP: 996 DSP: 51 popdr [0x8 -         34 - popdr]
DEBUG   machine:simulation    TICK:  63 PC:  36 DA:  55 AC: 4 DR: 102 CR: 875704339 BR: 47 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:  67 PC:  37 DA:  51 AC: 4 DR: 4 CR: 842011392 BR: 47 RSP: 996 DSP: 51 save [0x8 -         30 - save]
DEBUG   machine:simulation    TICK:  71 PC:  38 DA:   4 AC: 102 DR: 4 CR: 806551552 BR: 47 RSP: 996 DSP: 47 repeat 8 [0x8 -   13000008 - repeat (00000008)]
DEBUG   machine:simulation    TICK:  75 PC:   8 DA:   8 AC: 102 DR: 4 CR: 318767112 BR: 8 RSP: 996 DSP: 47 loadimm 43 [0x8 -    300002B - loadimm (0000002B)]
DEBUG   machine:simulation    TICK:  78 PC:  12 DA:  51 AC: 43 DR: 4 CR: 50331691 BR: 43 RSP: 996 DSP: 51 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:  81 PC:  13 DA:  51 AC: 43 DR: 4 CR: 839004674 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK:  85 PC:  14 DA:  43 AC: 43 DR: 4 CR: 36831798 BR: 43 RSP: 996 DSP: 47 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK:  90 PC:  15 DA:  51 AC: 0 DR: 4 CR: 839005699 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK:  94 PC:  16 DA:   0 AC: 0 DR: 4 CR: 37094144 BR: 43 RSP: 996 DSP: 47 dup [0x8 -         36 - dup]
DEBUG   machine:simulation    TICK:  99 PC:  17 DA:  51 AC: 111 DR: 4 CR: 906166272 BR: 43 RSP: 996 DSP: 51 loadimm 0 [0x8 -    3000000 - loadimm (00000000)]
DEBUG   machine:simulation    TICK: 104 PC:  21 DA:  59 AC: 0 DR: 4 CR: 50331648 BR: 0 RSP: 996 DSP: 59 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 107 PC:  22 DA:  59 AC: 0 DR: 4 CR: 842277938 BR: 0 RSP: 996 DSP: 59 popdr [0x8 -         34 - popdr]
DEBUG   machine:simulation    TICK: 111 PC:  23 DA:  55 AC: 0 DR: 4 CR: 874787345 BR: 0 RSP: 996 DSP: 55 greater [0x8 -         24 - greater]
DEBUG   machine:simulation    TICK: 115 PC:  24 DA:  55 AC: -1 DR: 111 CR: 607260928 BR: 0 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 118 PC:  25 DA:  55 AC: -1 DR: 111 CR: 839974912 BR: 0 RSP: 996 DSP: 55 while 42 [0x8 -   1100002A - while (0000002A)]
DEBUG   machine:simulation    TICK: 123 PC:  29 DA:  29 AC: -1 DR: 111 CR: 285212714 BR: 42 RSP: 996 DSP: 51 loadimm 47 [0x8 -    300002F - loadimm (0000002F)]
DEBUG   machine:simulation    TICK: 126 PC:  33 DA:  55 AC: 47 DR: 111 CR: 50331695 BR: 47 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 129 PC:  34 DA:  55 AC: 47 DR: 111 CR: 839005234 BR: 47 RSP: 996 DSP: 55 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK: 133 PC:  35 DA:  47 AC: 47 DR: 111 CR: 36975152 BR: 47 RSP: 996 DSP: 51 popdr [0x8 -         34 - popdr]
DEBUG   machine:simulation    TICK: 138 PC:  36 DA:  55 AC: 4 DR: 111 CR: 875704339 BR: 47 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 142 PC:  37 DA:  51 AC: 4 DR: 4 CR: 842011392 BR: 47 RSP: 996 DSP: 51 save [0x8 -         30 - save]
DEBUG   machine:simulation    TICK: 146 PC:  38 DA:   4 AC: 111 DR: 4 CR: 806551552 BR: 47 RSP: 996 DSP: 47 repeat 8 [0x8 -   13000008 - repeat (00000008)]
DEBUG   machine:simulation    TICK: 150 PC:   8 DA:   8 AC: 111 DR: 4 CR: 318767112 BR: 8 RSP: 996 DSP: 47 loadimm 43 [0x8 -    300002B - loadimm (0000002B)]
DEBUG   machine:simulation    TICK: 153 PC:  12 DA:  51 AC: 43 DR: 4 CR: 50331691 BR: 43 RSP: 996 DSP: 51 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 156 PC:  13 DA:  51 AC: 43 DR: 4 CR: 839004674 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK: 160 PC:  14 DA:  43 AC: 43 DR: 4 CR: 36831798 BR: 43 RSP: 996 DSP: 47 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 165 PC:  15 DA:  51 AC: 0 DR: 4 CR: 839005699 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK: 169 PC:  16 DA:   0 AC: 0 DR: 4 CR: 37094144 BR: 43 RSP: 996 DSP: 47 dup [0x8 -         36 - dup]
DEBUG   machine:simulation    TICK: 174 PC:  17 DA:  51 AC: 111 DR: 4 CR: 906166272 BR: 43 RSP: 996 DSP: 51 loadimm 0 [0x8 -    3000000 - loadimm (00000000)]
DEBUG   machine:simulation    TICK: 179 PC:  21 DA:  59 AC: 0 DR: 4 CR: 50331648 BR: 0 RSP: 996 DSP: 59 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 182 PC:  22 DA:  59 AC: 0 DR: 4 CR: 842277938 BR: 0 RSP: 996 DSP: 59 popdr [0x8 -         34 - popdr]
DEBUG   machine:simulation    TICK: 186 PC:  23 DA:  55 AC: 0 DR: 4 CR: 874787345 BR: 0 RSP: 996 DSP: 55 greater [0x8 -         24 - greater]
DEBUG   machine:simulation    TICK: 190 PC:  24 DA:  55 AC: -1 DR: 111 CR: 607260928 BR: 0 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 193 PC:  25 DA:  55 AC: -1 DR: 111 CR: 839974912 BR: 0 RSP: 996 DSP: 55 while 42 [0x8 -   1100002A - while (0000002A)]
DEBUG   machine:simulation    TICK: 198 PC:  29 DA:  29 AC: -1 DR: 111 CR: 285212714 BR: 42 RSP: 996 DSP: 51 loadimm 47 [0x8 -    300002F - loadimm (0000002F)]
DEBUG   machine:simulation    TICK: 201 PC:  33 DA:  55 AC: 47 DR: 111 CR: 50331695 BR: 47 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 204 PC:  34 DA:  55 AC: 47 DR: 111 CR: 839005234 BR: 47 RSP: 996 DSP: 55 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK: 208 PC:  35 DA:  47 AC: 47 DR: 111 CR: 36975152 BR: 47 RSP: 996 DSP: 51 popdr [0x8 -         34 - popdr]
DEBUG   machine:simulation    TICK: 213 PC:  36 DA:  55 AC: 4 DR: 111 CR: 875704339 BR: 47 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 217 PC:  37 DA:  51 AC: 4 DR: 4 CR: 842011392 BR: 47 RSP: 996 DSP: 51 save [0x8 -         30 - save]
DEBUG   machine:simulation    TICK: 221 PC:  38 DA:   4 AC: 111 DR: 4 CR: 806551552 BR: 47 RSP: 996 DSP: 47 repeat 8 [0x8 -   13000008 - repeat (00000008)]
DEBUG   machine:simulation    TICK: 225 PC:   8 DA:   8 AC: 111 DR: 4 CR: 318767112 BR: 8 RSP: 996 DSP: 47 loadimm 43 [0x8 -    300002B - loadimm (0000002B)]
DEBUG   machine:simulation    TICK: 228 PC:  12 DA:  51 AC: 43 DR: 4 CR: 50331691 BR: 43 RSP: 996 DSP: 51 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 231 PC:  13 DA:  51 AC: 43 DR: 4 CR: 839004674 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK: 235 PC:  14 DA:  43 AC: 43 DR: 4 CR: 36831798 BR: 43 RSP: 996 DSP: 47 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 240 PC:  15 DA:  51 AC: 0 DR: 4 CR: 839005699 BR: 43 RSP: 996 DSP: 51 load [0x8 -          2 - load]
DEBUG   machine:simulation    TICK: 244 PC:  16 DA:   0 AC: 0 DR: 4 CR: 37094144 BR: 43 RSP: 996 DSP: 47 dup [0x8 -         36 - dup]
DEBUG   machine:simulation    TICK: 249 PC:  17 DA:  51 AC: 0 DR: 4 CR: 906166272 BR: 43 RSP: 996 DSP: 51 loadimm 0 [0x8 -    3000000 - loadimm (00000000)]
DEBUG   machine:simulation    TICK: 254 PC:  21 DA:  59 AC: 0 DR: 4 CR: 50331648 BR: 0 RSP: 996 DSP: 59 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 257 PC:  22 DA:  59 AC: 0 DR: 4 CR: 842277938 BR: 0 RSP: 996 DSP: 59 popdr [0x8 -         34 - popdr]
DEBUG   machine:simulation    TICK: 261 PC:  23 DA:  55 AC: 0 DR: 4 CR: 874787345 BR: 0 RSP: 996 DSP: 55 greater [0x8 -         24 - greater]
DEBUG   machine:simulation    TICK: 265 PC:  24 DA:  55 AC: 0 DR: 0 CR: 607260928 BR: 0 RSP: 996 DSP: 55 popac [0x8 -         32 - popac]
DEBUG   machine:simulation    TICK: 268 PC:  25 DA:  55 AC: 0 DR: 0 CR: 839974912 BR: 0 RSP: 996 DSP: 55 while 42 [0x8 -   1100002A - while (0000002A)]
DEBUG   machine:simulation    TICK: 273 PC:  42 DA:  42 AC: 0 DR: 0 CR: 285212714 BR: 42 RSP: 996 DSP: 51 halt [0x8 -         26 - halt]
INFO   machine:simulation    output_buffer: [102, 111, 111]
foo
ticks: 275

```

0x0 VARIABLE input_address
0x4 VARIABLE output_address
10 VARIABLE count_of_numbers
1 VARIABLE counter

: SQUARE_OF_SUM
    count_of_numbers @ counter !
    0
    BEGIN
    counter @ 0 >
    WHILE
    counter @
    dup 1 - dup 1 - counter ! + +
    REPEAT
    # после этого на вершине стека сумма ста чисел
    dup *
; # на вершине - квадрат суммы

: SUM_OF_SQUARES
    count_of_numbers @ counter !
    0
    BEGIN
    counter @ 0 >
    WHILE
    counter @
    dup * +
    REPEAT
; # на вершине - сумма квадратов

SQUARE_OF_SUM # SUM_OF_SQUARES -
output_address @ !

HALT
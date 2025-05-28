# Найти разность между суммой квадратов и квадратом суммы первых ста натуральных чисел.

0x0 VARIABLE input_address
0x4 VARIABLE output_address
100 VARIABLE count_of_numbers
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
    dup *
;

: SUM_OF_SQUARES
    count_of_numbers @ counter !
    0
    BEGIN
    counter @ 0 >
    WHILE
    counter @
    dup * +
    counter @ 1 - counter !
    REPEAT
;

SQUARE_OF_SUM SUM_OF_SQUARES -
output_address @ !

HALT
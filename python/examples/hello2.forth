# Отсортировать массив чисел

0x0 VARIABLE input_address
0x4 VARIABLE output_address
5 VARIABLE buffer
4 VARIABLE buffer1
S" ______________________" VARIABLE buffer2
1 VARIABLE pointer1
2 VARIABLE pointer2
3 VARIABLE temp


: SORT 
    buffer pointer1 ! # инициализировали указатель

    BEGIN
    pointer1 @ @ 0 = NOT # пока не достигнем нуля
    WHILE
        pointer1 @ 4 + pointer2 !
        BEGIN
        pointer2 @ @ 0 = NOT # пока не достигнем нуля
        WHILE
            pointer1 @ @ pointer2 @ @ > IF
            pointer2 @ @ temp !
            pointer1 @ @ pointer2 @ !
            temp @ pointer1 @ !
            ELSE
            THEN
            pointer2 @ 4 + pointer2 !
        REPEAT
        pointer1 @ 4 + pointer1 !
    REPEAT

;

buffer pointer1 !

# получаем данные
BEGIN
input_address @ @ dup 0 = NOT
WHILE
pointer1 @ !
pointer1 @ 4 + pointer1 !
REPEAT

0 pointer1 @ !

SORT

buffer pointer1 !

BEGIN
pointer1 @ @ dup 0 = NOT
WHILE
output_address @ !
pointer1 @ 4 + pointer1 !
REPEAT


HALT
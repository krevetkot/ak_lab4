0x0 VARIABLE input_address
0x4 VARIABLE output_address
S" What is your name? " VARIABLE question
0 VARIABLE null_term
S" Hello, " VARIABLE hello
S" ___________________________" VARIABLE buffer
0 VARIABLE pointer

: PRINT_STRING
    BEGIN
    dup @ dup 0 >
    WHILE
    output_address @ !
    4 +
    REPEAT
;

: SAVE_STRING
    buffer pointer !

    BEGIN
    input_address @ @ dup 0 >
    WHILE
    pointer @ !
    pointer @ 4 + pointer !
    REPEAT
    33 pointer @ !
    0 pointer @ 4 + !
;

question PRINT_STRING
SAVE_STRING
hello PRINT_STRING

HALT
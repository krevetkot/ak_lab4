0x0 VARIABLE input_address
0x4 VARIABLE output_address
S" Hello, world!" VARIABLE hello_world
0 VARIABLE null_term

: PRINT_STRING
    BEGIN
    DUP @ DUP 0 >
    WHILE
    output_address @ !
    4 +
    REPEAT
;

hello_world PRINT_STRING

HALT
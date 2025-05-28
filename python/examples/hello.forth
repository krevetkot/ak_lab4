0x0 VARIABLE input_address
0x4 VARIABLE output_address
S" W" VARIABLE hello_var
0 VARIABLE null_term

: PRINT_STRING
    BEGIN
    dup @ dup 0 >
    WHILE
    output_address @ !
    1 +
    REPEAT
;

hello_var PRINT_STRING


HALT
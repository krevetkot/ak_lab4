0x0 VARIABLE input_address
0x4 VARIABLE output_address
0 VARIABLE symbol
S" What is your name?" VARIABLE hello_var
0 VARIABLE null_term

: PRINT_STRING
    BEGIN
    dup @ symbol ! 
    symbol @ 0 >
    WHILE
    symbol @
    output_address @ !
    1 +
    REPEAT
;

hello_var PRINT_STRING


HALT
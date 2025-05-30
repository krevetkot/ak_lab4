0x0 VARIABLE input_address
0x4 VARIABLE output_address

BEGIN
input_address @ @ DUP 0 >
WHILE
output_address @ !
REPEAT

HALT
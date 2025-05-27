0x0 VARIABLE input_address
0x4 VARIABLE output_address
0x2 VARIABLE counter

BEGIN
counter @ 0 >
WHILE
1 output_address @ !
counter @ 1 - counter !
REPEAT

HALT
0x0 VARIABLE input_address
0x4 VARIABLE output_address
0x2 VARIABLE counter

2 1 > IF
1 output_address @ !
ELSE
2 output_address @ !
THEN

HALT
0x0 VARIABLE input_address
0x4 VARIABLE output_address
0 VARIABLE element


BEGIN
input_address @ @ element ! 
element @ 0 >
WHILE
element @
output_address @ !
REPEAT

HALT
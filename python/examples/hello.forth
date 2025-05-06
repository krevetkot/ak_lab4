0x80 VARIABLE input_addr 
0x84 VARIABLE output_addr
0x1 VARIABLE one

: FUNC one + ;

BEGIN # это комментарий
input_addr @
WHILE 
output_addr !
REPEAT

1 > IF
1 +
ELSE
1 -
THEN

42 FUNC 
 
HALT
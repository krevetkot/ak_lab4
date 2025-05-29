0 VARIABLE input_address
4 VARIABLE output_address
0x0001000FFFFFFFF VARIABLE var1 # 17596481011711
0x1 VARIABLE var2
0 VARIABLE upper_result
0 VARIABLE lower_result

var1 4 + @
var2 4 + @
+ 
# до этого флаг С был в нуле, теперь стал 1
lower_result !

var1 @ var2 @ +
upper_result !

upper_result @ output_address @ !
lower_result @ output_address @ !

HALT


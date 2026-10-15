set pagination off
set confirm off
break *0x5332a3 if *(unsigned int*)($edi+8)==640
run --codol-archive-probe "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources/ff_init_coop_training_mp_cargoship_V29/2.bin" "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe"
set $blocks=*(unsigned int*)($esp+4)
set $b3=*(unsigned int*)($blocks+24)
x/40bx $b3+0xacaf
set $size=*(unsigned int*)($blocks+28)
dump binary memory E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/model-block3.bin $b3 ($b3+$size)
x/72bx $b3+0x746fb8
x/72bx $b3+0x746fa0
x/24f $b3+0x746fed-1
stepi
finish
p/x $eax
continue
quit

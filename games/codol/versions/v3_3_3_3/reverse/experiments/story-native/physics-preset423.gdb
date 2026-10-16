set pagination off
set confirm off
file E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/dedrun-debug-fixedbase.exe
break *0x54504c if *(unsigned int*)($ebp+16)==156
break *0x545051 if *(unsigned int*)($ebp+16)==156
break *0x545056 if *(unsigned int*)($ebp+16)==156
break *0x54505b if *(unsigned int*)($ebp+16)==156
run --codol-runtime-probe E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe mp_cargoship E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources-common-gfx/5.bin E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources-common/ff_init_common_mp_V43/5.bin E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources-base/ff_init_mp_cargoship_V32/2.bin E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources/ff_init_coop_training_mp_cargoship_V29/2.bin
bt
x/6wx $ebp+8
x/21wx $esp+0x48
x/96bx *(unsigned int*)($esp+0x4c)
x/23wx *(unsigned int*)($esp+0x38)+156*92
set $c=*(unsigned int**)($esp+0x10)
dump binary memory E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/preset-records423.bin $c[165] $c[165]+$c[166]*20
quit

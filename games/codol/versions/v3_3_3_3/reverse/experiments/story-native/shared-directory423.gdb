set pagination off
set confirm off
file E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/dedrun-debug-fixedbase.exe
break *0x160f2546
run --codol-archive-probe "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources-common/ff_init_common_mp_V43/5.bin" "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe"
set $c=*(unsigned int**)($esp+4)
printf "kind=%u pointer=%08x size=%u count=%u\n", *(unsigned int*)($esp+8), *(unsigned int*)($esp+12), *(unsigned int*)($esp+16), $c[166]
x/40wx $c
dump binary memory E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/alias-context423.bin $c ((char*)$c)+720
dump binary memory E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/alias-records423.bin $c[165] $c[165]+$c[166]*20
x/12wx ((char*)$c[3])+0x13a0df4
quit

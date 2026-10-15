set pagination off
set confirm off
file E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/image-alias-debug.exe
break *0x160f2666
run --codol-archive-probe E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources-marketplace/2.bin E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe
set $c=*(unsigned int**)($esp+4)
printf "kind=%u pointer=%08x count=%u\n", *(unsigned int*)($esp+8), *(unsigned int*)($esp+12), $c[166]
x/12wx $c[3]+0x1f4ad0
dump binary memory E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/image-alias-context.bin $c ((char*)$c)+720
dump binary memory E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/image-alias-records.bin $c[165] $c[165]+$c[166]*20
quit

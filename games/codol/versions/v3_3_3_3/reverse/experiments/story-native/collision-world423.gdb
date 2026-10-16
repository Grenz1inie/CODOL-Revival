set pagination off
set confirm off
break *0x5750af
run --codol-archive-probe "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources-base/ff_init_mp_cargoship_V32/2.bin" "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe"
stepi
finish
printf "world_planes_return=%d\n",$eax
continue
quit

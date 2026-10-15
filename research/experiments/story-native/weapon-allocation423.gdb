set pagination off
set confirm off
break *0x54f9ba if *(unsigned int*)($eax+0x88)>=5347225 && *(unsigned int*)($eax+0x88)<5407830
commands
silent
printf "source=%x block=%d size=%x align=%d consume=%d dest=%x caller=%x\n", *(unsigned int*)($eax+0x88),$edx,$ecx,*(unsigned int*)($esp+4),*(unsigned int*)($esp+8),*(unsigned int*)($eax+0x60+$edx*4),*(unsigned int*)$esp
continue
end
run --codol-archive-probe "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources/ff_init_coop_training_mp_cargoship_V29/2.bin" "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe"
quit

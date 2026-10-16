set pagination off
set confirm off
break *0x552da0 if $esi==-1 && $eax==0xffffffff
commands
silent
printf "model=0x%x block3=0x%x source=0x%x\n", **(unsigned int**)($ebp-16), *(unsigned int*)($ebx+0x6c), *(unsigned int*)($ebx+0x88)
continue
end
run --codol-archive-probe "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources/ff_init_coop_training_mp_cargoship_V29/2.bin" "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe"
quit

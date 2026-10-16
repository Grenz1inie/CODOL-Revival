set pagination off
set confirm off
break *0x56ae9b
commands
silent
printf "component=layout result=%d\n",$eax
continue
end
break *0x56af0a
commands
silent
printf "component=static_models result=%d\n",$eax
continue
end
break *0x56af2b
commands
silent
printf "component=world_brushes result=%d\n",$eax
continue
end
break *0x56af5b
commands
silent
printf "component=terrain result=%d\n",$eax
continue
end
break *0x56af75
commands
silent
printf "component=leaves result=%d\n",$eax
continue
end
break *0x56af8f
commands
silent
printf "component=brush_tree result=%d\n",$eax
continue
end
break *0x56afb7
commands
silent
printf "component=materials result=%d\n",$eax
continue
end
break *0x56afd5
commands
silent
printf "component=entities result=%d\n",$eax
continue
end
run --codol-archive-probe "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL-Revival/research/experiments/story-native/resources-base/ff_init_mp_cargoship_V32/2.bin" "E:/Games/CODOL_Experience_V3.3.3.3_FULL.7z/CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe"
quit

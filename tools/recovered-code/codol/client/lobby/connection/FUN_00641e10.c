// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: dwauth 与 STUN 配置读取
// VA: 0x00641e10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_88a82b73182cc47932137af41a0471451f32e98cb986bebdcb5fa10822f80bb1
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00641e10(DWORD param_1,int param_2,char *param_3)

{
  byte bVar1;
  char cVar2;
  char cVar3;
  HWND hWnd;
  FILE *pFVar4;
  int iVar5;
  char *pcVar6;
  HANDLE hFindFile;
  byte *pbVar7;
  BOOL BVar8;
  DWORD DVar9;
  undefined4 uVar10;
  uint uVar11;
  char *pcVar12;
  byte bVar13;
  byte *pbVar14;
  undefined1 *puVar15;
  LPCRITICAL_SECTION lpCriticalSection;
  uint uVar16;
  size_t _Count;
  undefined1 auStack_294 [3];
  char cStack_291;
  char *apcStack_290 [2];
  char *pcStack_288;
  uint uStack_284;
  LARGE_INTEGER local_280;
  undefined4 uStack_278;
  undefined4 uStack_274;
  undefined4 uStack_270;
  uint uStack_26c;
  undefined4 uStack_268;
  undefined4 uStack_264;
  undefined4 uStack_260;
  undefined4 uStack_25c;
  _WIN32_FIND_DATAA _Stack_258;
  char acStack_118 [268];
  uint local_c;
  
  local_c = DAT_00cc7c80 ^ (uint)auStack_294;
  local_280.s.LowPart = param_1;
  if (DAT_0c687184 == 0xb7) {
    hWnd = FindWindowA((LPCSTR)0x0,&DAT_00c77854);
    SetForegroundWindow(hWnd);
    goto LAB_00641e57;
  }
  FUN_0059c2b0();
  DAT_07817e60 = (int *)FUN_004ada80();
  if (DAT_07817e60 != (int *)0x0) {
    (**(code **)(*DAT_07817e60 + 4))();
  }
  if (DAT_01f9db17 == '\0') {
    DAT_01f9db17 = '\x01';
    _DAT_035f6c8c = 0xdeadbeef;
    DAT_035f244c = &DAT_035f6c8c;
  }
  cVar3 = *param_3;
  _strncpy(&DAT_03746950,param_3 + (cVar3 == '\"'),0x3ff);
  DAT_03746d4f = 0;
  pcVar6 = &DAT_03746950;
  do {
    pcVar12 = pcVar6;
    pcVar6 = pcVar12 + 1;
  } while (*pcVar12 != '\0');
  if (((cVar3 == '\"') != 0) && (pcVar12[-1] == '\"')) {
    pcVar12[-1] = '\0';
  }
  DAT_037471d3 = 0;
  DAT_0374694b = 0;
  pFVar4 = _fopen("dwauth.ini","r");
  if (pFVar4 != (FILE *)0x0) {
    FID_conflict__fscanf(pFVar4,"%59s\n",&DAT_03747198);
    FID_conflict__fscanf(pFVar4,"%hu\n",&DAT_037489e4);
    FID_conflict__fscanf(pFVar4,"%59s\n",&DAT_03746910);
    FID_conflict__fscanf(pFVar4,"%hu\n",&DAT_0374911c);
    FID_conflict__fscanf(pFVar4,"%x\n",&DAT_03749110);
    _fclose(pFVar4);
  }
  DAT_03748e58 = 0;
  DAT_03749118 = 0;
  DAT_03748ea8 = 0;
  _DAT_03748ee3 = 0;
  _DAT_03748f1f = 0;
  _DAT_03748f5b = 0;
  _DAT_03748f97 = 0;
  _DAT_03748fd3 = 0;
  _DAT_0374900f = 0;
  _DAT_0374904b = 0;
  _DAT_03749087 = 0;
  _DAT_037490c3 = 0;
  DAT_037490ff = 0;
  pFVar4 = _fopen("stun.ini","r");
  if (pFVar4 != (FILE *)0x0) {
    puVar15 = &DAT_03748ea8;
    do {
      iVar5 = FID_conflict__fscanf(pFVar4,"%59s\n",puVar15);
      if (iVar5 == 0) break;
      puVar15 = puVar15 + 0x3c;
    } while ((int)puVar15 < 0x3749100);
  }
  pFVar4 = _fopen("buildconfig.ini","r");
  if (pFVar4 == (FILE *)0x0) {
    _strcpy_s(&DAT_03747168,0x10,"release");
    _strcpy_s(&DAT_03747158,0x10,"release");
    _strcpy_s(&DAT_03748e94,0x10,"release");
    DAT_037471d4 = 2;
  }
  else {
    FID_conflict__fscanf(pFVar4,"build_version=%s\n",&DAT_03747168);
    FID_conflict__fscanf(pFVar4,"build_version_column=%d\n",&DAT_037471d4);
    FID_conflict__fscanf(pFVar4,"stream=%s\n",&DAT_03747158);
    FID_conflict__fscanf(pFVar4,"main_version=%s\n",&DAT_03748e94);
    _fclose(pFVar4);
  }
  lpCriticalSection = (LPCRITICAL_SECTION)&DAT_037444f0;
  do {
    InitializeCriticalSection(lpCriticalSection);
    lpCriticalSection = lpCriticalSection + 1;
  } while ((int)lpCriticalSection < 0x37448e0);
  FUN_005a6e00();
  FUN_00401000();
  DAT_03748ea4 = FUN_00633950(&DAT_00c778f0,5,0,0,local_280.s.HighPart,uStack_278,uStack_274,0,2,
                              &DAT_00c4e869);
  DAT_037489d8 = FUN_00633950(&DAT_00c778f8,0,0,1,local_280.s.HighPart,uStack_278,uStack_274,0,0,
                              &DAT_00c4e869);
  DAT_0374694c = FUN_00633950(&DAT_00c77900,0,0,1,local_280.s.HighPart,uStack_278,uStack_274,0,0,
                              &DAT_00c4e869);
  DAT_0783f654 = 1;
  pFVar4 = _fopen("iips.ini","r");
  if (pFVar4 != (FILE *)0x0) {
    pcStack_288 = (char *)0x0;
    apcStack_290[0] = (LPCSTR)0x1;
    FID_conflict__fscanf(pFVar4,"enable_iips=%d\n",&pcStack_288);
    FID_conflict__fscanf(pFVar4,"iips_url=%s\n",s__http___down_update_qq_com__00cd9b47 + 1);
    FID_conflict__fscanf(pFVar4,"iips_enableOptionalDownloads=%s\n",apcStack_290);
    if (*(char *)(DAT_037489d8 + 8) == '\0') {
      puVar15 = (undefined1 *)(uint)(pcStack_288 != (char *)0x0);
    }
    else {
      puVar15 = &DAT_00c4ec0c;
      if (pcStack_288 == (char *)0x0) {
        puVar15 = &DAT_00c5e024;
      }
    }
    FUN_00632150(DAT_037489d8,puVar15,local_280.s.HighPart,uStack_278,uStack_274,0);
    if (*(char *)(DAT_0374694c + 8) == '\0') {
      puVar15 = (undefined1 *)(uint)(apcStack_290[0] != (LPCSTR)0x0);
    }
    else {
      puVar15 = &DAT_00c4ec0c;
      if (apcStack_290[0] == (LPCSTR)0x0) {
        puVar15 = &DAT_00c5e024;
      }
    }
    FUN_00632150(DAT_0374694c,puVar15,local_280.s.HighPart,uStack_278,uStack_274,0);
    _fclose(pFVar4);
  }
  FUN_00640790();
  FUN_00640840();
  cVar3 = FUN_0063e110();
  if (cVar3 == '\0') {
    FUN_00637c60(&DAT_00c774b8,"localization.txt");
    FUN_00642880(&DAT_00c77494,0x10,0,1);
    goto LAB_00641e57;
  }
  if (*(int *)(DAT_037489d8 + 0xc) == 0) {
    DAT_0783f654 = 0;
  }
  pcVar6 = _getenv("IW_CORE_PATH");
  apcStack_290[0] = (char *)FUN_00637c60("%s\\tools_bin\\COD.NET\\COD.CrashReport.exe",pcVar6);
  hFindFile = FindFirstFileA(apcStack_290[0],&_Stack_258);
  if (hFindFile == (HANDLE)0xffffffff) {
    apcStack_290[0] = "..\\tools_bin\\COD.Net\\COD.CrashReport.exe";
  }
  FindClose(hFindFile);
  acStack_118[0] = '\0';
  pcVar6 = _strstr(&DAT_03746950,"+set ");
  if (pcVar6 != (char *)0x0) {
LAB_00642360:
    pbVar7 = (byte *)(pcVar6 + 5);
    bVar13 = *pbVar7;
    while (bVar13 == 0x20) {
      pbVar7 = pbVar7 + 1;
      bVar13 = *pbVar7;
    }
    pcStack_288 = &DAT_00c779d0 + -(int)pbVar7;
    pbVar14 = pbVar7;
    iVar5 = 4;
    do {
      uVar11 = (uint)*pbVar14;
      uVar16 = (uint)(byte)pcStack_288[(int)pbVar14];
      pbVar14 = pbVar14 + 1;
      if (iVar5 == 0) goto LAB_006423dc;
      if (uVar11 != uVar16) {
        if (uVar11 - 0x41 < 0x1a) {
          uVar11 = uVar11 + 0x20;
        }
        if (uVar16 - 0x41 < 0x1a) {
          uVar16 = uVar16 + 0x20;
        }
        if (uVar11 != uVar16) goto LAB_006423b7;
      }
      iVar5 = iVar5 + -1;
      if (uVar11 == 0) goto LAB_006423dc;
    } while( true );
  }
  goto LAB_00642427;
LAB_006423b7:
  if ((char)((uVar16 <= uVar11) * '\x02') != '\x01') {
    pcVar6 = _strstr((char *)pbVar7,"+set");
    if (pcVar6 == (char *)0x0) goto LAB_00642427;
    goto LAB_00642360;
  }
LAB_006423dc:
  pbVar7 = pbVar7 + 4;
  bVar13 = *pbVar7;
  while (bVar13 == 0x20) {
    pbVar7 = pbVar7 + 1;
    bVar13 = *pbVar7;
  }
  _Count = 0;
  bVar13 = 0x20;
  if (*pbVar7 == 0x22) {
    pbVar7 = pbVar7 + 1;
    bVar13 = 0x22;
  }
  bVar1 = *pbVar7;
  while ((bVar1 != bVar13 && (bVar1 != 0))) {
    iVar5 = _Count + 1;
    _Count = _Count + 1;
    bVar1 = pbVar7[iVar5];
  }
  _strncpy(acStack_118,(char *)pbVar7,_Count);
  acStack_118[_Count] = '\0';
LAB_00642427:
  if (acStack_118[0] == '\0') {
    pcVar6 = (char *)FUN_00637c60("main\\%s");
  }
  else {
    pcVar6 = (char *)FUN_00637c60("main\\%s_%s",acStack_118,"console_mp.elog");
  }
  BVar8 = IsDebuggerPresent();
  if (BVar8 == 0) {
    _strncpy(&DAT_0788bc98,"codoMP_client_ship.exe",0x100);
    _strncpy(&DAT_0788bd98,pcVar6,0x100);
    _strncpy(&DAT_07885988,apcStack_290[0],0x100);
    DAT_07885978 = SetUnhandledExceptionFilter(FUN_0063c820);
  }
  _strncpy(&DAT_0788be98,"Initializing...",0x7ff);
  DAT_0788c697 = 0;
  if (param_2 == 0) {
    FUN_00636990();
    cStack_291 = '\0';
    apcStack_290[0] = (LPCSTR)0x0;
    if (0 < DAT_017c310c) {
      do {
        pcStack_288 = *(char **)(DAT_017c3110 + (int)apcStack_290[0] * 4);
        pcVar6 = pcStack_288;
        do {
          cVar3 = *pcVar6;
          pcVar6 = pcVar6 + 1;
        } while (cVar3 != '\0');
        pcVar12 = "-q";
        iVar5 = (int)pcVar6 - (int)(pcStack_288 + 1);
        while( true ) {
          cVar3 = (pcStack_288 + -0xc77a24)[(int)pcVar12];
          cVar2 = *pcVar12;
          pcVar12 = pcVar12 + 1;
          if (iVar5 == 0) goto LAB_0064254d;
          if (cVar3 != cVar2) break;
          iVar5 = iVar5 + -1;
          if (cVar3 == '\0') goto LAB_0064254d;
        }
        if ((char)((cVar2 <= cVar3) * '\x02') == '\x01') {
LAB_0064254d:
          DAT_078852db = '\x01';
          goto LAB_00642554;
        }
        pcVar6 = pcStack_288;
        do {
          cVar3 = *pcVar6;
          pcVar6 = pcVar6 + 1;
        } while (cVar3 != '\0');
        pcVar12 = "-qa";
        iVar5 = (int)pcVar6 - (int)(pcStack_288 + 1);
        do {
          cVar3 = (pcStack_288 + -0xc77a28)[(int)pcVar12];
          cVar2 = *pcVar12;
          pcVar12 = pcVar12 + 1;
          if (iVar5 == 0) break;
          if (cVar3 != cVar2) {
            if ((char)((cVar2 <= cVar3) * '\x02') != '\x01') goto LAB_00642816;
            break;
          }
          iVar5 = iVar5 + -1;
        } while (cVar3 != '\0');
        cStack_291 = '\x01';
        DAT_07885984 = 1;
LAB_00642816:
        apcStack_290[0] = (char *)((int)apcStack_290[0] + 1);
      } while ((int)apcStack_290[0] < DAT_017c310c);
    }
    if ((DAT_078852db != '\0') || (cStack_291 != '\0')) {
LAB_00642554:
      *(undefined4 *)(*(int *)ThreadLocalStoragePointer + 0xc) = 0xffffffff;
      DAT_02916ca5 = 1;
      FUN_0059f2e0();
      Sleep(0);
      QueryPerformanceFrequency((LARGE_INTEGER *)apcStack_290);
      _DAT_00cd9b44 = (1.0 / (float)CONCAT44(apcStack_290[1],apcStack_290[0])) * 1000.0;
      _DAT_037444e0 = (double)_DAT_00cd9b44;
      _DAT_037444e8 = (double)(_DAT_00cd9b44 * 1000.0);
      _DAT_00cd9b44 = 1.0 / _DAT_00cd9b44;
      FUN_0063e8d0();
      DAT_03749a98 = (char *)0x8;
      DAT_03749ac4 = (char *)0x8;
      DAT_03749ae4 = 0x18;
      SystemParametersInfoA(0x3a,8,&DAT_03749a98,0);
      SystemParametersInfoA(0x34,8,&DAT_03749ac4,0);
      SystemParametersInfoA(0x32,0x18,&DAT_03749ae4,0);
      pcStack_288 = DAT_03749a98;
      apcStack_290[0] = DAT_03749ac4;
      apcStack_290[1] = (char *)DAT_03749ac8;
      uStack_270 = DAT_03749ae4;
      uStack_26c = DAT_03749ae8;
      uStack_268 = DAT_03749aec;
      uStack_264 = DAT_03749af0;
      uStack_284 = DAT_03749a9c;
      uStack_260 = DAT_03749af4;
      uStack_25c = DAT_03749af8;
      if ((DAT_03749a9c & 1) == 0) {
        uStack_284 = DAT_03749a9c & 0xfffffff3;
        SystemParametersInfoA(0x3b,8,&pcStack_288,0);
      }
      if (((uint)apcStack_290[1] & 1) == 0) {
        apcStack_290[1] = (char *)((uint)apcStack_290[1] & 0xfffffff3);
        SystemParametersInfoA(0x35,8,apcStack_290,0);
      }
      if ((uStack_26c & 1) == 0) {
        uStack_26c = uStack_26c & 0xfffffff3;
        SystemParametersInfoA(0x33,0x18,&uStack_270,0);
      }
      DAT_03749ab0 = local_280.s.LowPart;
      thunk_FUN_00aa54f0();
      FUN_00640930();
      SetErrorMode(1);
      if (DAT_0788c760 == 0) {
        DAT_03749354 = timeGetTime();
        QueryPerformanceCounter(&local_280);
        _DAT_03749468 = local_280.s.LowPart;
        _DAT_0374946c = local_280.s.HighPart;
        DAT_0788c760 = 1;
      }
      timeGetTime();
      FUN_0059d0f0();
      FUN_00405200(1);
      __getcwd(acStack_118,0x100);
      SetFocus(DAT_03749aac);
      FUN_0063ed70();
      do {
        if (DAT_03749ab8 != 0) {
          Sleep(5);
        }
        if (((DAT_02916ca7 != '\0') && (DVar9 = GetCurrentThreadId(), DVar9 == DAT_02f24558)) &&
           (DAT_078b0938 == 0)) {
          DAT_078b0938 = 1;
          EnterCriticalSection((LPCRITICAL_SECTION)&DAT_03744820);
          if (DAT_02e16c50 < 0x20) {
            *(code **)(&DAT_02e14388 + DAT_02e16c50 * 4) = FUN_0063f650;
            DAT_02e16c50 = DAT_02e16c50 + 1;
          }
          LeaveCriticalSection((LPCRITICAL_SECTION)&DAT_03744820);
        }
        FUN_0059e000();
        FUN_00600c30();
      } while( true );
    }
    uVar10 = FUN_0063e1d0("WIN_ERROR");
    FUN_0063e1d0("WIN_NO_TCLS",uVar10,0x10,0,1);
    FUN_00642880();
  }
  else {
    DAT_03744908 = 0;
    DAT_0374490c = 0;
  }
LAB_00641e57:
  __security_check_cookie(local_c ^ (uint)auStack_294);
  return;
}


"""Launcher options belonging to one 3.19 installation."""
import json
from pathlib import Path
import re
import shutil
import time

OPTION_DEFAULTS = {'display_mode': 'windowed', 'resolution': '1280x720', 'game_language': 'en'}
RESOLUTIONS = ('1280x720', '1366x768', '1600x900', '1920x1080', '2560x1440', '3840x2160')


def validate(options):
    required = {'player_name', 'fov', 'max_fps'}
    if not isinstance(options, dict) or not required <= set(options) or set(options) - required - OPTION_DEFAULTS.keys():
        raise ValueError('需要玩家名、FOV 和帧率上限')
    options = {**OPTION_DEFAULTS, **options}
    name = options['player_name']
    # Match local_profile319.player_name, whose actual limit is 15, not the GUI's 16.
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_\-\[\]]{3,15}', name):
        raise ValueError('玩家名需为 3–15 位英文字母、数字、下划线、连字符或方括号')
    for field, low, high in (('fov', 60, 120), ('max_fps', 0, 400)):
        if type(options[field]) is not int or not low <= options[field] <= high:
            raise ValueError(f'{field} 需为 {low}–{high} 的整数')
    if options['display_mode'] not in ('windowed', 'fullscreen'):
        raise ValueError('显示模式需为窗口化或全屏')
    if options['resolution'] not in RESOLUTIONS:
        raise ValueError('请选择支持的分辨率')
    if options['game_language'] not in ('en', 'zh-CN'):
        raise ValueError('游戏语言需为简体中文或英文')
    return options


def read_options(runtime):
    runtime = Path(runtime)
    path = runtime / 'launch-settings.json'
    if path.exists():
        return validate(json.loads(path.read_text(encoding='utf-8')))
    profile = runtime / 'server/profile319.json'
    name = json.loads(profile.read_text(encoding='utf-8')).get('name', 'Player') if profile.exists() else 'Player'
    return validate({'player_name': name, 'fov': 90, 'max_fps': 0})


def save_options(runtime, options):
    options = validate(options)
    runtime = Path(runtime)
    runtime.mkdir(parents=True, exist_ok=True)
    temporary = runtime / 'launch-settings.tmp'
    temporary.write_text(json.dumps(options, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(runtime / 'launch-settings.json')
    return options


def apply_options(runtime):
    runtime = Path(runtime)
    options = read_options(runtime)
    path = runtime / 'server/profile319.json'
    profile = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if profile.get('name') != options['player_name']:
        if path.exists():
            backup = runtime / 'backups' / f'profile319-{time.time_ns()}.json'
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
        profile['name'] = options['player_name']
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(profile) + '\n', encoding='utf-8')
        temporary.replace(path)
    # 3.19 0x62ca80 copies dvar 3291 into the room's automatic-start flag.
    width, height = options['resolution'].split('x')
    return (f"+set cg_fov {options['fov']} +set com_maxfps {options['max_fps']} +set 3291 0 "
            f"+set r_fullscreen {int(options['display_mode'] == 'fullscreen')} +set r_mode {options['resolution']} "
            f"+set r_customWidth {width} +set r_customHeight {height}")

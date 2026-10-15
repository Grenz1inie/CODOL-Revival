"""One-shot, user-authorized Windows MCP input test; no persistent elevation."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--hwnd', type=int, required=True)
    parser.add_argument('--target', choices=('backpack', 'capture', 'story-start', 'point', 'move-fire'), default='backpack')
    parser.add_argument('--point', type=int, nargs=2, help='Observed client-area coordinates for this one click')
    parser.add_argument('--size', type=int, nargs=2, help='Client size in the observed screenshot')
    args = parser.parse_args()
    if args.target == 'point' and (args.point is None or args.size is None):
        parser.error('--target point requires --point X Y and --size WIDTH HEIGHT')
    if args.target == 'move-fire' and args.size is None:
        parser.error('--target move-fire requires --size WIDTH HEIGHT')
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise PermissionError('This one-shot test requires the approved elevated process')
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.SetProcessDPIAware()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        name = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(name))
        if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(length)) or Path(name.value).resolve() != GAME.resolve():
            raise ValueError('Unexpected target executable')
    finally:
        kernel.CloseHandle(handle)
    hwnd = wintypes.HWND(args.hwnd)
    owner = wintypes.DWORD()
    user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
    if owner.value != args.pid:
        raise ValueError('Window no longer belongs to the verified game')
    rectangle, origin = wintypes.RECT(), wintypes.POINT()
    if not user.GetClientRect(hwnd, ctypes.byref(rectangle)) or not user.ClientToScreen(hwnd, ctypes.byref(origin)):
        raise ctypes.WinError(ctypes.get_last_error())
    expected_size = tuple(args.size) if args.target in ('point', 'move-fire') else (1280, 960)
    if args.target != 'capture' and (rectangle.right, rectangle.bottom) != expected_size:
        raise ValueError('Window size differs from the observed screenshot; do not click')
    if args.target == 'point' and not (0 <= args.point[0] < rectangle.right and 0 <= args.point[1] < rectangle.bottom):
        raise ValueError('Click must stay inside the verified game client area')
    from windows_mcp import uia
    if not uia.SetForegroundWindow(args.hwnd) or uia.GetForegroundWindow() != args.hwnd:
        raise RuntimeError('Game did not become foreground; do not click')
    from PIL import ImageGrab
    time.sleep(0.5)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    ImageGrab.grab().save(ROOT / f'runtime/captures/screenshots/{stamp}-admin-input-before.png')
    # Observed warehouse > Backpack tab, relative to the 1280x960 client area.
    point = {'backpack': (56, 117), 'story-start': (1040, 820)}.get(args.target)
    if args.target == 'point':
        point = args.point
    if args.target == 'move-fire':
        if uia.GetForegroundWindow() != args.hwnd:
            raise RuntimeError('Game lost foreground; do not send movement')
        try:
            # DirectInput needs W's scan code, without the extended-key flag
            # used by the generic UI Automation PressKey helper.
            uia.keybd_event(0x57, 0x11, 0, 0)
            time.sleep(2)
        finally:
            uia.keybd_event(0x57, 0x11, 2, 0)
        if uia.GetForegroundWindow() != args.hwnd:
            raise RuntimeError('Game lost foreground; do not fire')
        point = (rectangle.right // 2, rectangle.bottom // 2)
    x, y = (origin.x + point[0], origin.y + point[1]) if point else (None, None)
    if point:
        uia.SetCursorPos(x, y)
        time.sleep(0.5)
        if args.target == 'move-fire':
            try:
                uia.mouse_event(2, 0, 0, 0, 0)
                time.sleep(2)
            finally:
                uia.mouse_event(4, 0, 0, 0, 0)
        else:
            uia.Click(x, y)
    time.sleep(1)
    screenshot = ROOT / f'runtime/captures/screenshots/{stamp}-admin-{args.target}.png'
    ImageGrab.grab().save(screenshot)
    result = {'pid': args.pid, 'hwnd': args.hwnd, 'target': args.target,
              'screen_point': [x, y], 'click_count': int(point is not None), 'screenshot': str(screenshot)}
    result_path = 'runtime/captures/admin-input-test.json' if args.target in ('point', 'move-fire') else 'research/evidence/admin-input-test.json'
    (ROOT / result_path).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        (ROOT / 'runtime/logs/admin-input-test.log').write_text(traceback.format_exc(), encoding='utf-8')
        raise

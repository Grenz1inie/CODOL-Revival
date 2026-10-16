"""Two bounded read-only probes of the same verified isolated client."""
from pathlib import Path
import runpy

for name in ('read_room_runtime.py', 'read_bot_names.py'):
    runpy.run_path(str(Path(__file__).with_name(name)), run_name='__main__')

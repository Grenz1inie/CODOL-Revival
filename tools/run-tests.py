"""Run manager and version suites once, with their explicit import roots."""
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[1]
version = root / 'games/codol/versions/v3_3_3_3'
sys.path[:0] = [str(root), str(root / 'src'), str(root / 'tests'),
                str(version / 'tests'), str(version / 'reverse/tools')]
suite = unittest.TestSuite()
for directory in (root / 'tests', version / 'tests'):
    suite.addTests(unittest.TestLoader().discover(str(directory)))
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(not result.wasSuccessful())

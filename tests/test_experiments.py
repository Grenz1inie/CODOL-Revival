"""The fixed A-drive lab session stop path (manager/experiments.py)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from manager import experiments


class LabSessionTests(unittest.TestCase):
    def test_absent_or_broken_session_is_not_running_and_stop_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as name:
            empty = Path(name)
            self.assertFalse(experiments.running(empty))
            self.assertFalse(experiments.stop(timeout=0.1, lab=empty))
            self.assertFalse((empty / 'stop.request').exists())
            (empty / 'startup.json').write_text('{ not json', encoding='utf-8')
            self.assertFalse(experiments.running(empty))

    def test_stop_signals_the_lab_and_waits_for_the_supervisor_to_exit(self):
        with tempfile.TemporaryDirectory() as name:
            lab = Path(name)
            (lab / 'startup.json').write_text(json.dumps({'supervisor': {'pid': 4242}}), encoding='utf-8')
            state = {'up': True}
            def supervisor(pid):
                if not state['up']:
                    return False
                if (lab / 'stop.request').exists():    # the supervisor leaves on the request
                    state['up'] = False
                    return False
                return pid == 4242
            with patch.object(experiments, '_alive', supervisor):
                self.assertTrue(experiments.running(lab))
                self.assertTrue(experiments.stop(timeout=2.0, lab=lab))
                self.assertTrue((lab / 'stop.request').exists())
                self.assertFalse(experiments.running(lab))

    def test_stop_reports_failure_when_the_lab_does_not_shut_down_in_time(self):
        with tempfile.TemporaryDirectory() as name:
            lab = Path(name)
            (lab / 'startup.json').write_text(json.dumps({'supervisor': {'pid': 4242}}), encoding='utf-8')
            with patch.object(experiments, '_alive', lambda pid: True):
                self.assertFalse(experiments.stop(timeout=0.2, lab=lab))


if __name__ == '__main__':
    unittest.main()

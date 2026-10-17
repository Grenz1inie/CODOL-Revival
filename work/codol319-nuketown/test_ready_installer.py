"""Installer seam: byte guard, suspended write window, and failure release."""
from contextlib import contextmanager
import unittest
from ready_gate_proposal import ORIGINAL
from ready_gate_experiment import install


class Memory:
    base = 0x400000
    def __init__(self, original=ORIGINAL, fail=False):
        self.data = {0x63c5e0: original}
        self.paused = False
        self.allocations = 0
        self.fail = fail
    @contextmanager
    def suspended(self):
        self.paused = True
        try: yield
        finally: self.paused = False
    def read(self, address, size): return self.data[address][:size]
    def allocate(self):
        assert self.paused
        self.allocations += 1
        return 0x20180000
    def write(self, address, data):
        assert self.paused
        if self.fail: raise OSError('controlled write failure')
        self.data[address] = data
    def executable(self, address): assert self.paused
    def patch(self, address, original, replacement):
        assert self.paused and self.read(address, len(original)) == original
        self.write(address, replacement)


class InstallerTests(unittest.TestCase):
    def test_unknown_original_is_rejected_without_writes(self):
        memory = Memory(b'wrong!')
        self.assertIsNone(install(memory))
        self.assertEqual(memory.data, {0x63c5e0: b'wrong!'})
        self.assertEqual(memory.allocations, 0)
        self.assertFalse(memory.paused)
    def test_valid_install_is_read_back_before_resuming(self):
        memory = Memory()
        result = install(memory)
        self.assertEqual(result['entry'], '0x63c5e0')
        self.assertEqual(result['original'], ORIGINAL.hex())
        self.assertEqual(memory.read(0x63c5e0, 6).hex(), result['patch'])
        self.assertFalse(memory.paused)
    def test_failed_cave_write_leaves_entry_original_and_resumes(self):
        memory = Memory(fail=True)
        with self.assertRaises(OSError): install(memory)
        self.assertEqual(memory.data[0x63c5e0], ORIGINAL)
        self.assertFalse(memory.paused)


if __name__ == '__main__': unittest.main()

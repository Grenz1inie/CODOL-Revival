"""Native startup must reject invalid packages before exposing a reservation."""
import json
from pathlib import Path
import tempfile
import unittest

from test_match_runtime import package


class RustMatchRuntimeTests(unittest.TestCase):
    def test_bad_packages_never_publish_a_ready_native_server(self):
        from games.codol.versions.v3_3_3_3.server.match_server.runtime import load_matchmaking
        with tempfile.TemporaryDirectory() as temp:
            for case in ('capacity','integrity','unready','version'):
                with self.subTest(case=case):
                    path=Path(temp)/case
                    package(path,weapon_capacity=352 if case=='capacity' else 900)
                    if case=='integrity':
                        (path/'weapon-acr.bin').write_bytes(bytes(0xe28))
                    elif case in ('unready','version'):
                        file=path/'manifest.json'
                        manifest=json.loads(file.read_text())
                        manifest['physics_ready' if case=='unready' else 'format_version']=False if case=='unready' else 427
                        file.write_text(json.dumps(manifest))
                    with self.assertRaises((OSError,ValueError,RuntimeError)):
                        load_matchmaking(path,port=0)

    def test_native_startup_exposes_current_map_and_no_python_world(self):
        from games.codol.versions.v3_3_3_3.server.match_server.runtime import load_matchmaking
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'match'
            package(path,'mp_nuked')
            service=load_matchmaking(path,port=0)
            try:
                self.assertEqual(service.map_name,'mp_nuked')
                self.assertEqual(service.options['netconst_checksum'],3852334052)
                self.assertTrue(service.server.is_alive())
                self.assertFalse(hasattr(service,'world'))
            finally:
                service.close()
            self.assertFalse(service.server.is_alive())


if __name__=='__main__':
    unittest.main()

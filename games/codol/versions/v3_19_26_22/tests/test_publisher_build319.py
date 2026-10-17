import unittest
from pathlib import Path
import tempfile
import zlib
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.client import publisher


class PublisherBuildTests(unittest.TestCase):
    def test_git_checkout_newlines_do_not_change_downloads(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            with patch.object(publisher, 'SOURCE', source), patch.object(publisher, 'config_key', return_value=bytes(24)):
                outputs = []
                for newline in (b'\n', b'\r\n'):
                    for name in ('configs_s.ini', 'market_ui.ini'):
                        (source/name).write_bytes(b'[version]'+newline+b'value=319'+newline)
                    outputs.append(publisher.files(b'client', b'playlist'))
                self.assertEqual(outputs[0], outputs[1])

    def test_playlist_changes_only_existing_offline_rules(self):
        original = (b'version 797\r\nrule requireOpenNat 1 \r\nrule party_minlobbytime 60 \r\n'
                    b'playlist 110\nrule party_minplayers 12\nrule party_maxplayers 18\n'
                    b'rule another 12\nname english "Original"\n')
        expected = (b'version 797\r\nrule requireOpenNat 0 \r\nrule party_minlobbytime 10 \r\n'
                    b'playlist 110\nrule party_minplayers 1\nrule party_maxplayers 18\n'
                    b'rule another 12\nname english "Original"\n')
        self.assertEqual(publisher.offline_playlist(original), expected)
        self.assertEqual(publisher.offline_playlist(expected), expected)

    def test_sources_generate_downloads_without_imported_binaries_or_player_state(self):
        key = bytes(range(24))
        with patch.object(publisher, 'config_key', return_value=key):
            files = publisher.files(b'fixture client', b'version 797\nrule party_minplayers 6\n')
        self.assertEqual(zlib.decompress(files['publisher-files/mp_playlists_shipRetail_release.info']),
                         b'version 797\nrule party_minplayers 1\n')
        config = publisher.config_crypt(files['publisher-files/configs_s.info'], key)
        self.assertIn(b'url=http://127.0.0.1:8319/tc-live/${TITLE_ID}/', config)
        self.assertIn(b'[version]', config)
        self.assertIn(b'Local CODOL 3.19', publisher.config_crypt(files['publisher-files/MOTD.info'], key))
        self.assertFalse(any('profile' in name or name.endswith(('.dll', '.exe')) for name in files))
        self.assertEqual(files['match-host/nfs-www/nfs-live/dev/index.json'], b'{"NotForSale": []}\n')

    def test_config_cipher_uses_length_iv_and_handles_non_block_aligned_data(self):
        key = bytes(range(24))
        # AES-192 CTR: LE payload length then 12 bytes of 01, BE counter.
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        import struct
        data = b'[version]\nvalue=319\n'
        encoder = Cipher(algorithms.AES(key), modes.CTR(struct.pack('<I', len(data))+b'\x01'*12)).encryptor()
        expected = encoder.update(data)+encoder.finalize()
        self.assertEqual(publisher.config_crypt(data, key), expected)
        self.assertEqual(publisher.config_crypt(expected, key), data)

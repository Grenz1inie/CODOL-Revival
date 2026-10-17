"""Build offline publisher downloads from source text and the original client."""
from pathlib import Path
import re
import struct
import zlib

import pefile
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .fastfile import keys

SOURCE = Path(__file__).parents[1] / 'resources/publisher'


def config_key(client):
    private, _ = keys(client)
    with pefile.PE(data=client, fast_load=True) as image:
        wrapped = image.get_data(0x9a9708, 256)
    key = private.decrypt(wrapped, padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))
    if len(key) != 24:
        raise ValueError('Invalid 3.19 publisher key')
    return key


def config_crypt(data, key):
    iv = struct.pack('<I', len(data)) + b'\x01' * 12
    encoder = Cipher(algorithms.AES(key), modes.CTR(iv)).encryptor()
    return encoder.update(data) + encoder.finalize()


def offline_playlist(original):
    for name, value in ((b'requireOpenNat', b'0'), (b'party_minlobbytime', b'10'),
                        (b'party_minplayers', b'1')):
        original = re.sub(rb'(?m)^(rule[ \t]+' + name + rb'[ \t]+)\d+(?=[ \t\r]*$)',
                          lambda match: match[1] + value, original)
    return original


def files(client, playlist):
    key = config_key(client)
    motd = '[motd_config]\r\ntype=config\r\nlastupdatetime=1792059077\r\n'
    for category in range(5):
        motd += (f'[motd_{category}]\r\ntype=message\r\ntimestamp=1792059077\r\n'
                 f'category={category}\r\ncaption=Welcome\r\nmessage=Local CODOL 3.19 server.\r\n'
                 'beViewed=1\r\nformat=0\r\nsender=CODOL\r\notherSender=\r\nimagePath=\r\n')
    downloads = {
        'configs_s.info': config_crypt((SOURCE / 'configs_s.ini').read_text(encoding='utf-8').encode('utf-8'), key),
        'MOTD.info': config_crypt(motd.encode('ascii'), key),
        'mp_playlists_shipRetail_release.info': zlib.compress(offline_playlist(playlist)),
        'market_ui.info': zlib.compress((SOURCE / 'market_ui.ini').read_text(encoding='utf-8').encode('utf-8')),
        'daily_challenge_config.info': zlib.compress(b'; Local diagnostic: no daily challenges configured.\n'),
        'activities_v1.info': b'  ',
        'broadcast.info': b'<MSG T=1570255261,P=0/>',
        'market-down.info': b'[Market]\r\nupdate=1\r\nonetimefetch=1\r\nstarttime=1569560400\r\nendtime=1569562200\r\ninterval=600\r\n',
        'tlogconfig.info': b'[TLog]\r\nuiclickcount=0\r\nuiclick=0\r\nuipage=1\r\nuilastpages=0\r\ndwdsmm_number=30\r\ndwdsmm_initvalue=50\r\ndwdsmm_slope=1.9\r\nloadoutchangeevent=0\r\nuipage_limit=30\r\n',
        'whitelist_tester.info': b'[Whitelist]\r\n',
    }
    result = {'publisher-files/' + name: data for name, data in downloads.items()}
    for name in ('tc', 'tc-live'):
        result[f'match-host/nfs-www/{name}/dev/index.json'] = b'{"advertisement": []}\n'
    for name in ('nfs', 'nfs-live'):
        result[f'match-host/nfs-www/{name}/dev/index.json'] = b'{"NotForSale": []}\n'
    return result

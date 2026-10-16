"""Reconstruct the captured menu asset table, cross-check using native x86.

This verifies a capture-specific prediction; it is not yet a live initialized
map checksum and must not be substituted for a different set of loaded assets.
"""
import os
from pathlib import Path
import argparse
import json
import struct
import subprocess
import zlib

ROOT=Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'


def reconstruct(capture):
    assets=capture['assets']
    runtime=sorted((a for a in assets if a['origin']=='runtime'),key=lambda a:a['type'])
    if [a['type'] for a in runtime]!=[20,21,22]:raise ValueError('Runtime NCS lists missing')
    database=[a for a in assets if a['origin']=='database']
    languages=('eng','fra','deu','ita','spa','bri','rus','pol','kor','tai','jpn','chi','tha','let','cze')
    # Native 661980 sorts names with a current-language prefix after others.
    # Current capture contains none for ANY supported language, so no guess
    # about the client's active language is necessary for this ordering.
    if any(a['name'][8:].startswith(tuple(p+'_' for p in languages)) for a in database):
        raise ValueError('Language-prefixed assets require the active language for ordering')
    ordered=runtime+sorted(database,key=lambda a:(a['source'],a['type'],a['name'].lower()))
    rdata=(ROOT.parent/'iips-memory/codoMP_client_shipRetail.exe.9076736.bin').read_bytes()
    ranges=[struct.unpack_from('<III',rdata,0xDA9808-0xCA8000+i*12) for i in range(23)]
    seed=capture['globals']['077db834']['value']
    wire=bytearray(struct.pack('<II',seed,len(ordered)))
    table=bytearray([255])*0x31d9
    values={i:[] for i in range(23)}
    defaults={};checksum=0;nodes=0
    for position,asset in enumerate(ordered):
        if position==3:checksum=seed
        strings=asset['strings']
        if len(strings)!=asset['count'] or any(s is None for s in strings):raise ValueError('Incomplete NCS capture')
        wire+=struct.pack('<III',asset['type'],asset['source'],len(strings))
        wire+=asset['name'].encode('ascii')+b'\0'
        for text in strings:wire+=text.encode('ascii')+b'\0'
        kind=asset['type']
        if kind==15:continue
        # Native 661700 only compares against previous lists, not against
        # other entries within the current list.
        prior=set(values[kind])
        added=[s for s in strings if s not in prior]
        if not added:continue
        base,capacity,offset=ranges[kind]
        if base!=0x31d9 and len(values[kind])+len(added)>capacity-offset:
            raise ValueError('Native NCS range exceeded')
        start=base+offset+len(values[kind]);nodes+=1
        values[kind]+=added
        for i,text in enumerate(added):
            checksum=zlib.crc32(text.encode('ascii'),checksum)
            if base!=0x31d9:
                table[start+i]=kind;defaults[start+i]=text
    return {'predicted_checksum_hex':f'{checksum:08X}','type_table_hex':table.hex(),
            'defaults':defaults,'nodes':nodes,'strings':sum(map(len,values.values())),
            'source':capture['source'],'verified_in_live_initializer':False}, wire


def main():
    ap=argparse.ArgumentParser();ap.add_argument('capture',type=Path);a=ap.parse_args()
    result,wire=reconstruct(json.loads(a.capture.read_text()))
    binary=a.capture.with_suffix('.ncs-input.bin');binary.write_bytes(wire)
    native=subprocess.run([str(ROOT/'mainframe-verification/test_native_ncs319.exe'),
        str(ROOT/'mainframe-verification/config-reader-relocated.bin'),
        str(ROOT.parent/'iips-memory/codoMP_client_shipRetail.exe.9076736.bin'),str(binary)],
        capture_output=True,text=True,timeout=20)
    if native.returncode:raise RuntimeError(native.stdout+native.stderr)
    lines=native.stdout.splitlines();fields=dict(p.split('=') for p in lines[0].split())
    assert fields['checksum'].upper()==result['predicted_checksum_hex'],(fields,result['predicted_checksum_hex'])
    assert lines[1]=='types='+result['type_table_hex']
    assert int(fields['nodes'])==result['nodes']
    assert int(fields['strings'])==result['strings']
    result['verified_against_native_recovered_functions']=True
    output=a.capture.with_suffix('.reconstructed.json');output.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('defaults','type_table_hex')},indent=2))
    print('default indices 0..30:',{k:v for k,v in result['defaults'].items() if k<=30})
    print('saved:',output)

if __name__=='__main__':main()

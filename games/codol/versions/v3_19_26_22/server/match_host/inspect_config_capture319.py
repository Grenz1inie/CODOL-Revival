"""Parse read-only native evidence without treating uninitialized data as valid."""
import argparse
from collections import Counter
import json
from pathlib import Path


def parse_capture(path):
    result={'source':str(path),'globals':{},'assets':[],'registered_dvars':[]}
    current=None
    for line in path.read_text().splitlines():
        fields=dict(part.split('=',1) for part in line.split() if '=' in part)
        if line.startswith('global '):
            result['globals'][fields['address']]={'value':int(fields['value'],16),'readable':fields['readable']=='1'}
        elif line.startswith('type_table_hex='):
            table=bytes.fromhex(fields['type_table_hex'])
            if len(table)!=0x31d9:raise ValueError('Incomplete type table')
            result['type_table_hex']=table.hex()
            result['type_counts']=dict(Counter(table))
        elif line.startswith('asset '):
            current=dict(fields)
            current['name']=bytes.fromhex(fields['name_hex']).decode('ascii','backslashreplace') if fields['name_hex'] not in ('unreadable','overlong') else fields['name_hex']
            current['type']=int(fields['type']);current['source']=int(fields['source']);current['count']=int(fields['count'])
            current['strings']=[]
            result['assets'].append(current)
        elif line.startswith('string ') and current is not None:
            value=fields['hex']
            current['strings'].append(bytes.fromhex(value).decode('ascii','backslashreplace') if value not in ('unreadable','overlong') else None)
        elif line.startswith('registered_dvar '):
            result['registered_dvars'].append({'index':int(fields['index']),'flags':int(fields['flags'],16),
                'name':bytes.fromhex(fields['name_hex']).decode('ascii','backslashreplace')})
        elif line.startswith('database_nodes='):
            result['database_nodes']=int(fields['database_nodes'])
            result['database_assets']=int(fields['assets'])
    flag=result['globals'].get('077db42c',{})
    checksum=result['globals'].get('077d8240',{})
    result['native_table_initialized']=flag.get('readable') and flag.get('value')==1
    result['usable_native_checksum']=bool(result['native_table_initialized'] and checksum.get('readable') and 'type_table_hex' in result)
    if result['usable_native_checksum']:result['checksum_hex']='%08X'%checksum['value']
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('capture',type=Path);a=ap.parse_args()
    result=parse_capture(a.capture)
    output=a.capture.with_suffix('.json');output.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('assets','type_table_hex','registered_dvars')},indent=2))
    print('assets:',[(v['name'],v['type'],v['count']) for v in result['assets']])
    print('saved:',output)

if __name__=='__main__':main()

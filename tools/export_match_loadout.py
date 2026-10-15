"""Bundle the current rifle header and reference waypoints for the independent match.

The output owns its bytes; neither the old source tree nor its executable is a
runtime dependency. A candidate NCS registry stays a candidate after this step.
"""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from export_match_map import OUTPUT_ROOT, read_ncs_prefix_block3, read_block3_string
from index_story_zone import read_assets
from match_server.loadout import read_weapon
from match_server.mapdata import load_map
from match_server.navigation import Navigation


def export_loadout(source, output, common_zone, waypoints, registration):
    package=load_map(source)
    registration=Path(registration)
    ncs_bytes=(registration/'ncs.json').read_bytes()
    sources_bytes=(registration/'sources.json').read_bytes()
    ncs=json.loads(ncs_bytes)
    sources=json.loads(sources_bytes)
    map_name = package['manifest']['map']
    required_zones = {map_name, map_name + '_const', map_name + '_load'}
    if not required_zones.issubset(ncs['selected_zones']):
        raise ValueError('registration does not include the selected map')
    output=Path(output).resolve()
    if output==OUTPUT_ROOT.resolve() or not output.is_relative_to(OUTPUT_ROOT.resolve()) or output.exists():
        raise ValueError('choose a new directory under independent-match')
    zone=Path(common_zone).read_bytes()
    zone_hash=hashlib.sha256(zone).hexdigest()
    inputs={row['name']:row['zone_sha256'] for row in package['manifest']['inputs']}
    if any(row['name'] in inputs and row['zone_sha256']!=inputs[row['name']]
           for row in sources['fastfiles']):
        raise ValueError('registration zones differ from map package')
    if zone_hash!=inputs.get('common_mp'):
        raise ValueError('weapon zone does not match current map package')
    prefix=read_ncs_prefix_block3(zone)
    matches=[]
    for asset_index,(kind,data) in enumerate(read_assets(zone)):
        if kind!=28 or len(data)<0xe28:
            continue
        reference,=struct.unpack_from('<I',data)
        if reference==0xffffffff:
            name=data[0xe28:data.index(0,0xe28)].decode('ascii')
        elif (reference-1)>>28==3 and (reference-1)&0xfffffff < len(prefix):
            name=read_block3_string(prefix,reference)
        else:
            continue  # Unselected names need not trigger full weapon replay.
        if name=='acr_mp':
            matches.append((asset_index,data[:0xe28]))
    if len(matches)!=1:
        raise ValueError('current acr_mp definition missing or ambiguous')
    asset_index,header=matches[0]
    registry=ncs['registry']['kinds']
    def resource(kind,name):
        row=registry[str(kind)]
        return dict(name=name,index=row['reserved']+row['strings'].index(name))
    weapon=resource(13,'acr_mp')
    weapon['header']='weapon-acr.bin'
    parameters=read_weapon(header,index=weapon['index'])
    navigation=Path(waypoints).read_bytes()
    Navigation.from_csv(navigation.decode('ascii'),None)  # Format only; edges are checked against geometry at runtime.
    loadout=dict(weapon=weapon,body=resource(0,'mp_fullbody_juggernaut_explosive_so'),
        hands=resource(0,'viewhands_player_tf141'),parameters=asdict(parameters),
        provenance=dict(format_version=423,zone='common_mp',zone_sha256=zone_hash,
            asset_index=asset_index,weapon_header_sha256=hashlib.sha256(header).hexdigest(),
            waypoint_sha256=hashlib.sha256(navigation).hexdigest(),
            waypoint_source=str(Path(waypoints).resolve()),
            waypoint_status='reference graph; every used edge requires current collision clearance'))
    files=dict(package['files'])
    files.update({'ncs.json':ncs_bytes,'registration-sources.json':sources_bytes,
                  'weapon-acr.bin':header,'waypoints.csv':navigation,
                  'loadout.json':(json.dumps(loadout,indent=2)+'\n').encode()})
    manifest=dict(package['manifest'])
    manifest['inputs']=list({row['name']:row for row in
                            [*manifest['inputs'],*sources['fastfiles']]}.values())
    manifest['ncs_status']=ncs['status']
    manifest['files']={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
                       for name,data in files.items()}
    manifest['loadout']='loadout.json'
    output.mkdir(parents=True)
    for name,data in files.items():
        destination=output/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(data)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for argument in ('source','output','common-zone','waypoints','registration'):
        parser.add_argument('--'+argument,type=Path,required=True)
    args=parser.parse_args()
    manifest=export_loadout(args.source,args.output,args.common_zone,args.waypoints,args.registration)
    print(json.dumps(dict(output=str(args.output.resolve()),map=manifest['map'],
                          files=len(manifest['files']),physics_ready=manifest['physics_ready'])))

"""Names consumed by 3.19 room creation, not the publisher's old dvar names."""
import re
import zlib


def nuketown_rules(data):
    source = zlib.decompress(data)
    lines = []
    nuketown = False
    names = {b'party_minplayers': b'1011', b'party_maxplayers': b'3265'}
    for line in source.splitlines(keepends=True):
        header = re.match(rb'^\s*playlist\s+(\d+)\b', line)
        if header:
            nuketown = header[1] == b'110'
        if nuketown:
            line = re.sub(rb'^(\s*rule\s+)(party_minplayers|party_maxplayers)(?=\s)',
                          lambda match: match[1] + names[match[2]], line)
        lines.append(line)
    result = b''.join(lines)
    return data if result == source else zlib.compress(result)

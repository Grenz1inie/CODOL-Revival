"""Bounded offline execution of the SHA-verified FF423 client's loader/registrar.

No process is launched. Loader DB queries/queue and snprintf are seams; loader
branching is original machine code. Full registration executes original seed,
sort, dedup, CRC and final chain checks using supplied DB/dvar inputs. Neither
result establishes which archives are mounted in a live client.
"""
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from client_reader423 import ClientReader423
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESI,
    UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_EDI)
from story_netconst423 import build_registry


class RegistrationProbe:
    def __init__(self):
        self.reader = ClientReader423()  # Verifies the complete client SHA-256.
        self.cpu = self.reader.cpu
        self.cpu.mem_map(0x32000000, 0x400000)
        self.heap = 0x32000000

    def alloc(self, data):
        address = self.heap
        self.cpu.mem_write(address, data)
        self.heap += (len(data) + 7) & ~7
        return address

    def text(self, address):
        return bytes(self.cpu.mem_read(address, 256)).split(b'\0', 1)[0].decode('ascii')

    def words(self, address, count):
        return struct.unpack('<' + 'I' * count, self.cpu.mem_read(address, count * 4))

    def ret(self, value=0):
        sp = self.cpu.reg_read(UC_X86_REG_ESP)
        self.cpu.reg_write(UC_X86_REG_EAX, value)
        self.cpu.reg_write(UC_X86_REG_EIP, self.words(sp, 1)[0])
        self.cpu.reg_write(UC_X86_REG_ESP, sp + 4)

    def call(self, address, *args):
        stack, end = 0x303ff000, 0x303ffff0
        self.cpu.mem_write(stack, struct.pack('<' + 'I' * (1 + len(args)), end, *args))
        self.cpu.reg_write(UC_X86_REG_ESP, stack)
        self.cpu.emu_start(address, end, count=30000000)
        if self.cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError(f'client probe did not return: {address:#x}')
        return self.cpu.reg_read(UC_X86_REG_EAX)

    def zone_plan(self, mapname, category, *, mounted=()):
        return [r['name'] for r in self.zone_records('map', mapname, category,
                mounted=mounted) if r['name']]

    def zone_records(self, phase, mapname='mp_killhouse_sh', category='mp', *, mounted=(), flags=0):
        """Execute 49fe30/49fd70; mounted set supplied, no gametype CSV override.

        The addon zone uses the category fallback when coGameTypesTable is absent.
        This is a requested archive list, not proof any requested file exists.
        """
        result, hooks = [], []
        def boundary(cpu, address, size, context):
            sp = cpu.reg_read(UC_X86_REG_ESP)
            if address == 0x4a0820:
                self.ret(int(self.text(self.words(sp + 4, 1)[0]) in mounted))
            elif address == 0x637be0:
                dest, capacity, fmt, arg = self.words(sp + 4, 4)
                pattern = self.text(fmt)
                count = pattern.count('%s')
                if not 1 <= count <= 3 or '%' in pattern.replace('%s', ''):
                    raise ValueError('unexpected loader format: ' + pattern)
                values = tuple(self.text(p) for p in self.words(sp + 16, count))
                data = (pattern % values).encode('ascii')
                cpu.mem_write(dest, data[:capacity - 1] + b'\0')
                self.ret(len(data))
            elif address == 0x49f960:
                records, count, sync = self.words(sp + 4, 3)
                for i in range(count):
                    name, alloc, free = self.words(records + i * 12, 3)
                    result.append(dict(name=self.text(name) if name else None,
                                       alloc=alloc, free=free, sync=sync))
                self.ret()
            else:
                # Progress reporting (484c60), or absent optional CSV (49e7d0).
                self.ret()
        for va in (0x484c60, 0x4a0820, 0x637be0, 0x49f960, 0x49e7d0, 0x5664a0, 0x4a0f80):
            hooks.append(self.cpu.hook_add(UC_HOOK_CODE, boundary, begin=va, end=va))
        try:
            self.cpu.reg_write(UC_X86_REG_ECX, self.alloc(category.encode() + b'\0'))
            self.cpu.mem_write(0x1ad9244, struct.pack('<I', flags))
            map_ptr = self.alloc(mapname.encode() + b'\0')
            self.cpu.reg_write(UC_X86_REG_EDI, map_ptr)
            self.call({'map': 0x49fe30, 'frontend': 0x59c180, 'loadscreen': 0x4651b0}[phase], map_ptr)
            return result
        finally:
            for hook in hooks:
                self.cpu.hook_del(hook)

    def db_events(self, ready):
        """Windows event seam only; execute the client's readiness decisions."""
        stub = self.alloc(b'\xb8' + struct.pack('<I', 0 if ready else 258) + b'\xc2\x08\x00')
        self.cpu.mem_write(0xb5b14c, struct.pack('<I', stub))
        self.cpu.mem_write(0x2f24554, struct.pack('<I', 1))

    def loading_message(self, *, db_ready):
        """Accepted OOB branch 467056..4670aa; real line reader/local queue/reset.

        Address/token admission and rendering/DB execution are outside this seam.
        The fixture starts after the OOB command line has already been consumed.
        """
        cpu, frame, conn = self.cpu, 0x303fe000, 0x30100000
        command = self.alloc(bytes(1024))
        cpu.mem_write(0x2e1437c, struct.pack('<3I', command, 1024, 0))
        lock = self.alloc(b'\xc2\x04\x00')
        for va in (0xb5b180, 0xb5b174):
            cpu.mem_write(va, struct.pack('<I', lock))
        self.db_events(db_ready)
        cpu.mem_write(0x1a2e7ec, struct.pack('<I', 7))
        cpu.mem_write(0x1a2a538, struct.pack('<I', conn ^ 0xd362501f))
        original = bytes([0x5a]) * 0xa2000
        cpu.mem_write(conn, original)
        cpu.mem_write(0x2df9934, struct.pack('<I', 1))
        body = b'mp_killhouse_sh\nmp\n'
        data = self.alloc(body)
        msg = self.alloc(struct.pack('<12I', 0, 1, data, 0, len(body), len(body), 0, 0, 0, 0, 0, 0))
        cpu.mem_write(frame - 0x458, struct.pack('<I', 0))
        cpu.mem_write(frame - 0x450, struct.pack('<I', msg))
        result, hooks = {}, []
        def boundary(cpu, address, size, context):
            if address == 0x46a450:
                result.update(map=self.text(cpu.reg_read(UC_X86_REG_ESI)),
                    category=self.text(self.words(cpu.reg_read(UC_X86_REG_ESP) + 4, 1)[0]))
            self.ret()
        for va in (0x6098d0, 0x46a450, 0x4704c0):
            hooks.append(cpu.hook_add(UC_HOOK_CODE, boundary, begin=va, end=va))
        try:
            cpu.reg_write(UC_X86_REG_EBP, frame)
            cpu.reg_write(UC_X86_REG_ESP, frame - 0x500)
            cpu.emu_start(0x467056, 0x4670aa, count=100000)
            if cpu.reg_read(UC_X86_REG_EIP) != 0x4670aa:
                raise ValueError('loadingnewmap branch did not finish')
            result.update(command=self.text(command), state=self.words(0x1a2e7ec, 1)[0],
                registered=self.words(0x2df9934, 1)[0],
                connection_unchanged=bytes(cpu.mem_read(conn, len(original))) == original)
            return result
        finally:
            for hook in hooks:
                cpu.hook_del(hook)

    def heartbeat_response(self, *, db_ready):
        """Accepted state-6 branch; real event checks and state setter."""
        cpu, conn = self.cpu, 0x30100000
        self.db_events(db_ready)
        cpu.mem_write(0x1a2e7ec, struct.pack('<I', 6))
        cpu.mem_write(0x1a2a538, struct.pack('<I', conn ^ 0xd362501f))
        cpu.reg_write(UC_X86_REG_EBX, 0)
        cpu.reg_write(UC_X86_REG_ESP, 0x303ff000)
        cpu.emu_start(0x466c81, 0x466d62, count=100000)
        if cpu.reg_read(UC_X86_REG_EIP) != 0x466d62:
            raise ValueError('heartbeatresponse branch did not finish')
        return self.words(0x1a2e7ec, 1)[0]

    def register(self, tables, seed):
        """Actual 584ed0 + 584d80 + 681a80; no CRC/compare bypass."""
        ordered = build_registry(tables, checksum_seed=seed)['table_order']
        by_name = {t['name']: t for t in tables}
        # Initial zero registry, with the independently measured dvar-name seed.
        self.cpu.mem_write(0x2df7ce8, bytes(0x168))
        self.cpu.mem_write(0x2df9938, bytes(0x400))
        self.cpu.mem_write(0x2df7d90, struct.pack('<I', seed))
        for name in ordered:
            t = by_name[name]
            pointers = [self.alloc(s.encode('ascii') + b'\0') for s in t['strings']]
            array = self.alloc(struct.pack('<' + 'I' * len(pointers), *pointers) or bytes(4))
            header = self.alloc(struct.pack('<5I', self.alloc(name.encode() + b'\0'),
                t['type'], t['source'], len(pointers), array))
            self.cpu.reg_write(UC_X86_REG_ESI, header)
            if self.call(0x584ed0) != 1:
                raise ValueError('client rejected registration: ' + name)
        return self.words(0x2df7d90, 1)[0]

    def build_registration(self, tables, registration):
        """5850b0 including native qsort/comparator and final validity checks.

        DB assets and the measured dvar names/flags are input seams. This
        proves the supplied complete set, not successful asynchronous FF loads.
        """
        cpu, headers, hooks = self.cpu, {}, []
        for t in tables:
            pointers = [self.alloc(s.encode('ascii') + b'\0') for s in t['strings']]
            array = self.alloc(struct.pack('<' + 'I' * len(pointers), *pointers) or bytes(4))
            headers[t['name']] = self.alloc(struct.pack('<5I',
                self.alloc(t['name'].encode() + b'\0'), t['type'], t['source'], len(pointers), array))
        language = self.alloc(struct.pack('<4I', 0, 0, 0, 11))  # Chinese build language.
        cpu.mem_write(0x315fbec, struct.pack('<I', language))
        dvars = [self.alloc(struct.pack('<2I', self.alloc(name.encode() + b'\0'),
                 8 if name in registration['codinfo_names'] else 0)) for name in registration['names']]
        cpu.mem_write(0x2dfaba4, struct.pack('<I', len(dvars)))
        cpu.mem_write(0x2dfaba8, struct.pack('<' + 'I' * len(dvars), *dvars))
        # No separate type-19 names in the input capture. It is not a required
        # final chain and its CRC is replaced by the all-network-dvar seed.
        cpu.mem_write(0x2dfaba0, bytes(4))
        self.call(0x5855d0)
        if self.words(0x2df9d38, 1)[0] != registration['checksum_seed']:
            raise ValueError('native dvar seed mismatch')
        def boundary(cpu, address, size, context):
            sp = cpu.reg_read(UC_X86_REG_ESP)
            if address == 0x49ec50:
                kind, name = self.words(sp + 4, 2)
                if kind != 44 or self.text(name) not in headers:
                    raise ValueError('missing required level NCS: ' + self.text(name))
                self.ret(headers[self.text(name)])
            elif address == 0x49ed90:
                cpu.mem_write(cpu.reg_read(UC_X86_REG_EDI), struct.pack('<' + 'I' * len(headers), *headers.values()))
                self.ret(len(headers))
            else:
                dest, capacity, fmt = self.words(sp + 4, 3)
                pattern = self.text(fmt)
                args = tuple(self.text(p) for p in self.words(sp + 16, pattern.count('%s')))
                data = (pattern % args).encode('ascii')
                cpu.mem_write(dest, data[:capacity - 1] + b'\0')
                self.ret(len(data))
        for va in (0x49ec50, 0x49ed90, 0x637be0):
            hooks.append(cpu.hook_add(UC_HOOK_CODE, boundary, begin=va, end=va))
        try:
            self.call(0x584be0)
            self.call(0x5850b0)
            return dict(checksum=self.words(0x2df7d90, 1)[0], registered=self.words(0x2df9934, 1)[0])
        finally:
            for hook in hooks:
                cpu.hook_del(hook)

    def preload(self, mapname, category):
        """Run loadingnewmap's 46a4f0 target, stop at its zone-load boundary.

        Network dispatcher framing/address checks are not emulated here.
        The registry reset itself executes, along with the preload flag writes.
        """
        result, hooks = {}, []
        def boundary(cpu, address, size, context):
            if address == 0x46a450:
                result.update(map=self.text(cpu.reg_read(UC_X86_REG_ESI)),
                    category=self.text(self.words(cpu.reg_read(UC_X86_REG_ESP) + 4, 1)[0]))
            self.ret()
        for va in (0x6098d0, 0x46a450, 0x4704c0):
            hooks.append(self.cpu.hook_add(UC_HOOK_CODE, boundary, begin=va, end=va))
        try:
            self.cpu.mem_write(0x2df9934, struct.pack('<I', 1))
            self.cpu.reg_write(UC_X86_REG_ESI, self.alloc(mapname.encode() + b'\0'))
            self.call(0x46a4f0, self.alloc(category.encode() + b'\0'))
            result['flags'] = [self.cpu.mem_read(va, 1)[0] for va in (0x17cd282, 0x1a2e7e0, 0x17cd27e)]
            result['registered'] = self.words(0x2df9934, 1)[0]
            return result
        finally:
            for hook in hooks:
                self.cpu.hook_del(hook)


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ncs', type=Path, required=True)
    parser.add_argument('--category', default='mp')
    args = parser.parse_args()
    data = json.loads(args.ncs.read_text())
    selected = data['tables']
    registration = data.get('registration_evidence', {})
    phases = {'candidate_all': selected,
              'candidate_without_map': [t for t in selected if not t['zone'].startswith('mp_killhouse_sh')]}
    print(json.dumps(dict(
        checksums={name: RegistrationProbe().register(tables, data['checksum_seed']) for name, tables in phases.items()},
        requested_zones=RegistrationProbe().zone_plan('mp_killhouse_sh', args.category),
        loader_records={phase: RegistrationProbe().zone_records(phase, category=args.category,
            flags=3 if phase != 'frontend' else 0) for phase in ('frontend', 'loadscreen', 'map')},
        complete_registration=(RegistrationProbe().build_registration(selected, registration)
            if 'codinfo_names' in registration else None),
        loading_message={str(ready): RegistrationProbe().loading_message(db_ready=ready) for ready in (False, True)},
        heartbeat_response={str(ready): RegistrationProbe().heartbeat_response(db_ready=ready) for ready in (False, True)},
        preload=RegistrationProbe().preload('mp_killhouse_sh', args.category),
        mounted_set_verified=False,
        limitation='CRC verified for supplied tables only; requested zones and mounted DB assets are distinct'), indent=2))

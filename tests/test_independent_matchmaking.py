import base64
import struct
import unittest

from client_matchmaking423 import ClientMatchmaking423
import test_match_world as fixture


def message(recipient,text):
    data=text.encode('ascii')
    return b'\x0a'+struct.pack('<Q',recipient)+b'\x13\x08'+struct.pack('<II',len(data)+4,len(data))+data+b'\0'


class IndependentMatchmakingTests(unittest.TestCase):
    def test_nuketown_accepts_fixed_playlist_rotation_and_rejects_other_maps(self):
        from match_server.matchmaking import IndependentMatchmaking
        service=IndependentMatchmaking(fixture.MatchWorldTests().world(),netconst_checksum=55,
                                      map_name='mp_nuked',port=0)
        try:
            service.find(1,bytes.fromhex('08010000000800000000080a000000079b1ff0d600'))
            start='mmstart sv_resetServer; 2486 1; 3265 2; 2489 0; playlist 110; start_map_rotate_once 2'
            self.assertIsNone(service.message(1,message(service.server_id,start)))
            self.assertIsNone(service.message(1,message(service.server_id,'mmstart g_gametype dm; map mp_nuked')))
            for invalid in (start.replace('playlist 110','playlist 0'),
                            start.replace('playlist 110','playlist 240'),
                            start.replace('start_map_rotate_once 2','start_map_rotate_once -1'),
                            start+'; map mp_killhouse_sh',
                            'mmstart g_gametype cha; map mp_nuked',
                            'mmstart map mp_nuked; map mp_killhouse_sh'):
                with self.subTest(command=invalid),self.assertRaises(ValueError):
                    service.message(1,message(service.server_id,invalid))
        finally:
            service.close()

    def test_live_independent_endpoint_is_published_and_room_is_bound_to_killhouse(self):
        from match_server.matchmaking import IndependentMatchmaking
        service=IndependentMatchmaking(fixture.MatchWorldTests().world(),netconst_checksum=55,port=0)
        reader=ClientMatchmaking423()
        query=bytes.fromhex('08010000000800000000080a000000079b1ff0d600')
        uid=0x1234567812345678
        try:
            candidate,=service.find(uid,query)
            self.assertTrue(service.server.thread.is_alive())
            ok,state,_=reader.candidate(candidate)
            self.assertTrue(ok)
            self.assertEqual(struct.unpack_from('<H',state,0x1c)[0],service.server.port)
            text=f'mmbook 1 {base64.b64encode(service.security_id).decode()} 1'
            reply=service.message(uid,message(service.server_id,text))
            self.assertEqual(reader.booking_push(reply),(service.server_id,b'mmbook accepted'))
            self.assertIsNone(service.message(uid,message(service.server_id,'mmstart set g_gametype dm;map mp_killhouse_sh')))
            with self.assertRaises(ValueError):
                service.message(uid,message(service.server_id,'mmstart map mp_cargoship'))
            with self.assertRaises(ValueError):
                service.find(uid+1,query)
            with self.assertRaises(ValueError):
                service.message(uid+1,message(service.server_id,text))
            with self.assertRaises(ValueError):
                service.message(uid,message(service.server_id,text.replace('mmbook 1','mmbook -1')))
            service.server.close()
            self.assertEqual(service.find(uid,query),())
        finally:
            service.close()

    def test_invalid_query_never_creates_or_publishes_a_socket(self):
        from match_server.matchmaking import IndependentMatchmaking
        service=IndependentMatchmaking(fixture.MatchWorldTests().world(),netconst_checksum=55,port=0)
        with self.assertRaises(ValueError):
            service.find(1,b'invalid')
        self.assertIsNone(service.server)
        service.close()


if __name__=='__main__':
    unittest.main()

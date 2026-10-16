"""Loopback-only 3.19 lobby greeting research. No remote service connections."""
from pathlib import Path
import os
import socket,struct,json,time,hashlib,hmac,sys,threading
root=Path(os.environ['CODOL319_SERVER_ROOT'])
sys.path.insert(0,str(root))
from lsg_codec import decode,encode,empty_task_reply,empty_task_reply_total
if "--reply-total" in sys.argv: empty_task_reply=empty_task_reply_total
import local_profile319
from playlist319 import nuketown_rules
from room319 import Room, native_manifest
def emit(event,**values):
    with (root/'lsg-handshake.jsonl').open('a',encoding='utf-8') as out:out.write(json.dumps(dict(event=event,time=time.time(),**values))+'\n')
def exact(c,n):
    data=b''
    while len(data)<n:
        part=c.recv(n-len(data))
        if not part:raise EOFError('Client closed the connection')
        data+=part
    return data
s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',31901));s.listen(4);s.settimeout(1)
emit('listening',port=31901)
# Runs until stopped (the old 2-hour limit cut off logins mid-launch); --lifetime N restores a limit.
AYRIA_PARITY={4,11,21,28,68,102,139}
deadline=time.monotonic()+(float(sys.argv[sys.argv.index("--lifetime")+1]) if "--lifetime" in sys.argv else float("inf"))
while time.monotonic()<deadline:
    try:c,peer=s.accept()
    except TimeoutError:continue
    with c:
        c.settimeout(90)
        try:
            hello=exact(c,28);emit('client_hello',hex=hello.hex(),peer=peer)
            assert struct.unpack_from('<4I',hello)==(200,200,210,220)
            payload=b'\xab\x81'+struct.pack('<I',210)+b'Local319'+bytes(8)
            greeting=struct.pack('<I',len(payload))+payload
            c.sendall(greeting);emit('server_greeting',hex=greeting.hex())
            length=struct.unpack('<I',exact(c,4))[0]
            if not 1<=length<=65536:raise ValueError('Invalid client frame length '+str(length))
            reply=exact(c,length);emit('client_auth_frame',bytes=length,hex=reply.hex())
            assert reply[:2]==b'\xab\x82'
            framed=struct.pack('<I',len(reply))+reply
            transcript=hello[8:]+greeting+framed[:-8]
            prk=hmac.new(hashlib.sha1(transcript).digest(),b'Local319DiagnosticKey123',hashlib.sha1).digest()
            challenges=hmac.new(prk,b'CLIENTCHAL\x01',hashlib.sha1).digest()[:16]
            assert reply[-8:]==challenges[:8], 'Client proof does not match the reconstructed transcript'
            confirmation=b'\xab\x83'+challenges[8:]
            c.sendall(struct.pack('<I',len(confirmation))+confirmation)
            emit('server_confirmation',hex=confirmation.hex(),client_proof_verified=True)
            keys=b'';previous=b''
            for i in range(1,5):
                previous=hmac.new(prk,previous+b'BDDATA'+bytes([i]),hashlib.sha1).digest();keys+=previous
            emit('synthetic_session_keys',hex=keys[:72].hex())
            server_sequence=1
            assigned=encode(4,b'\x0a'+struct.pack('<Q',1),keys,server_sequence)
            c.sendall(assigned);emit('assigned_connection_id',connection_id=1,bytes=len(assigned))
            server_sequence+=1
            request_number=0
            room = Room(local_profile319.UID, lambda roster=None:
                native_manifest(local_profile319.UID, local_profile319.player_name(), roster))
            # --wake: send an empty keepalive frame every 0.5 s so the client's network loop wakes
            # (experiment for the fixed 18 s gaps between its login request bursts).
            send_lock=threading.Lock();alive=[True]
            def waker(conn=c):
                while alive[0]:
                    time.sleep(0.5)
                    try:
                        with send_lock:conn.sendall(bytes(4))
                    except OSError:break
            if '--wake' in sys.argv:threading.Thread(target=waker,daemon=True).start()
            while time.monotonic()<deadline:
                length=struct.unpack('<I',exact(c,4))[0]
                if length==0:
                    with send_lock:c.sendall(bytes(4))
                    emit('keepalive_reply');continue
                if not 1<=length<=65536:raise ValueError('Invalid post-login frame size '+str(length))
                packet=exact(c,length);emit('post_login_frame',bytes=length,hex=packet.hex())
                kind,body=decode(packet,keys)
                emit('decoded_message',kind=kind,hex=body.hex())
                if kind==0x86 and len(body)>=3 and body[1]==3:
                    service,task=body[0],body[2]
                    request_number+=1
                    # --txn-zero: reply with transaction ID 0 (immediate result) instead of our counter;
                    # experiment for the fixed 18 s waits between login bursts.
                    txn=0 if '--txn-zero' in sys.argv else request_number
                    emit('service_request',service=service,task=task)
                    previous_room = (room.phase, room.observed_count)
                    room_reply, room_pushes = room.handle(body, txn)
                    if (room.phase, room.observed_count) != previous_room:
                        emit('room_state',phase=room.phase,channel=room.channel,observed_count=room.observed_count,
                             players=[{key: p[key] for key in ('uid','name','team','slot')} for p in room.players])
                    # Room "Ready": the room member update (11:4) the client sends when Ready is pressed
                    # carries member flags 80 08 (seen on every Ready press). autoarm319.sh (room mode)
                    # starts the match on this event.
                    if room.phase == 'idle' and (service,task)==(11,4) and bytes.fromhex('020200000008000000800800') in body:
                        emit('room_ready')
                    # --ayria-parity: like the Ayria AlwaysOffline emulator, answer the room/matchmaking
                    # (11, 21, 28), stats (4), presence (68), chat (102) and 139 services with an empty
                    # success instead of "unsupported" (error 2), so the room screens open.
                    if service in {3,6,8,9,10,12,29,71,80,93} or ('--ayria-parity' in sys.argv and service in AYRIA_PARITY):
                        error=1000 if service==10 else (2 if '--fail-catalog' in sys.argv and service==80 and task==107 else 0)
                        response=empty_task_reply(task,txn,error)
                        # PROFILE_MGMT: keep the player's public info so onboarding runs only once.
                        if service==8 and task==3:
                            local_profile319.save_public_info(local_profile319.UID,body[3:])
                            emit('profile_saved',uid=local_profile319.UID,bytes=len(body)-3)
                        elif service==8 and task==1:
                            uids=local_profile319.read_request_uids(body)
                            response,count=local_profile319.public_info_reply(task,txn,uids,'--profile-no-entity' not in sys.argv)
                            emit('profile_read',uids=uids,results=count)
                        elif service==8 and task==2 and '--no-secure-profile' not in sys.argv:  # secure data + 36 replicated fields (secure_fields319.json); level verified in memory 11:12
                            # Private info = secure player data (experience/prestige -> level).
                            response=local_profile319.private_info_reply(task,txn,with_entity='--profile-no-entity' not in sys.argv)
                            emit('secure_profile_read',experience=local_profile319.profile_settings().get('experience',local_profile319.LEVEL70_XP))
                        # Marketplace: unlimited balance (getBalance 130) and successful purchases
                        # (purchaseSKU 154, recorded). --wallet-layout X picks the result encoding.
                        # 3.3.3.3 fetches the balance as a pair (00A4A930): 80/130 and 93/131 fill two
                        # wallet objects of one class; the UI updates when both complete.
                        # --wallet-rotate cycles result variants per 80/130 request (variant logged).
                        # Purchases (93/131 with an item id) are recorded as owned (permanent); the
                        # inventory (80/203) serves them. --inventory-keyed adds the u64+string key.
                        if (service,task)==(93,131):
                            bought=local_profile319.purchase_item_id(body)
                            if bought:
                                # The id is a shop SKU: charge its price, own exactly its items (sku-items319.txt).
                                granted,result=local_profile319.buy_sku(bought)
                                emit('item_owned',sku=bought,items=granted,result=result,wallet=local_profile319.wallet())
                        if (service,task)==(80,230):
                            response=local_profile319.player_assets_reply(task,txn)
                            emit('player_assets_reply',items=len(local_profile319.owned_items()),bytes=len(response))
                        elif (service,task)==(80,203):
                            if '--own-appearance' in sys.argv:
                                response,count=local_profile319.inventory_reply_ids(task,txn,local_profile319.appearance_items()+local_profile319.owned_items(),'--inventory-keyed' in sys.argv)
                            elif '--own-everything' in sys.argv:
                                response,count=local_profile319.inventory_reply_all(task,txn,'--inventory-keyed' in sys.argv)
                            else:
                                response=local_profile319.inventory_reply(task,txn,'--inventory-keyed' in sys.argv);count=len(local_profile319.owned_items())
                            emit('inventory_reply',items=count,bytes=len(response))
                        if (service,task) in ((80,130),(93,131)) and '--no-wallet' not in sys.argv:
                            if '--wallet-rotate' in sys.argv:
                                if (service,task)==(80,130):
                                    wallet_variant=globals().get('wallet_variant',-1)+1
                                variant=local_profile319.WALLET_VARIANTS[globals().get('wallet_variant',0)%len(local_profile319.WALLET_VARIANTS)]
                            else:
                                # 3.3.3.3 005E28D0: GP/CP read from wallet slots by currency byte 1/2;
                                # 93/131 fills one slot (single result), 80/130 the array.
                                variant=('G',10,1) if service==80 else ('G',1,1)
                            response=local_profile319.wallet_reply(task,txn,*variant)
                            emit('wallet_reply',service=service,variant=list(variant),request=body.hex())
                        elif service==80 and task==154:
                            local_profile319.record_purchase(body)
                            bought=local_profile319.purchase_item_id(body)
                            if bought:
                                granted,result=local_profile319.buy_sku(bought)
                                emit('item_owned',sku=bought,items=granted,result=result,wallet=local_profile319.wallet())
                            response=empty_task_reply(task,txn,0)
                            emit('purchase_recorded',request=body.hex())
                        if service==10 and task==21 and body[3:4]==b'\x10':
                            context_end=body.index(b'\0',4)
                            assert body[context_end+1:context_end+2]==b'\x10', 'Publisher filename string tag missing'
                            filename=body[context_end+2:].split(b'\0',1)[0].decode('ascii','strict')
                            # Any publisher file present in publisher-files/ (plain names only); the extra
                            # Ayria-parity files: activities_v1, broadcast, tlogconfig, market-down, whitelist_tester.
                            if filename.endswith('.info') and '/' not in filename and chr(92) not in filename and not filename.startswith('.') and (root/'publisher-files'/filename).is_file():
                                data=(root/'publisher-files'/filename).read_bytes()
                                if filename == 'mp_playlists_shipRetail_release.info':
                                    data = nuketown_rules(data)
                                error=0
                                response=(b'\x0a'+struct.pack("<Q",txn)+b'\x08'+struct.pack('<I',0)+b'\x03'+bytes([task])+b'\x08'+struct.pack('<I',1)+b'\x08'+struct.pack('<I',1)+b'\x13\x08'+struct.pack('<I',len(data))+data)
                                emit('publisher_file_reply',filename=filename,content_bytes=len(data),source='native 3.19 embedded playlist' if filename.startswith('mp_playlists') else 'diagnostic local config with native defaults')
                        if room_reply is not None:
                            response = room_reply
                        reply=encode(1,response,keys,server_sequence)
                        server_sequence+=1
                        with send_lock:c.sendall(reply)
                        emit('local_task_reply',service=service,task=task,error=error,bytes=len(reply))
                        for push in room_pushes:
                            reply = encode(2, push, keys, server_sequence)
                            server_sequence += 1
                            with send_lock:c.sendall(reply)
                    else:
                        reply=encode(1,empty_task_reply(task,txn,2),keys,server_sequence)
                        server_sequence+=1
                        with send_lock:c.sendall(reply)
                        emit('unsupported_task_reply',service=service,task=task,error=2)
        except (OSError,EOFError,ValueError,AssertionError) as ex:emit('error',message=str(ex))
        finally:
            if 'alive' in dir():alive[0]=False
s.close();emit('stopped')

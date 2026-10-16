use codol_match::runtime::read_weapon;

fn header()->Vec<u8> {
    let mut h=vec![0;0xe28];
    for (o,v) in [(0xd08,36u32),(0xd10,90),(0x71c,2000),(0x728,2500),(0x6dc,30),(0xbc8,22)] {
        h[o..o+4].copy_from_slice(&v.to_le_bytes());
    }
    h[0xbcc..0xbd0].copy_from_slice(&1500f32.to_le_bytes());
    h[0xbe0..0xbe4].copy_from_slice(&1501f32.to_le_bytes());
    h
}
#[test]
fn rifle_fields_keep_base_ammo_and_reject_unsupported_or_invalid_headers() {
    let mut h=header();
    let w=read_weapon(&h,5).unwrap();
    assert_eq!((w.index,w.clip_type,w.ammo_type,w.clip_size,w.fire_ms),(5,5,5,36,90));
    assert!(read_weapon(&h,0).is_err());
    assert!(read_weapon(&h[..h.len()-1],5).is_err());
    h[0xd68]=1;assert!(read_weapon(&h,5).is_err());h[0xd68]=0;
    h[0xbb8]=1;assert!(read_weapon(&h,5).is_err());h[0xbb8]=0;
    h[0xbe0..0xbe4].copy_from_slice(&f32::NAN.to_le_bytes());
    assert!(read_weapon(&h,5).is_err());
}

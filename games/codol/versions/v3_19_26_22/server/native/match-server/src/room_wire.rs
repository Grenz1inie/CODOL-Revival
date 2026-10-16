use crate::{Player, Team};

// 3.19 native 0x623880 -> 0x623de0. Unknown fields retain the native
// constructor defaults for bots and the supplied client values for the human.
const FIELDS: &[(usize, usize)] = &[
    (0, 64), (0x88, 8), (0x90, 1), (0x94, 16), (0x96, 16),
    (0x98, 8), (0x99, 8), (0xa0, 64), (0x8c, 32), (0xa8, 1),
    (0xac, 8), (0xb0, 8), (0xb2, 16), (0xb4, 16), (0xb6, 16),
    (0xb8, 16), (0xba, 16), (0x1a0, 8), (0x1a2, 16), (0x1a4, 8),
    (0x1a8, 32), (0x1ac, 32), (0x1b0, 8), (0x1c0, 32), (0x1c4, 32),
    (0x1c8, 8), (0x1b1, 1), (0x1b2, 1), (0x1b3, 1), (0x1b4, 1),
    (0x1b5, 1), (0x1b7, 1), (0x1b8, 32), (0x1bc, 8), (0x1bd, 8), (0x1be, 1),
];

pub(super) fn roster(players: &[Player], human_state: &[u8; 0x1d0]) -> Vec<u8> {
    let mut output = vec![0u8; (41 + players.len() * 545).div_ceil(8)];
    let mut position = 0;
    let mut write = |value: u64, bits: usize| {
        for bit in 0..bits {
            output[position / 8] |= (((value >> bit) & 1) as u8) << (position % 8);
            position += 1;
        }
    };
    write(0, 1); // bdBitBuffer without type tags.
    write(14, 8);
    write(players.len() as u64, 32);
    for player in players {
        let mut row = if player.is_bot { [0; 0x1d0] } else { *human_state };
        if player.is_bot {
            row[0x94..0x98].copy_from_slice(&1000u32.to_le_bytes());
            row[0xac..0xb0].fill(0xff);
            row[0xb0] = 0xff;
            row[0x90] = 1;
        }
        row[..8].copy_from_slice(&player.uid.to_le_bytes());
        row[0x88] = if player.team == Team::One { 1 } else { 2 };
        for &(offset, bits) in FIELDS {
            let value = if bits == 1 {
                u64::from(row[offset] != 0)
            } else {
                let mut bytes = [0; 8];
                bytes[..bits / 8].copy_from_slice(&row[offset..offset + bits / 8]);
                u64::from_le_bytes(bytes)
            };
            write(value, bits);
        }
    }
    output
}

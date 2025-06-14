# ar2_ps2_logic.py - Action Replay 2 code routines for PS2
#
# This is a Python port of the C code from Omniconvert (ar2.c).
# Based on work by misfire and Pyriel.

import struct

_g_ar2_seed_bytes = bytearray(4)

AR2_KEY_ADDR = 0xDEADFACE
AR1_SEED = 0x05100518

AR2_TABLES = [
	[ 
		0x00, 0x1F, 0x9B, 0x69, 0xA5, 0x80, 0x90, 0xB2,
		0xD7, 0x44, 0xEC, 0x75, 0x3B, 0x62, 0x0C, 0xA3,
		0xA6, 0xE4, 0x1F, 0x4C, 0x05, 0xE4, 0x44, 0x6E,
		0xD9, 0x5B, 0x34, 0xE6, 0x08, 0x31, 0x91, 0x72,
	],
	[ 
		0x00, 0xAE, 0xF3, 0x7B, 0x12, 0xC9, 0x83, 0xF0,
		0xA9, 0x57, 0x50, 0x08, 0x04, 0x81, 0x02, 0x21,
		0x96, 0x09, 0x0F, 0x90, 0xC3, 0x62, 0x27, 0x21,
		0x3B, 0x22, 0x4E, 0x88, 0xF5, 0xC5, 0x75, 0x91,
	],
	[ 
		0x00, 0xE3, 0xA2, 0x45, 0x40, 0xE0, 0x09, 0xEA,
		0x42, 0x65, 0x1C, 0xC1, 0xEB, 0xB0, 0x69, 0x14,
		0x01, 0xD2, 0x8E, 0xFB, 0xFA, 0x86, 0x09, 0x95,
		0x1B, 0x61, 0x14, 0x0E, 0x99, 0x21, 0xEC, 0x40,
	],
	[ 
		0x00, 0x25, 0x6D, 0x4F, 0xC5, 0xCA, 0x04, 0x39,
		0x3A, 0x7D, 0x0D, 0xF1, 0x43, 0x05, 0x71, 0x66,
		0x82, 0x31, 0x21, 0xD8, 0xFE, 0x4D, 0xC2, 0xC8,
		0xCC, 0x09, 0xA0, 0x06, 0x49, 0xD5, 0xF1, 0x83,
	]
]

def _ar2_byteswap(val_u32):
    """Byteswap for AR2 seed handling (matches C's swapbytes)."""
    return struct.unpack('<I', struct.pack('>I', val_u32 & 0xFFFFFFFF))[0]

def ar2_set_seed(key_u32):
    """Sets the global AR2 seed."""
    global _g_ar2_seed_bytes
    swapped_key = _ar2_byteswap(key_u32)
    _g_ar2_seed_bytes = bytearray(struct.pack('<I', swapped_key))

def _nibble_flip(byte_val):
    return ((byte_val << 4) | (byte_val >> 4)) & 0xFF

def _ar2_decrypt_word(code_u32, type_u8, seed_idx_u8):
    """Decrypts a single 32-bit AR2 code word."""
    code_u32 &= 0xFFFFFFFF
    type_u8 &= 0xFF
    seed_idx_u8 &= 0x1F

    if type_u8 == 7:
        if seed_idx_u8 & 1:
            type_u8 = 1
        else:
            return (~code_u32) & 0xFFFFFFFF

    tmp_bytes = list(struct.pack('<I', code_u32))

    if type_u8 == 0:
        tmp_bytes[3] = (tmp_bytes[3] ^ AR2_TABLES[0][seed_idx_u8]) & 0xFF
        tmp_bytes[2] = (tmp_bytes[2] ^ AR2_TABLES[1][seed_idx_u8]) & 0xFF
        tmp_bytes[1] = (tmp_bytes[1] ^ AR2_TABLES[2][seed_idx_u8]) & 0xFF
        tmp_bytes[0] = (tmp_bytes[0] ^ AR2_TABLES[3][seed_idx_u8]) & 0xFF
    elif type_u8 == 1:
        tmp_bytes[3] = (_nibble_flip(tmp_bytes[3]) ^ AR2_TABLES[0][seed_idx_u8]) & 0xFF
        tmp_bytes[2] = (_nibble_flip(tmp_bytes[2]) ^ AR2_TABLES[2][seed_idx_u8]) & 0xFF
        tmp_bytes[1] = (_nibble_flip(tmp_bytes[1]) ^ AR2_TABLES[3][seed_idx_u8]) & 0xFF
        tmp_bytes[0] = (_nibble_flip(tmp_bytes[0]) ^ AR2_TABLES[1][seed_idx_u8]) & 0xFF
    elif type_u8 == 2:
        tmp_bytes[3] = (tmp_bytes[3] + AR2_TABLES[0][seed_idx_u8]) & 0xFF
        tmp_bytes[2] = (tmp_bytes[2] + AR2_TABLES[1][seed_idx_u8]) & 0xFF
        tmp_bytes[1] = (tmp_bytes[1] + AR2_TABLES[2][seed_idx_u8]) & 0xFF
        tmp_bytes[0] = (tmp_bytes[0] + AR2_TABLES[3][seed_idx_u8]) & 0xFF
    elif type_u8 == 3:
        tmp_bytes[3] = (tmp_bytes[3] - AR2_TABLES[3][seed_idx_u8]) & 0xFF
        tmp_bytes[2] = (tmp_bytes[2] - AR2_TABLES[2][seed_idx_u8]) & 0xFF
        tmp_bytes[1] = (tmp_bytes[1] - AR2_TABLES[1][seed_idx_u8]) & 0xFF
        tmp_bytes[0] = (tmp_bytes[0] - AR2_TABLES[0][seed_idx_u8]) & 0xFF
    elif type_u8 == 4:
        tmp_bytes[3] = ((tmp_bytes[3] ^ AR2_TABLES[0][seed_idx_u8]) + AR2_TABLES[0][seed_idx_u8]) & 0xFF
        tmp_bytes[2] = ((tmp_bytes[2] ^ AR2_TABLES[3][seed_idx_u8]) + AR2_TABLES[3][seed_idx_u8]) & 0xFF
        tmp_bytes[1] = ((tmp_bytes[1] ^ AR2_TABLES[1][seed_idx_u8]) + AR2_TABLES[1][seed_idx_u8]) & 0xFF
        tmp_bytes[0] = ((tmp_bytes[0] ^ AR2_TABLES[2][seed_idx_u8]) + AR2_TABLES[2][seed_idx_u8]) & 0xFF
    elif type_u8 == 5:
        tmp_bytes[3] = ((tmp_bytes[3] - AR2_TABLES[1][seed_idx_u8]) ^ AR2_TABLES[0][seed_idx_u8]) & 0xFF
        tmp_bytes[2] = ((tmp_bytes[2] - AR2_TABLES[2][seed_idx_u8]) ^ AR2_TABLES[1][seed_idx_u8]) & 0xFF
        tmp_bytes[1] = ((tmp_bytes[1] - AR2_TABLES[3][seed_idx_u8]) ^ AR2_TABLES[2][seed_idx_u8]) & 0xFF
        tmp_bytes[0] = ((tmp_bytes[0] - AR2_TABLES[0][seed_idx_u8]) ^ AR2_TABLES[3][seed_idx_u8]) & 0xFF
    elif type_u8 == 6:
        tmp_bytes[3] = (tmp_bytes[3] + AR2_TABLES[0][seed_idx_u8]) & 0xFF
        tmp_bytes[2] = (tmp_bytes[2] - AR2_TABLES[1][(seed_idx_u8 + 1) & 0x1F]) & 0xFF
        tmp_bytes[1] = (tmp_bytes[1] + AR2_TABLES[2][(seed_idx_u8 + 2) & 0x1F]) & 0xFF
        tmp_bytes[0] = (tmp_bytes[0] - AR2_TABLES[3][(seed_idx_u8 + 3) & 0x1F]) & 0xFF

    return struct.unpack('<I', bytes(tmp_bytes))[0]

def ar2_batch_decrypt_arr(code_list_u32):
    """
    Batch decrypts a list of u32 AR2 codes in place.
    Returns the new effective size of the list if 0xDEADFACE codes were processed.
    """
    global _g_ar2_seed_bytes
    i = 0
    current_size = len(code_list_u32)

    while i < current_size:
        if i + 1 >= current_size:
            break
        
        code_list_u32[i] = _ar2_decrypt_word(code_list_u32[i], _g_ar2_seed_bytes[0], _g_ar2_seed_bytes[1])
        code_list_u32[i+1] = _ar2_decrypt_word(code_list_u32[i+1], _g_ar2_seed_bytes[2], _g_ar2_seed_bytes[3])

        if code_list_u32[i] == AR2_KEY_ADDR:
            ar2_set_seed(code_list_u32[i+1])
            del code_list_u32[i:i+2]
            current_size -= 2
        else:
            i += 2
    return current_size

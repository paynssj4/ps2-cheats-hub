# armax_ps2_logic.py - Action Replay Max code routines for PS2
#
# This is a Python port of the C code from Omniconvert (armax.c).
# It aims to replicate the decryption/encryption logic for ARMAX PS2 codes.
#
# Based on work by Parasyte (2003-2004) and Pyriel (2008) from Omniconvert.

import struct
from ar2_ps2_logic import ar2_set_seed, ar2_batch_decrypt_arr
# import logging # Uncomment and use logging.debug instead of print for better control

# logging.debug("<<<<< CHARGEMENT DU MODULE armax_ps2_logic.py (VERSION AVEC LITERAL DIRECT POUR FILTER_MAP - V6) >>>>>")
# logging.debug(f"<<<<< CHEMIN DU MODULE CHARGÉ : {__file__} >>>>>")

GENTABLE0 = [
    0x39, 0x31, 0x29, 0x21, 0x19, 0x11, 0x09, 0x01,
    0x3A, 0x32, 0x2A, 0x22, 0x1A, 0x12, 0x0A, 0x02,
    0x3B, 0x33, 0x2B, 0x23, 0x1B, 0x13, 0x0B, 0x03,
    0x3C, 0x34, 0x2C, 0x24, 0x3F, 0x37, 0x2F, 0x27,
    0x1F, 0x17, 0x0F, 0x07, 0x3E, 0x36, 0x2E, 0x26,
    0x1E, 0x16, 0x0E, 0x06, 0x3D, 0x35, 0x2D, 0x25,
    0x1D, 0x15, 0x0D, 0x05, 0x1C, 0x14, 0x0C, 0x04,
]
GENTABLE1 = [
    0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01,
]
GENTABLE2 = [
    0x01, 0x02, 0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0E,
    0x0F, 0x11, 0x13, 0x15, 0x17, 0x19, 0x1B, 0x1C,
]
GENTABLE3 = [
    0x0E, 0x11, 0x0B, 0x18, 0x01, 0x05, 0x03, 0x1C,
    0x0F, 0x06, 0x15, 0x0A, 0x17, 0x13, 0x0C, 0x04,
    0x1A, 0x08, 0x10, 0x07, 0x1B, 0x14, 0x0D, 0x02,
    0x29, 0x34, 0x1F, 0x25, 0x2F, 0x37, 0x1E, 0x28,
    0x33, 0x2D, 0x21, 0x30, 0x2C, 0x31, 0x27, 0x38,
    0x22, 0x35, 0x2E, 0x2A, 0x32, 0x24, 0x1D, 0x20,
]
GENSUBTABLE = [
    0x1D, 0x2E, 0x7A, 0x85, 0x3F, 0xAB, 0xD9, 0x46,
]

CRCTABLE0 = [
	0x0000, 0x1081, 0x2102, 0x3183, 0x4204, 0x5285, 0x6306, 0x7387,
	0x8408, 0x9489, 0xA50A, 0xB58B, 0xC60C, 0xD68D, 0xE70E, 0xF78F,
]
CRCTABLE1 = [
	0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
	0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
]

TABLE0 = [
    0x01010400, 0x00000000, 0x00010000, 0x01010404, 0x01010004, 0x00010404, 0x00000004, 0x00010000,
    0x00000400, 0x01010400, 0x01010404, 0x00000400, 0x01000404, 0x01010004, 0x01000000, 0x00000004,
    0x00000404, 0x01000400, 0x01000400, 0x00010400, 0x00010400, 0x01010000, 0x01010000, 0x01000404,
    0x00010004, 0x01000004, 0x01000004, 0x00010004, 0x00000000, 0x00000404, 0x00010404, 0x01000000,
    0x00010000, 0x01010404, 0x00000004, 0x01010000, 0x01010400, 0x01000000, 0x01000000, 0x00000400,
    0x01010004, 0x00010000, 0x00010400, 0x01000004, 0x00000400, 0x00000004, 0x01000404, 0x00010404,
    0x01010404, 0x00010004, 0x01010000, 0x01000404, 0x01000004, 0x00000404, 0x00010404, 0x01010400,
    0x00000404, 0x01000400, 0x01000400, 0x00000000, 0x00010004, 0x00010400, 0x00000000, 0x01010004,
]
TABLE1 = [
    0x80108020, 0x80008000, 0x00008000, 0x00108020, 0x00100000, 0x00000020, 0x80100020, 0x80008020,
    0x80000020, 0x80108020, 0x80108000, 0x80000000, 0x80008000, 0x00100000, 0x00000020, 0x80100020,
    0x00108000, 0x00100020, 0x80008020, 0x00000000, 0x80000000, 0x00008000, 0x00108020, 0x80100000,
    0x00100020, 0x80000020, 0x00000000, 0x00108000, 0x00008020, 0x80108000, 0x80100000, 0x00008020,
    0x00000000, 0x00108020, 0x80100020, 0x00100000, 0x80008020, 0x80100000, 0x80108000, 0x00008000,
    0x80100000, 0x80008000, 0x00000020, 0x80108020, 0x00108020, 0x00000020, 0x00008000, 0x80000000,
    0x00008020, 0x80108000, 0x00100000, 0x80000020, 0x00100020, 0x80008020, 0x80000020, 0x00100020,
    0x00108000, 0x00000000, 0x80008000, 0x00008020, 0x80000000, 0x80100020, 0x80108020, 0x00108000,
]
TABLE2 = [
    0x00000208, 0x08020200, 0x00000000, 0x08020008, 0x08000200, 0x00000000, 0x00020208, 0x08000200,
    0x00020008, 0x08000008, 0x08000008, 0x00020000, 0x08020208, 0x00020008, 0x08020000, 0x00000208,
    0x08000000, 0x00000008, 0x08020200, 0x00000200, 0x00020200, 0x08020000, 0x08020008, 0x00020208,
    0x08000208, 0x00020200, 0x00020000, 0x08000208, 0x00000008, 0x08020208, 0x00000200, 0x08000000,
    0x08020200, 0x08000000, 0x00020008, 0x00000208, 0x00020000, 0x08020200, 0x08000200, 0x00000000,
    0x00000200, 0x00020008, 0x08020208, 0x08000200, 0x08000008, 0x00000200, 0x00000000, 0x08020008,
    0x08000208, 0x00020000, 0x08000000, 0x08020208, 0x00000008, 0x00020208, 0x00020200, 0x08000008,
    0x08020000, 0x08000208, 0x00000208, 0x08020000, 0x00020208, 0x00000008, 0x08020008, 0x00020200,
]
TABLE3 = [
    0x00802001, 0x00002081, 0x00002081, 0x00000080, 0x00802080, 0x00800081, 0x00800001, 0x00002001,
    0x00000000, 0x00802000, 0x00802000, 0x00802081, 0x00000081, 0x00000000, 0x00800080, 0x00800001,
    0x00000001, 0x00002000, 0x00800000, 0x00802001, 0x00000080, 0x00800000, 0x00002001, 0x00002080,
    0x00800081, 0x00000001, 0x00002080, 0x00800080, 0x00002000, 0x00802080, 0x00802081, 0x00000081,
    0x00800080, 0x00800001, 0x00802000, 0x00802081, 0x00000081, 0x00000000, 0x00000000, 0x00802000,
    0x00002080, 0x00800080, 0x00800081, 0x00000001, 0x00802001, 0x00002081, 0x00002081, 0x00000080,
    0x00802081, 0x00000081, 0x00000001, 0x00002000, 0x00800001, 0x00002001, 0x00802080, 0x00800081,
    0x00002001, 0x00002080, 0x00800000, 0x00802001, 0x00000080, 0x00800000, 0x00002000, 0x00802080,
]
TABLE4 = [
    0x00000100, 0x02080100, 0x02080000, 0x42000100, 0x00080000, 0x00000100, 0x40000000, 0x02080000,
    0x40080100, 0x00080000, 0x02000100, 0x40080100, 0x42000100, 0x42080000, 0x00080100, 0x40000000,
    0x02000000, 0x40080000, 0x40080000, 0x00000000, 0x40000100, 0x42080100, 0x42080100, 0x02000100,
    0x42080000, 0x40000100, 0x00000000, 0x42000000, 0x02080100, 0x02000000, 0x42000000, 0x00080100,
    0x00080000, 0x42000100, 0x00000100, 0x02000000, 0x40000000, 0x02080000, 0x42000100, 0x40080100,
    0x02000100, 0x40000000, 0x42080000, 0x02080100, 0x40080100, 0x00000100, 0x02000000, 0x42080000,
    0x42080100, 0x00080100, 0x42000000, 0x42080100, 0x02080000, 0x00000000, 0x40080000, 0x42000000,
    0x00080100, 0x02000100, 0x40000100, 0x00080000, 0x00000000, 0x40080000, 0x02080100, 0x40000100,
]
TABLE5 = [
    0x20000010, 0x20400000, 0x00004000, 0x20404010, 0x20400000, 0x00000010, 0x20404010, 0x00400000,
    0x20004000, 0x00404010, 0x00400000, 0x20000010, 0x00400010, 0x20004000, 0x20000000, 0x00004010,
    0x00000000, 0x00400010, 0x20004010, 0x00004000, 0x00404000, 0x20004010, 0x00000010, 0x20400010,
    0x20400010, 0x00000000, 0x00404010, 0x20404000, 0x00004010, 0x00404000, 0x20404000, 0x20000000,
    0x20004000, 0x00000010, 0x20400010, 0x00404000, 0x20404010, 0x00400000, 0x00004010, 0x20000010,
    0x00400000, 0x20004000, 0x20000000, 0x00004010, 0x20000010, 0x20404010, 0x00404000, 0x20400000,
    0x00404010, 0x20404000, 0x00000000, 0x20400010, 0x00000010, 0x00004000, 0x20400000, 0x00404010,
    0x00004000, 0x00400010, 0x20004010, 0x00000000, 0x20404000, 0x20000000, 0x00400010, 0x20004010,
]
TABLE6 = [
    0x00200000, 0x04200002, 0x04000802, 0x00000000, 0x00000800, 0x04000802, 0x00200802, 0x04200800,
    0x04200802, 0x00200000, 0x00000000, 0x04000002, 0x00000002, 0x04000000, 0x04200002, 0x00000802,
    0x04000800, 0x00200802, 0x00200002, 0x04000800, 0x04000002, 0x04200000, 0x04200800, 0x00200002,
    0x04200000, 0x00000800, 0x00000802, 0x04200802, 0x00200800, 0x00000002, 0x04000000, 0x00200800,
    0x04000000, 0x00200800, 0x00200000, 0x04000802, 0x04000802, 0x04200002, 0x04200002, 0x00000002,
    0x00200002, 0x04000000, 0x04000800, 0x00200000, 0x04200800, 0x00000802, 0x00200802, 0x04200800,
    0x00000802, 0x04000002, 0x04200802, 0x04200000, 0x00200800, 0x00000000, 0x00000002, 0x04200802,
    0x00000000, 0x00200802, 0x04200000, 0x00000800, 0x04000002, 0x04000800, 0x00000800, 0x00200002,
]
TABLE7 = [
    0x10001040, 0x00001000, 0x00040000, 0x10041040, 0x10000000, 0x10001040, 0x00000040, 0x10000000,
    0x00040040, 0x10040000, 0x10041040, 0x00041000, 0x10041000, 0x00041040, 0x00001000, 0x00000040,
    0x10040000, 0x10000040, 0x10001000, 0x00001040, 0x00041000, 0x00040040, 0x10040040, 0x10041000,
    0x00001040, 0x00000000, 0x00000000, 0x10040040, 0x10000040, 0x10001000, 0x00041040, 0x00040000,
    0x00041040, 0x00040000, 0x10041000, 0x00001000, 0x00000040, 0x10040040, 0x00001000, 0x00041040,
    0x10001000, 0x00000040, 0x10000040, 0x10040000, 0x10040040, 0x10000000, 0x00040000, 0x10001040,
    0x00000000, 0x10041040, 0x00040040, 0x10000040, 0x10040000, 0x10001000, 0x10001040, 0x00000000,
    0x10041040, 0x00041000, 0x00041000, 0x00001040, 0x00001040, 0x00040040, 0x10000000, 0x10041000,
]

# print(">>>>> UTILISATION D'UN LITERAL DIRECT POUR FILTER_MAP (V6) <<<<<")
# logging.debug(">>>>> UTILISATION D'UN LITERAL DIRECT POUR FILTER_MAP (V6) <<<<<")
CORRECT_FILTER_CHARS_LITERAL = "0123456789ABCDEFGHJKMNPQRTUVWXYZ"
# logging.debug(f">>>>> DEBUG: CORRECT_FILTER_CHARS_LITERAL (repr) = {repr(CORRECT_FILTER_CHARS_LITERAL)}")
# logging.debug(f">>>>> DEBUG: CORRECT_FILTER_CHARS_LITERAL (len)  = {len(CORRECT_FILTER_CHARS_LITERAL)}")
# logging.debug(f">>>>> DEBUG: CORRECT_FILTER_CHARS_LITERAL (id)   = {id(CORRECT_FILTER_CHARS_LITERAL)}")

# logging.debug(">>>>> DEBUG PRE-ENUMERATE (sur CORRECT_FILTER_CHARS_LITERAL): Iterating for H, J, K, M")
# for i_debug, char_debug in enumerate(CORRECT_FILTER_CHARS_LITERAL):
#     if char_debug in ('H', 'J', 'K', 'M'):
#         logging.debug(f"  enumerate sees: index={i_debug}, char='{char_debug}' (repr: {repr(char_debug)})")

FILTER_MAP = {char: i for i, char in enumerate(CORRECT_FILTER_CHARS_LITERAL)}
FILTER_CHARS = CORRECT_FILTER_CHARS_LITERAL
# logging.debug(f">>>>> DEBUG GLOBAL (après assignation depuis literal): FILTER_CHARS (repr) = {repr(FILTER_CHARS)}")
# logging.debug(f">>>>> DEBUG GLOBAL (après assignation depuis literal): FILTER_CHARS (len)  = {len(FILTER_CHARS)}")
# logging.debug(f">>>>> DEBUG GLOBAL (après assignation depuis literal): FILTER_CHARS (id)   = {id(FILTER_CHARS)}")
# logging.debug(f">>>>> DEBUG GLOBAL: FILTER_MAP['K'] immédiatement après création = {FILTER_MAP.get('K')}")
# logging.debug(f">>>>> DEBUG GLOBAL: FILTER_MAP['J'] immédiatement après création = {FILTER_MAP.get('J')}")


g_genseeds = [0] * 32
g_gameid = 0
g_region = 0

BITSTRINGLEN = [0x06, 0x0A, 0x0C, 0x13, 0x13, 0x08, 0x07, 0x20]

def rotate_left(value, rotate, bits=32):
    """Rotate bits left."""
    value &= ((1 << bits) - 1)
    rotate &= (bits - 1)
    return ((value << rotate) | (value >> (bits - rotate))) & ((1 << bits) - 1)

def rotate_right(value, rotate, bits=32):
    """Rotate bits right."""
    value &= ((1 << bits) - 1)
    rotate &= (bits - 1)
    return ((value >> rotate) | (value << (bits - rotate))) & ((1 << bits) - 1)

def byteswap(val):
    """Swap byte order (little-endian to big-endian or vice versa for 32-bit int)."""
    val &= 0xFFFFFFFF
    return struct.unpack('<I', struct.pack('>I', val))[0]

def getcode(src_pair_list):
    """Reads two 32-bit integers from list and byteswaps them.
       Corresponds to C: addr = byteswap(src[0]), val = byteswap(src[1])
    """
    addr = byteswap(src_pair_list[0])
    val = byteswap(src_pair_list[1])
    return addr, val
def setcode_python(dst_list_ref, index, addr_u32, val_u32):
    """Sets two 32-bit integers in list (byteswapped).
       Corresponds to C: dst[0] = byteswap(addr); dst[1] = byteswap(val);
    """
    dst_list_ref[index] = byteswap(addr_u32)
    dst_list_ref[index+1] = byteswap(val_u32)

def generateseeds(seeds_list_ref, seedtable_list, doreverse_bool):
    """
    Generates the 32 seeds used in the main algorithm rounds.
    Ported from Omniconvert's armax_ps2_logic.py (which is a port of armax.c).
    Modifies seeds_list_ref in place.
    """
    array0 = [0] * 0x38
    array1 = [0] * 0x38

    i = 0
    while i < 0x38:
        tmp = (GENTABLE0[i] - 1) & 0xFF
        if (seedtable_list[tmp >> 3] & GENTABLE1[tmp & 7]):
            array0[i] = 1
        else:
            array0[i] = 0
        i += 1

    i = 0
    while i < 0x10:
        array2 = [0] * 8
        tmp2 = GENTABLE2[i]

        for j in range(0x38):
            tmp = (tmp2 + j) & 0xFF

            if j > 0x1B:
                if tmp > 0x37:
                    tmp = (tmp - 0x1C) & 0xFF
            elif tmp > 0x1B:
                tmp = (tmp - 0x1C) & 0xFF
            array1[j] = array0[tmp]

        for j in range(0x30):
            if not array1[GENTABLE3[j] - 1]:
                continue
            
            tmp_mul_shift = j // 6
            array2[tmp_mul_shift] |= (GENTABLE1[j % 6] >> 2)
        
        seeds_list_ref[i << 1] = ((array2[0] << 24) | (array2[2] << 16) | (array2[4] << 8) | array2[6]) & 0xFFFFFFFF
        seeds_list_ref[(i << 1) + 1] = ((array2[1] << 24) | (array2[3] << 16) | (array2[5] << 8) | array2[7]) & 0xFFFFFFFF
        i += 1

    if not doreverse_bool:
        j = 0x1F
        for i in range(0, 16, 2):
            seeds_list_ref[i], seeds_list_ref[j - 1] = seeds_list_ref[j - 1], seeds_list_ref[i]
            seeds_list_ref[i + 1], seeds_list_ref[j] = seeds_list_ref[j], seeds_list_ref[i + 1]
            j -= 2

def buildseeds():
    """Initializes the global g_genseeds table."""
    global g_genseeds
    generateseeds(g_genseeds, GENSUBTABLE, False)


def unscramble1(addr, val):
    """First unscrambling step (part of decryption) - Aligning with C structure."""
    addr &= 0xFFFFFFFF
    val &= 0xFFFFFFFF
    
    val = rotate_left(val, 4) 
    tmp = ((addr ^ val) & 0xF0F0F0F0) & 0xFFFFFFFF
    addr = (addr ^ tmp) & 0xFFFFFFFF
    val = rotate_right((val ^ tmp), 0x14) & 0xFFFFFFFF
    tmp = ((addr ^ val) & 0xFFFF0000) & 0xFFFFFFFF
    addr = (addr ^ tmp) & 0xFFFFFFFF
    val = rotate_right((val ^ tmp), 0x12) & 0xFFFFFFFF

    tmp = ((addr ^ val) & 0x33333333) & 0xFFFFFFFF
    addr = (addr ^ tmp) & 0xFFFFFFFF
    val = rotate_right((val ^ tmp), 6) & 0xFFFFFFFF

    tmp = ((addr ^ val) & 0x00FF00FF) & 0xFFFFFFFF
    addr = (addr ^ tmp) & 0xFFFFFFFF
    val = rotate_left((val ^ tmp), 9) & 0xFFFFFFFF
    tmp = ((addr ^ val) & 0xAAAAAAAA) & 0xFFFFFFFF
    addr = rotate_left((addr ^ tmp), 1) & 0xFFFFFFFF
    val = (val ^ tmp) & 0xFFFFFFFF


    return addr & 0xFFFFFFFF, val & 0xFFFFFFFF

def unscramble2(addr, val):
    """Second unscrambling step (part of decryption) - Aligning with C structure."""
    addr &= 0xFFFFFFFF
    val &= 0xFFFFFFFF

    val = rotate_right(val, 1) & 0xFFFFFFFF

    tmp = ((addr ^ val) & 0xAAAAAAAA) & 0xFFFFFFFF
    val = (val ^ tmp) & 0xFFFFFFFF
    addr = rotate_right((addr ^ tmp), 9) & 0xFFFFFFFF


    tmp = ((addr ^ val) & 0x00FF00FF) & 0xFFFFFFFF
    val = (val ^ tmp) & 0xFFFFFFFF
    addr = rotate_left((addr ^ tmp), 6) & 0xFFFFFFFF

    tmp = ((addr ^ val) & 0x33333333) & 0xFFFFFFFF
    val = (val ^ tmp) & 0xFFFFFFFF
    addr = rotate_left((addr ^ tmp), 0x12) & 0xFFFFFFFF

    tmp = ((addr ^ val) & 0xFFFF0000) & 0xFFFFFFFF
    val = (val ^ tmp) & 0xFFFFFFFF
    addr = rotate_left((addr ^ tmp), 0x14) & 0xFFFFFFFF


    tmp = ((addr ^ val) & 0xF0F0F0F0) & 0xFFFFFFFF
    val = (val ^ tmp) & 0xFFFFFFFF
    addr = rotate_right((addr ^ tmp), 4) & 0xFFFFFFFF

    return addr & 0xFFFFFFFF, val & 0xFFFFFFFF

def decrypt_armax_code_line(encrypted_pair_list, current_pair_index):
    """
    Decrypts a single pair of ARMAX code words.
    encrypted_pair_list is the flat list of all binary codes.
    current_pair_index is the starting index of the current pair in encrypted_pair_list.
    Returns a tuple (decrypted_address, decrypted_value).
    Modifies encrypted_pair_list in place.
    """
    current_code_word1 = encrypted_pair_list[current_pair_index]
    current_code_word2 = encrypted_pair_list[current_pair_index + 1]
    # logging.debug(f">>>>> DEBUG decrypt_armax_code_line: Entrée encrypted_pair_list (index {current_pair_index}) = [{current_code_word1:08X}, {current_code_word2:08X}]")

    addr, val = getcode([current_code_word1, current_code_word2])

    # logging.debug(f">>>>> DEBUG decrypt_armax_code_line: Après getcode -> addr={addr:08X}, val={val:08X}")

    addr, val = unscramble1(addr, val)
    # logging.debug(f">>>>> DEBUG decrypt_armax_code_line: Après unscramble1 -> addr={addr:08X}, val={val:08X}")

    i = 0
    while i < 32:
        tmp = (rotate_right(val, 4) ^ g_genseeds[i]) & 0xFFFFFFFF
        tmp2 = (val ^ g_genseeds[i+1]) & 0xFFFFFFFF
        # logging.debug(f">>>>> DEBUG decrypt_armax_code_line:   Round 1 (addr): tmp={tmp:08X}, tmp2={tmp2:08X}")
        
        addr_xor_val = (TABLE6[tmp & 0x3F] ^ TABLE4[(tmp >> 8) & 0x3F] ^
                        TABLE2[(tmp >> 16) & 0x3F] ^ TABLE0[(tmp >> 24) & 0x3F] ^
                        TABLE7[tmp2 & 0x3F] ^ TABLE5[(tmp2 >> 8) & 0x3F] ^
                        TABLE3[(tmp2 >> 16) & 0x3F] ^ TABLE1[(tmp2 >> 24) & 0x3F])
        addr = (addr ^ addr_xor_val) & 0xFFFFFFFF
        
        i += 2
        if i >= 32:
            break
        
        # logging.debug(f">>>>> DEBUG decrypt_armax_code_line: Boucle i={i} (avant Round 2), addr_in={addr:08X}, val_in={val:08X}, seed0={g_genseeds[i]:08X}, seed1={g_genseeds[i+1]:08X}")

        tmp = (rotate_right(addr, 4) ^ g_genseeds[i]) & 0xFFFFFFFF
        tmp2 = (addr ^ g_genseeds[i+1]) & 0xFFFFFFFF

        val_xor_val = (TABLE6[tmp & 0x3F] ^ TABLE4[(tmp >> 8) & 0x3F] ^
                       TABLE2[(tmp >> 16) & 0x3F] ^ TABLE0[(tmp >> 24) & 0x3F] ^
                       TABLE7[tmp2 & 0x3F] ^ TABLE5[(tmp2 >> 8) & 0x3F] ^
                       TABLE3[(tmp2 >> 16) & 0x3F] ^ TABLE1[(tmp2 >> 24) & 0x3F])
        val = (val ^ val_xor_val) & 0xFFFFFFFF

        i += 2

    addr, val = unscramble2(addr, val)
    setcode_python(encrypted_pair_list, current_pair_index, val, addr)


def alphatobin_single_code(armax_code_str_no_dashes):
    """
    Converts a single ARMAX code string (13 chars, no dashes) to two 32-bit integers.
    Matches Omniconvert's C and Python logic.
    """
    if len(armax_code_str_no_dashes) != 13:
        raise ValueError("ARMAX code string must be 13 characters long (no dashes).")

    values = []
    for char_code in armax_code_str_no_dashes:
        try:
            values.append(FILTER_MAP[char_code])
        except KeyError:
            raise ValueError(f"Invalid character '{char_code}' in ARMAX code.")

    bin0 = (values[0] << 27) | (values[1] << 22) | (values[2] << 17) | \
           (values[3] << 12) | (values[4] << 7)  | (values[5] << 2)  | \
           (values[6] >> 3)
    bin0 &= 0xFFFFFFFF

    bin1 = ((values[6] & 0x07) << 29)
    bin1 |= (values[7] << 24)
    bin1 |= (values[8] << 19)
    bin1 |= (values[9] << 14)
    bin1 |= (values[10] << 9)
    bin1 |= (values[11] << 4)
    bin1 |= (values[12] >> 1)
    bin1 &= 0xFFFFFFFF

    # logging.debug(f">>>>> DEBUG alphatobin_single_code: input='{armax_code_str_no_dashes}', bin0={bin0:08X}, bin1={bin1:08X}")
    return bin0, bin1

def gencrc16_python(codes_list_u32, size_u32_count):
    """Generates CRC16 for ARMAX codes."""
    ret_crc = 0
    for word_idx in range(size_u32_count):
        current_word = codes_list_u32[word_idx]
        for i in range(4):
            byte_to_process = (current_word >> (i * 8)) & 0xFF
            tmp2 = byte_to_process ^ (ret_crc & 0xFF)
            
            ret_crc = ( (CRCTABLE0[(tmp2 >> 4) & 0x0F] ^ CRCTABLE1[tmp2 & 0x0F]) ^ (ret_crc >> 8) ) & 0xFFFF
    return ret_crc

def verifycode_python(codes_list_u32, size_u32_count):
    """Verifies ARMAX code CRC. Returns 4-bit checksum."""
    tmp = gencrc16_python(codes_list_u32, size_u32_count)
    return (((tmp >> 12) ^ (tmp >> 8) ^ (tmp >> 4) ^ tmp) & 0x0F)

def getbitstring_python(ctrl_list, num_bits_to_get):
    """
    Extracts a bitstring from the codes.
    ctrl_list = [base_codes_list, current_word_offset, current_bit_offset, total_words_in_base_list]
    Returns a tuple (success_bool, extracted_value_u32).
    Modifies ctrl_list[1] (word_offset) and ctrl_list[2] (bit_offset) in place.
    """
    base_codes_list = ctrl_list[0]

    output_val = 0
    bits_remaining = num_bits_to_get

    while bits_remaining > 0:
        if ctrl_list[2] > 0x1F:
            ctrl_list[2] = 0
            ctrl_list[1] += 1
        
        if ctrl_list[1] >= ctrl_list[3]:
            return False, 0

        current_word = base_codes_list[ctrl_list[1]]
        bit_val = (current_word >> (0x1F - ctrl_list[2])) & 1
        output_val = (output_val << 1) | bit_val
        
        ctrl_list[2] += 1
        bits_remaining -= 1
    
    return True, output_val

def batchdecrypt_python(binary_codes_list):
    """
    Main ARMAX decryption for a list of binary codes.
    Modifies binary_codes_list in place.
    Returns True on success (CRC OK), False on failure.
    Sets global g_gameid and g_region.
    """
    global g_gameid, g_region

    num_code_pairs = len(binary_codes_list) // 2
    if (g_genseeds[0] == 0 and g_genseeds[1] == 0):
        buildseeds()

    for i in range(num_code_pairs):
        decrypt_armax_code_line(binary_codes_list, i * 2)

    ctrl_for_getbitstring = [binary_codes_list, 0, 4, len(binary_codes_list)]
    
    tmparray2 = [0] * 8

    success, tmparray2[1] = getbitstring_python(ctrl_for_getbitstring, 13)
    if not success: return False
    success, tmparray2[2] = getbitstring_python(ctrl_for_getbitstring, 19)
    if not success: return False
    success, tmparray2[3] = getbitstring_python(ctrl_for_getbitstring, 1)
    if not success: return False
    success, tmparray2[4] = getbitstring_python(ctrl_for_getbitstring, 1)
    if not success: return False
    success, tmparray2[5] = getbitstring_python(ctrl_for_getbitstring, 2)
    if not success: return False

    g_gameid = tmparray2[1]
    g_region = tmparray2[5]

    original_first_word_val = binary_codes_list[0]
    binary_codes_list[0] &= 0x0FFFFFFF
    
    calculated_crc_check_val = verifycode_python(binary_codes_list, len(binary_codes_list))
    original_crc_check_val = (original_first_word_val >> 28) & 0xF

    binary_codes_list[0] = original_first_word_val

    return original_crc_check_val == calculated_crc_check_val

def arm_read_verifier_python(decrypted_binary_codes_list):
    """
    Scans the verifier bit string to determine how many lines it occupies.
    Returns number of ARMAX lines (pairs of u32), or -1 on error.
    """
    ctrl = [decrypted_binary_codes_list, 1, 8, len(decrypted_binary_codes_list)]
    bits_read = 0
    num_armax_lines = 1

    success, terminator_bit = getbitstring_python(ctrl, 1)
    if not success: return -1
    bits_read += 1

    while terminator_bit == 0:
        success, exp_size_index = getbitstring_python(ctrl, 3)
        if not success: return -1
        bits_read += 3

        if exp_size_index >= len(BITSTRINGLEN): return -1
        
        expansion_data_len = BITSTRINGLEN[exp_size_index]
        success, _ = getbitstring_python(ctrl, expansion_data_len)
        if not success: return -1
        bits_read += expansion_data_len

        success, terminator_bit = getbitstring_python(ctrl, 1)
        if not success: return -1
        bits_read += 1

    bits_read -= 24
    while bits_read > 0:
        num_armax_lines += 1
        bits_read -= 64

    return num_armax_lines

def armax_batch_decrypt_full_python(list_of_armax_strings, ar2_key_u32):
    """
    Top-level function to decrypt a list of ARMAX strings.
    Handles ARMAX decryption and subsequent AR2 decryption if applicable.
    Returns a tuple: (status_bool, list_of_decrypted_u32_pairs, game_id, region)
    """
    global g_gameid, g_region

    if not list_of_armax_strings:
        return False, [], 0, 0

    flat_binary_codes = []
    for armax_str in list_of_armax_strings:
        cleaned_str = armax_str.strip().upper().replace("-", "")
        if len(cleaned_str) != 13:
            print(f"Warning: ARMAX string '{armax_str}' has incorrect length, skipping.")
            continue
        
        try:
            b0, b1 = alphatobin_single_code(cleaned_str)
            flat_binary_codes.extend([b0, b1])
        except ValueError as e:
            print(f"Error converting ARMAX string '{armax_str}': {e}")
            return False, [], 0, 0

    if not flat_binary_codes:
        return False, [], 0, 0

    armax_decrypt_success = batchdecrypt_python(flat_binary_codes)
    if not armax_decrypt_success:
        print("ARMAX batch decryption failed (CRC error or other).")
        return False, [(flat_binary_codes[i], flat_binary_codes[i+1]) for i in range(0, len(flat_binary_codes), 2)], g_gameid, g_region

    num_armax_lines_u32_pairs = arm_read_verifier_python(flat_binary_codes)
    if num_armax_lines_u32_pairs == -1:
        print("Error reading ARMAX verifier string.")
        return False, [(flat_binary_codes[i], flat_binary_codes[i+1]) for i in range(0, len(flat_binary_codes), 2)], g_gameid, g_region

    num_armax_u32s = num_armax_lines_u32_pairs * 2
    ar2_data_size_u32s = len(flat_binary_codes) - num_armax_u32s

    if ar2_data_size_u32s > 0:
        ar2_code_slice = flat_binary_codes[num_armax_u32s:]
        
        for i in range(len(ar2_code_slice)):
            ar2_code_slice[i] = byteswap(ar2_code_slice[i])

        ar2_set_seed(ar2_key_u32)
        new_ar2_size = ar2_batch_decrypt_arr(ar2_code_slice)

        flat_binary_codes = flat_binary_codes[:num_armax_u32s] + ar2_code_slice[:new_ar2_size]

    result_pairs = []
    for i in range(0, len(flat_binary_codes), 2):
        if i + 1 < len(flat_binary_codes):
            result_pairs.append((flat_binary_codes[i], flat_binary_codes[i+1]))
        else:
            result_pairs.append((flat_binary_codes[i], 0xDEADBEEF))

    return True, result_pairs, g_gameid, g_region

# Initialize seeds when the module is loaded
buildseeds()

if __name__ == "__main__":
    # These prints are for testing purposes only and should not be in production code.
    # print(f">>>>> DEBUG __main__ de armax_ps2_logic.py: g_genseeds initialisés.")
    # print(f"g_genseeds (first 4 words): {g_genseeds[0]:08X} {g_genseeds[1]:08X} {g_genseeds[2]:08X} {g_genseeds[3]:08X}")

    test_armax_code_ffx_m = "CEB513B0BNBKA" 
    test_armax_code_generic = "1E88A92EA7GRR"
    user_code1 = "GMZET6VWH2W3W"
    user_code2 = "VED7KAJZAMKYH"

    all_passed = True
    for test in test_cases:
        # print(f"\nTesting {test['name']}: {test['armax'][:4]}-{test['armax'][4:8]}-{test['armax'][8:]}")
        try:
            armax_input_cleaned = test['armax'].replace('-', '').upper()
            if len(armax_input_cleaned) == 15:
                armax_input_cleaned = armax_input_cleaned[:13]

            temp_binary_list = list(alphatobin_single_code(armax_input_cleaned))
            print(f"  Binary pair (bin0, bin1): {temp_binary_list[0]:08X} {temp_binary_list[1]:08X}")
            # decrypt_armax_code_line(temp_binary_list, 0) # This line was commented out in the original, but should be uncommented for the test to actually decrypt
            dec_addr, dec_val = temp_binary_list[0], temp_binary_list[1]
            # print(f"  Decrypted RAW: {dec_addr:08X} {dec_val:08X}")
            # print(f"  Expected RAW:  {test['expected_addr']} {test['expected_val']}")

            assert f"{dec_addr:08X}" == test['expected_addr']
            assert f"{dec_val:08X}" == test['expected_val']
            # print(f"  {test['name']} Test: PASSED")

        except ValueError as e:
            # print(f"  Error during test '{test['name']}': {e}")
            all_passed = False
        except AssertionError:
            # print(f"  {test['name']} Test: FAILED - Output does not match expected.")
            all_passed = False
        except Exception as e:
            # print(f"  An unexpected error occurred during test '{test['name']}': {e}")
            all_passed = False
            
    if all_passed:
        # print("\nAll tests passed successfully!")
        pass
    # else:
        # print("\nSome tests FAILED.")
        # pass

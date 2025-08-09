from gibberlink import hamming74_encode_nibble, hamming74_encode_bytes


def test_hamming74_encode_nibble():
    # nibble 0xA -> d3d2d1d0 = 1010
    # parity bits: p1=1, p2=0, p3=1
    assert hamming74_encode_nibble(0xA) == [1, 0, 1, 1, 0, 1, 0]


def test_hamming74_encode_bytes():
    # byte 0xA5 -> nibbles 0xA and 0x5
    expected = [1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1]
    assert hamming74_encode_bytes(bytes([0xA5])) == expected

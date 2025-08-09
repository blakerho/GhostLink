from ghostlink import bits_to_symbols


def test_bits_to_symbols_preserves_input_list():
    bits = [1, 0, 1, 1]
    original = bits[:]
    symbols = bits_to_symbols(bits, 8)
    assert bits == original
    assert symbols == [5, 4]

def test_bits_to_symbols_order4_with_padding():
    bits = [1, 0, 1, 1, 1]  # 5 bits -> padded to 6
    symbols = bits_to_symbols(bits, 4)
    assert symbols == [2, 3, 2]

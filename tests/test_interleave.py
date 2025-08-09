from ghostlink import interleave
from ghostlink.decoder import deinterleave


def test_interleave_roundtrip():
    bits = [0, 1, 1, 0, 1, 0, 0, 1, 1, 1]
    depth = 4
    inter = interleave(bits, depth)
    assert inter != bits  # ensure interleaving actually rearranges
    de = deinterleave(inter, depth)[:len(bits)]
    assert de == bits

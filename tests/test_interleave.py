import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from GhostLink import interleave
from decoder import deinterleave


def test_interleave_roundtrip():
    bits = [0, 1, 1, 0, 1, 0, 0, 1, 1, 1]
    depth = 4
    inter = interleave(bits, depth)
    assert inter != bits  # ensure interleaving actually rearranges
    de = deinterleave(inter, depth)[:len(bits)]
    assert de == bits

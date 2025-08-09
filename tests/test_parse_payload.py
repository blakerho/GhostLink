import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from decoder import parse_payload
from GhostLink import build_payload, encode_bytes_to_wav
from decoder import decode_wav
from pathlib import Path


def test_parse_payload_bad_magic():
    payload = build_payload(b"hi")
    bad = b"BAD" + payload[3:]
    with pytest.raises(ValueError, match="bad magic"):
        parse_payload(bad)


def test_parse_payload_truncated():
    payload = build_payload(b"hi")
    truncated = payload[:-1]
    with pytest.raises(ValueError, match="truncated payload"):
        parse_payload(truncated)


def test_parse_payload_crc_mismatch():
    payload = bytearray(build_payload(b"hi"))
    payload[-1] ^= 0xFF
    with pytest.raises(ValueError, match="CRC mismatch"):
        parse_payload(bytes(payload))


def test_decode_wav_surfaces_corruption(tmp_path):
    message = b"hi"
    path, _ = encode_bytes_to_wav(
        user_bytes=message,
        out_dir=str(tmp_path),
        base_name_hint="msg",
        samplerate=16000,
        baud=200.0,
        amp=0.1,
        dense=True,
        mix_profile="streaming",
        gap_ms=0.0,
        preamble_s=0.5,
        interleave_depth=2,
        repeats=1,
        ramp_ms=5.0,
    )

    data = bytearray(Path(path).read_bytes())
    for i in range(44, len(data)):
        data[i] = 0
    corrupt_path = Path(tmp_path) / "corrupt.wav"
    corrupt_path.write_bytes(data)

    with pytest.raises(ValueError):
        decode_wav(
            path=str(corrupt_path),
            baud=200.0,
            dense=True,
            mix_profile="streaming",
            preamble_s=0.5,
            interleave_depth=2,
            repeats=1,
        )

from gibberlink import encode_bytes_to_wav
from gibberlink.decoder import decode_wav

HISTORY_DB_NAME = "gibberlink_history.db"


def test_full_encode_decode_cycle(tmp_path):
    message = b"hi"
    out_dir = tmp_path
    path, skipped = encode_bytes_to_wav(
        user_bytes=message,
        out_dir=str(out_dir),
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
    assert skipped is False
    assert (out_dir / HISTORY_DB_NAME).exists()
    decoded = decode_wav(
        path=path,
        baud=200.0,
        dense=True,
        mix_profile="streaming",
        preamble_s=0.5,
        interleave_depth=2,
        repeats=1,
    )
    assert decoded == message

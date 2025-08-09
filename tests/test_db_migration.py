from gibberlink import encode_bytes_to_wav
from gibberlink.__main__ import db_init
import sqlite3


def test_legacy_db_migrates(tmp_path):
    legacy = tmp_path / "ghostlink_history.db"
    db_init(str(legacy))
    encode_bytes_to_wav(
        user_bytes=b"hi",
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
    new_db = tmp_path / "gibberlink_history.db"
    assert new_db.exists()
    assert not legacy.exists()
    conn = sqlite3.connect(new_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM encodes").fetchone()[0]
    finally:
        conn.close()
    assert count == 1

from ghostlink import encode_bytes_to_wav
from ghostlink.constants import HISTORY_DB
import sqlite3
from pathlib import Path


def test_db_in_project_root(tmp_path):
    path, _ = encode_bytes_to_wav(
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
    assert Path(path).with_suffix(".mid").exists()
    root_db = Path.cwd() / HISTORY_DB
    assert root_db.exists()
    assert not (tmp_path / HISTORY_DB).exists()
    conn = sqlite3.connect(root_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM encodes").fetchone()[0]
    finally:
        conn.close()
    assert count == 1

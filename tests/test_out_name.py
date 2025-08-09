import subprocess
import sys
from pathlib import Path

from gibberlink import encode_bytes_to_wav
from gibberlink.constants import HISTORY_DB


def test_encode_bytes_to_wav_out_name(tmp_path):
    path, skipped = encode_bytes_to_wav(
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
        out_name="custom.wav",
    )
    assert skipped is False
    assert Path(path).name == "custom.wav"
    assert (tmp_path / "custom_slow25.wav").exists()
    assert (tmp_path / "custom_slow50.wav").exists()
    assert (tmp_path / "custom_slow100.wav").exists()
    assert (tmp_path / "custom.mid").exists()
    assert (tmp_path / HISTORY_DB).exists()


def test_cli_out_name(tmp_path):
    msg = "hi"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "gibberlink",
            "text",
            msg,
            str(tmp_path),
            "--out-name",
            "cli.wav",
        ],
        check=True,
        capture_output=True,
    )
    wav_files = list(Path(tmp_path).glob("*.wav"))
    assert any(p.name == "cli.wav" for p in wav_files)
    slow = {p.name for p in wav_files}
    assert "cli_slow25.wav" in slow
    assert "cli_slow50.wav" in slow
    assert "cli_slow100.wav" in slow
    assert (tmp_path / "cli.mid").exists()


def test_cli_out_name_rejected_for_dir(tmp_path):
    in_dir = tmp_path / "inp"
    in_dir.mkdir()
    (in_dir / "a.txt").write_text("hi")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "gibberlink",
            "dir",
            str(in_dir),
            str(tmp_path),
            "--out-name",
            "bad.wav",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0

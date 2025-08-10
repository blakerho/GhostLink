import subprocess
import wave
from pathlib import Path

import pytest


def _duration(p: Path) -> float:
    with wave.open(str(p), "rb") as wf:
        return wf.getnframes() / wf.getframerate()

def test_cli_round_trip(tmp_path, install_cli):
    msg = "hello"
    # Encode message via CLI
    subprocess.run(
        ["ghostlink", "text", msg, str(tmp_path)],
        check=True,
        capture_output=True,
    )
    wav_files = list(Path(tmp_path).glob("*.wav"))
    assert len(wav_files) == 5
    slow = {p.name for p in wav_files if "slow" in p.stem}
    assert any(name.endswith("_slow25.wav") for name in slow)
    assert any(name.endswith("_slow50.wav") for name in slow)
    assert any(name.endswith("_slow100.wav") for name in slow)
    assert any(name.endswith("_slow1000.wav") for name in slow)
    wav_path = [p for p in wav_files if "slow" not in p.stem][0]
    slow1000 = [p for p in wav_files if p.name.endswith("_slow1000.wav")][0]
    assert _duration(slow1000) == pytest.approx(_duration(wav_path) * 10, rel=0.01)
    midi_files = list(Path(tmp_path).glob("*.mid"))
    assert len(midi_files) == 1
    # Decode using reference decoder CLI
    proc = subprocess.run(
        ["ghostlink-decode", str(wav_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout.strip() == msg

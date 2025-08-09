import subprocess
import sys
from pathlib import Path


def test_cli_round_trip(tmp_path):
    msg = "hello"
    # Encode message via CLI
    subprocess.run(
        [sys.executable, "-m", "gibberlink", "text", msg, str(tmp_path)],
        check=True,
        capture_output=True,
    )
    wav_files = list(Path(tmp_path).glob("*.wav"))
    assert len(wav_files) == 4
    slow = {p.name for p in wav_files if "slow" in p.stem}
    assert any(name.endswith("_slow25.wav") for name in slow)
    assert any(name.endswith("_slow50.wav") for name in slow)
    assert any(name.endswith("_slow100.wav") for name in slow)
    midi_files = list(Path(tmp_path).glob("*.mid"))
    assert len(midi_files) == 1
    wav_path = [p for p in wav_files if "slow" not in p.stem][0]
    # Decode using reference decoder CLI
    proc = subprocess.run(
        [sys.executable, "-m", "gibberlink.decoder", str(wav_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout.strip() == msg

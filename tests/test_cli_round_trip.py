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
    assert len(wav_files) == 1
    wav_path = wav_files[0]
    # Decode using reference decoder CLI
    proc = subprocess.run(
        [sys.executable, "-m", "gibberlink.decoder", str(wav_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout.strip() == msg

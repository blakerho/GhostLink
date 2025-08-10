import wave
from pathlib import Path

import pytest

from ghostlink import encode_bytes_to_wav


def _duration(p: Path) -> float:
    with wave.open(str(p), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def test_slowscaled_durations(tmp_path):
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
    main_dur = _duration(Path(path))
    factors = {"slow25": 4 / 3, "slow50": 2.0, "slow100": 4.0, "slow1000": 10.0}
    for suffix, factor in factors.items():
        slow = Path(path).with_name(Path(path).stem + f"_{suffix}.wav")
        assert slow.exists()
        assert _duration(slow) == pytest.approx(main_dur * factor, rel=0.01)


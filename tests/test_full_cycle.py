from ghostlink import (
    encode_bytes_to_wav,
    build_payload,
    hamming74_encode_bytes,
    interleave,
    bits_to_symbols,
)
from ghostlink.decoder import decode_wav
from ghostlink.constants import HISTORY_DB
from pathlib import Path
from mido import MidiFile
import wave
import pytest


def _duration(p: Path) -> float:
    with wave.open(str(p), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


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
    assert (Path.cwd() / HISTORY_DB).exists()
    midi_path = Path(path).with_suffix(".mid")
    assert midi_path.exists()
    for suffix in ("slow25", "slow50", "slow100", "slow1000"):
        assert Path(path).with_name(Path(path).stem + f"_{suffix}.wav").exists()
    main_dur = _duration(Path(path))
    slow1000 = Path(path).with_name(Path(path).stem + "_slow1000.wav")
    assert _duration(slow1000) == pytest.approx(main_dur * 10, rel=0.01)
    mid = MidiFile(midi_path)
    notes = [msg for track in mid.tracks for msg in track if msg.type == "note_on"]
    payload = build_payload(message)
    bits = hamming74_encode_bytes(payload)
    bits = interleave(bits, 2)
    symbols = bits_to_symbols(bits, 8)
    assert len(notes) == len(symbols)
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

import struct

from GhostLink import symbols_to_audio


def test_boundary_samples_continuous():
    freqs = [1234.0]
    sr = 8000
    baud = 100.0
    amp = 0.5
    symbols = [0] * 5

    combined, _ = symbols_to_audio(symbols * 2, freqs, sr, baud, amp,
                                   phase0=0.0, gap_ms=0.0, ramp_ms=0.0)
    part1, phase = symbols_to_audio(symbols, freqs, sr, baud, amp,
                                    phase0=0.0, gap_ms=0.0, ramp_ms=0.0)
    part2, _ = symbols_to_audio(symbols, freqs, sr, baud, amp,
                                phase0=phase, gap_ms=0.0, ramp_ms=0.0)
    joined = part1 + part2

    assert joined == combined
    samples1 = struct.unpack('<' + 'h' * (len(part1) // 2), part1)
    assert samples1[-1] != 0

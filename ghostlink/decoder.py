#!/usr/bin/env python3
"""
GhostLink Decoder: Recover text from FSK audio produced by the `ghostlink` encoder.

Examples:
  ghostlink-decode ./message.wav
  python -m ghostlink.decoder ./message.wav
"""

import argparse
import binascii
import logging
import math
import struct
import wave
import sys
import os
from typing import List
from .profiles import freq_profile

# ------------------------
# Logging
# ------------------------
def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

# ------------------------
# Goertzel detector
# ------------------------
def goertzel(samples: List[float], freq: float, sr: int) -> float:
    coeff = 2.0 * math.cos(2.0 * math.pi * freq / sr)
    s_prev = 0.0
    s_prev2 = 0.0
    for x in samples:
        s = x + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s
    power = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
    return power

# ------------------------
# Symbol and bit helpers
# ------------------------
def symbols_to_bits(symbols: List[int], order: int) -> List[int]:
    k = 2 if order == 4 else 3
    out = []
    for s in symbols:
        for j in reversed(range(k)):
            out.append((s >> j) & 1)
    return out

def deinterleave(bits: List[int], depth: int) -> List[int]:
    if depth <= 1:
        return bits
    rows = depth
    cols = (len(bits) + rows - 1) // rows
    padded = bits + [0] * (rows * cols - len(bits))
    dest = [0] * (rows * cols)
    idx = 0
    for c in range(cols):
        for r in range(rows):
            dest[r * cols + c] = padded[idx]
            idx += 1
    return dest[:len(bits)]

# ------------------------
# Hamming(7,4) decode
# ------------------------
def hamming74_decode_bits(bits: List[int]) -> List[int]:
    out = []
    for i in range(0, len(bits) - 6, 7):
        block = bits[i:i+7]
        p1, p2, d3, p3, d2, d1, d0 = block
        s1 = p1 ^ d3 ^ d2 ^ d0
        s2 = p2 ^ d3 ^ d1 ^ d0
        s3 = p3 ^ d2 ^ d1 ^ d0
        err = (s1 << 0) | (s2 << 1) | (s3 << 2)
        if err:
            idx = err - 1
            if idx < 7:
                block[idx] ^= 1
        out.extend([block[2], block[4], block[5], block[6]])
    return out

def bits_to_bytes(bits: List[int]) -> bytes:
    out = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
            else:
                byte <<= 1
        out.append(byte)
    return bytes(out)

# ------------------------
# WAV reader and symbol extraction
# ------------------------
def read_wav(path: str) -> (List[float], int):
    with wave.open(path, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("Only mono 16-bit WAV supported")
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
        samples = struct.unpack("<%dh" % n, raw)
        return [s / 32768.0 for s in samples], sr

def detect_symbols(samples: List[float], sr: int, baud: float, preamble_s: float, freqs: List[float]) -> List[int]:
    start = int(round(preamble_s * sr))
    sym_len = int(round(sr / baud))
    symbols = []
    i = start
    while i + sym_len <= len(samples):
        chunk = samples[i:i+sym_len]
        mags = [goertzel(chunk, f, sr) for f in freqs]
        symbols.append(int(max(range(len(mags)), key=lambda j: mags[j])))
        i += sym_len
    return symbols

# ------------------------
# Payload extraction
# ------------------------
def decode_symbols(symbols: List[int], order: int, interleave_depth: int) -> bytes:
    bits = symbols_to_bits(symbols, order)
    if interleave_depth > 1:
        extra = len(bits) % interleave_depth
        if extra:
            bits = bits[:-extra]
        bits = deinterleave(bits, interleave_depth)
    rem = len(bits) % 7
    if rem:
        bits = bits[:-rem]
    decoded = hamming74_decode_bits(bits)
    return bits_to_bytes(decoded)

def parse_payload(data: bytes) -> bytes:
    if len(data) < 3 + 4 + 4:
        raise ValueError("payload too short")
    if data[:3] != b"GL1":
        raise ValueError("bad magic")
    length = struct.unpack(">I", data[3:7])[0]
    need = 3 + 4 + length + 4
    if len(data) < need:
        raise ValueError("truncated payload")
    msg = data[7:7+length]
    crc_recv = struct.unpack(">I", data[7+length:7+length+4])[0]
    crc_calc = binascii.crc32(msg) & 0xFFFFFFFF
    if crc_calc != crc_recv:
        raise ValueError("CRC mismatch")
    return msg

def decode_wav(path: str, baud: float, dense: bool, mix_profile: str,
               preamble_s: float, interleave_depth: int, repeats: int) -> bytes:
    samples, sr = read_wav(path)
    freqs = freq_profile(dense, mix_profile)
    symbols = detect_symbols(samples, sr, baud, preamble_s, freqs)
    order = 8 if dense else 4
    if repeats > 1 and len(symbols) >= repeats:
        per = len(symbols) // repeats
        for i in range(repeats):
            seg = symbols[i*per:(i+1)*per]
            try:
                payload = decode_symbols(seg, order, interleave_depth)
                return parse_payload(payload)
            except Exception as e:
                logging.warning(f"[!] Repeat {i+1} failed: {e}")
        raise ValueError("all repeats failed")
    else:
        payload = decode_symbols(symbols, order, interleave_depth)
        return parse_payload(payload)

# ------------------------
# CLI
# ------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GhostLink decoder: recover text from FSK audio.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("wav", help="Input WAV file")
    p.add_argument("--baud", type=float, default=90.0, help="Symbol rate")
    p.add_argument("--preamble", type=float, default=0.8, help="Preamble seconds to skip")
    p.add_argument("--dense", action="store_true", help="Expect dense 8-FSK (default)")
    p.add_argument("--sparse", action="store_true", help="Expect sparse 4-FSK")
    p.add_argument("--mix-profile", choices=["streaming", "studio"], default="streaming",
                   help="Frequency profile")
    p.add_argument("--interleave", type=int, default=4, help="Interleave depth")
    p.add_argument("--repeats", type=int, default=2, help="Payload repeats")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    return p.parse_args()

def validate_args(args: argparse.Namespace) -> None:
    if not args.wav or not os.path.isfile(args.wav):
        raise FileNotFoundError(args.wav)
    if args.interleave < 1 or args.interleave > 64:
        raise ValueError("interleave depth must be 1..64")
    if args.repeats < 1 or args.repeats > 16:
        raise ValueError("repeats must be 1..16")
    if args.sparse and args.dense:
        raise ValueError("choose either --dense or --sparse")
    if not args.sparse:
        args.dense = True

# ------------------------
# Main
# ------------------------
def main() -> int:
    try:
        args = parse_args()
        setup_logging(args.verbose)
        validate_args(args)
        msg = decode_wav(
            path=args.wav,
            baud=args.baud,
            dense=args.dense and not args.sparse,
            mix_profile=args.mix_profile,
            preamble_s=args.preamble,
            interleave_depth=args.interleave,
            repeats=args.repeats,
        )
        try:
            text = msg.decode("utf-8")
        except Exception:
            text = msg.hex()
        print(text)
        return 0
    except KeyboardInterrupt:
        logging.error("[x] Interrupted by user.")
        return 130
    except Exception as e:
        logging.error(f"[x] Decode failed: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())

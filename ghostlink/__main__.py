#!/usr/bin/env python3
"""
GhostLink: Stealth audio encoder for embedding structured text in music.
Dense-by-default 8-FSK with FEC, codec-safe frequency sets, and SQLite+hash dedupe.

Modes:
  - text: encode a short message from CLI
  - file: encode a single UTF-8 text file
  - dir:  encode all UTF-8 text files in a directory (non-recursive)

Examples:
  ghostlink text "trust_no_one" out/
  python -m ghostlink file ./secret.txt out/ --dense
  ghostlink dir ./payloads/ out/ --sparse --baud 60
  ghostlink text "msg" out/ --mix-profile streaming --amp 0.04 --verbose
"""

import argparse
import array
import binascii
import hashlib
import logging
import math
import os
import sqlite3
import struct
import sys
import time
import wave
from typing import List, Tuple, Iterable, Optional
from .profiles import freq_profile
from .constants import GIB_MAGIC, HISTORY_DB

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
# Helpers
# ------------------------
def ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def list_text_files(dir_path: str) -> List[str]:
    try:
        # Sort for deterministic processing order
        return sorted([
            os.path.join(dir_path, f)
            for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f)) and f.lower().endswith((".txt", ".md", ".log"))
        ])
    except Exception as e:
        logging.error(f"[x] Failed to list directory '{dir_path}': {e}")
        return []

def read_utf8_bytes(src: str, is_literal: bool) -> bytes:
    if is_literal:
        return src.encode("utf-8")
    try:
        with open(src, "rb") as fh:
            data = fh.read()
        # Validate UTF-8 (we'll allow raw bytes if not strict)
        try:
            _ = data.decode("utf-8")
        except UnicodeDecodeError:
            logging.warning("[!] Input not valid UTF-8; encoding raw bytes anyway.")
        return data
    except Exception as e:
        logging.error(f"[x] Failed to read file '{src}': {e}")
        raise

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# ------------------------
# Hamming(7,4) FEC
# ------------------------
def _calc_hamming74(nibble: int) -> Tuple[int, int, int, int, int, int, int]:
    """Return Hamming(7,4) encoding for a single nibble."""
    d3 = (nibble >> 3) & 1
    d2 = (nibble >> 2) & 1
    d1 = (nibble >> 1) & 1
    d0 = nibble & 1
    p1 = d3 ^ d2 ^ d0
    p2 = d3 ^ d1 ^ d0
    p3 = d2 ^ d1 ^ d0
    return p1, p2, d3, p3, d2, d1, d0


# Precompute all 16 possible encoded nibbles for fast lookup
HAMMING74_ENCODE_TABLE: Tuple[Tuple[int, ...], ...] = tuple(
    _calc_hamming74(n) for n in range(16)
)


def hamming74_encode_nibble(nibble: int) -> List[int]:
    """Encode a nibble using Hamming(7,4) with a table lookup."""
    if nibble < 0 or nibble > 0xF:
        raise ValueError("Nibble must be 0..15")
    return list(HAMMING74_ENCODE_TABLE[nibble])

def bytes_to_bits(b: bytes) -> List[int]:
    bits = []
    for byte in b:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits

def hamming74_encode_bytes(b: bytes) -> List[int]:
    bits = bytes_to_bits(b)
    # To nibbles
    nibs = []
    for i in range(0, len(bits), 4):
        chunk = bits[i:i+4]
        if len(chunk) < 4:
            chunk += [0] * (4 - len(chunk))
        nibble = (chunk[0] << 3) | (chunk[1] << 2) | (chunk[2] << 1) | (chunk[3] << 0)
        nibs.append(nibble)
    out = []
    for n in nibs:
        out.extend(HAMMING74_ENCODE_TABLE[n])
    return out

def interleave(bits: List[int], depth: int) -> List[int]:
    if depth <= 1:
        return bits
    rows = depth
    cols = (len(bits) + rows - 1) // rows
    padded = bits + [0] * (rows * cols - len(bits))
    # Read by columns
    out = []
    for c in range(cols):
        for r in range(rows):
            out.append(padded[r * cols + c])
    return out

# ------------------------
# Symbol mapping (4-FSK, 8-FSK)
# ------------------------
def bits_to_symbols(bits: List[int], order: int) -> List[int]:
    if order not in (4, 8):
        raise ValueError("order must be 4 or 8")
    k = 2 if order == 4 else 3
    bits_copy = bits[:]
    pad = (-len(bits_copy)) % k
    if pad:
        bits_copy += [0] * pad
    symbols = []
    for i in range(0, len(bits_copy), k):
        val = 0
        for j in range(k):
            val = (val << 1) | bits_copy[i + j]
        symbols.append(val)  # 0..3 or 0..7
    return symbols

# ------------------------
# Audio synthesis
# ------------------------
def raised_cosine_env(total_samples: int, ramp_samples: int) -> List[float]:
    if ramp_samples <= 0 or 2 * ramp_samples >= total_samples:
        return [1.0] * total_samples
    env = [0.0] * total_samples
    for n in range(ramp_samples):
        env[n] = 0.5 * (1 - math.cos(math.pi * (n / ramp_samples)))
    for n in range(ramp_samples, total_samples - ramp_samples):
        env[n] = 1.0
    for n in range(total_samples - ramp_samples, total_samples):
        k = total_samples - 1 - n
        env[n] = 0.5 * (1 - math.cos(math.pi * (k / ramp_samples)))
    return env

def synth_tone(freq: float, sr: int, duration_s: float, amp: float,
               phase0: float, ramp_ms: float = 5.0, bit_depth: int = 16) -> Tuple[bytes, float]:
    total = max(1, int(round(duration_s * sr)))
    ramp = int((ramp_ms / 1000.0) * sr)
    env = raised_cosine_env(total, ramp)
    two_pi_over_sr = 2.0 * math.pi / sr
    out = []
    phase = phase0
    
    if bit_depth == 32:
        # 32-bit float format
        for i in range(total):
            s = math.sin(phase) * amp * env[i]
            out.append(s)  # Keep as float for 32-bit
            phase += two_pi_over_sr * freq
            if phase > 1e6:
                phase = math.fmod(phase, 2.0 * math.pi)
        return struct.pack("<" + "f" * len(out), *out), phase
    elif bit_depth == 24:
        # 24-bit PCM format
        pcm_bytes = bytearray()
        for i in range(total):
            s = math.sin(phase) * amp * env[i]
            val = max(-8388608, min(8388607, int(round(s * 8388607.0))))
            # Pack as 3 bytes little-endian
            pcm_bytes.extend(struct.pack("<i", val)[:3])  # Take first 3 bytes of 4-byte int
            phase += two_pi_over_sr * freq
            if phase > 1e6:
                phase = math.fmod(phase, 2.0 * math.pi)
        return bytes(pcm_bytes), phase
    else:
        # 16-bit PCM format (original)
        for i in range(total):
            s = math.sin(phase) * amp * env[i]
            val = max(-32768, min(32767, int(round(s * 32767.0))))
            out.append(val)
            phase += two_pi_over_sr * freq
            if phase > 1e6:
                phase = math.fmod(phase, 2.0 * math.pi)
        return struct.pack("<" + "h" * len(out), *out), phase

def symbols_to_audio(symbols: List[int], freqs: List[float], sr: int, baud: float,
                     amp: float, phase0: float = 0.0,
                     gap_ms: float = 0.0, ramp_ms: float = 5.0, bit_depth: int = 16) -> Tuple[bytes, float]:
    sym_dur = 1.0 / float(baud)
    gap_s = max(0.0, gap_ms / 1000.0)
    buff = bytearray()
    phase = phase0
    for s in symbols:
        f = freqs[s]
        tone, phase = synth_tone(f, sr, sym_dur, amp, phase, ramp_ms=ramp_ms, bit_depth=bit_depth)
        buff.extend(tone)
        if gap_s > 0:
            silence, phase = synth_tone(0.0, sr, gap_s, 0.0, phase, ramp_ms=0.0, bit_depth=bit_depth)
            buff.extend(silence)
    return bytes(buff), phase

def write_wav(path: str, sr: int, pcm: bytes, bit_depth: int = 16, channels: int = 1) -> None:
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        if bit_depth == 32:
            wf.setsampwidth(4)  # 4 bytes for 32-bit float
        elif bit_depth == 24:
            wf.setsampwidth(3)  # 3 bytes for 24-bit PCM
        else:
            wf.setsampwidth(2)  # 2 bytes for 16-bit PCM
        wf.setframerate(sr)
        
        if channels == 2:
            # For stereo, duplicate mono signal to both channels
            if bit_depth == 32:
                # Unpack float samples, duplicate each, repack
                sample_count = len(pcm) // 4
                samples = struct.unpack("<" + "f" * sample_count, pcm)
                stereo_samples = []
                for sample in samples:
                    stereo_samples.extend([sample, sample])  # L, R
                pcm = struct.pack("<" + "f" * len(stereo_samples), *stereo_samples)
            elif bit_depth == 24:
                # For 24-bit, manually duplicate each 3-byte sample
                stereo_pcm = bytearray()
                for i in range(0, len(pcm), 3):
                    sample_bytes = pcm[i:i+3]
                    stereo_pcm.extend(sample_bytes)  # L channel
                    stereo_pcm.extend(sample_bytes)  # R channel
                pcm = bytes(stereo_pcm)
            else:
                # Unpack 16-bit samples, duplicate each, repack
                sample_count = len(pcm) // 2
                samples = struct.unpack("<" + "h" * sample_count, pcm)
                stereo_samples = []
                for sample in samples:
                    stereo_samples.extend([sample, sample])  # L, R
                pcm = struct.pack("<" + "h" * len(stereo_samples), *stereo_samples)
        
        wf.writeframes(pcm)


def stretch_audio(samples: bytes, factor: float) -> bytes:
    """Resample PCM data to ``factor`` of its original speed.

    ``factor`` < 1.0 slows the audio. Linear interpolation is used between
    adjacent samples to avoid artifacts.
    """
    if factor <= 0:
        raise ValueError("factor must be positive")

    src = array.array("h")
    src.frombytes(samples)
    n = len(src)
    if n == 0:
        return b""

    out_len = int(round(n / factor))
    out = array.array("h", [0] * out_len)
    for i in range(out_len):
        pos = i * factor
        i0 = int(math.floor(pos))
        frac = pos - i0
        if i0 >= n - 1:
            sample = src[-1]
        else:
            s0 = src[i0]
            s1 = src[i0 + 1]
            sample = int(round(s0 + (s1 - s0) * frac))
        out[i] = sample
    return out.tobytes()

# ------------------------
# Framing / payload
# ------------------------
def build_payload(user_bytes: bytes) -> bytes:
    magic = GIB_MAGIC
    length = struct.pack(">I", len(user_bytes))
    crc = struct.pack(">I", binascii.crc32(user_bytes) & 0xFFFFFFFF)
    return magic + length + user_bytes + crc

def preamble(freqs: List[float], sr: int, amp: float, seconds: float, bit_depth: int = 16) -> Tuple[bytes, float]:
    if seconds <= 0:
        return b"", 0.0
    per = max(0.05, seconds / len(freqs))
    out = bytearray()
    phase = 0.0
    for f in freqs:
        t, phase = synth_tone(f, sr, per, amp, phase, bit_depth=bit_depth)
        out.extend(t)
    return bytes(out), phase

# ------------------------
# Frequency profiles (codec-safe by design)
# ------------------------
# ------------------------
# SQLite logging & dedupe
# ------------------------
def db_init(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS encodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc INTEGER NOT NULL,
            mode TEXT NOT NULL,
            input_ref TEXT NOT NULL,
            framed_sha256 TEXT NOT NULL UNIQUE,
            bytes_len INTEGER NOT NULL,
            samplerate INTEGER NOT NULL,
            baud REAL NOT NULL,
            amp REAL NOT NULL,
            dense INTEGER NOT NULL,
            mix_profile TEXT NOT NULL,
            freqs TEXT NOT NULL,
            wav_path TEXT NOT NULL,
            crc32_hex TEXT NOT NULL
        );
        """)
        conn.commit()
    finally:
        conn.close()

def db_has_hash(db_path: str, h: str) -> Tuple[bool, str]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT wav_path FROM encodes WHERE framed_sha256 = ?", (h,))
        row = cur.fetchone()
        if row:
            return True, row[0]
        return False, ""
    finally:
        conn.close()

def db_insert(db_path: str, mode: str, input_ref: str, h: str, bytes_len: int,
              samplerate: int, baud: float, amp: float, dense: bool, mix_profile: str,
              freqs: List[float], wav_path: str, crc_hex: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        INSERT INTO encodes
        (ts_utc, mode, input_ref, framed_sha256, bytes_len, samplerate, baud, amp, dense, mix_profile, freqs, wav_path, crc32_hex)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(time.time()), mode, input_ref, h, bytes_len, samplerate, float(baud),
            float(amp), 1 if dense else 0, mix_profile,
            ",".join(f"{x:.2f}" for x in freqs),
            os.path.abspath(wav_path), crc_hex
        ))
        conn.commit()
    finally:
        conn.close()


def db_remove_hash(db_path: str, h: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM encodes WHERE framed_sha256 = ?", (h,))
        conn.commit()
    finally:
        conn.close()

# ------------------------
# Core encode
# ------------------------
def encode_bytes_to_wav(user_bytes: bytes, out_dir: str, base_name_hint: str,
                        samplerate: int, baud: float, amp: float,
                        dense: bool, mix_profile: str,
                        gap_ms: float, preamble_s: float, interleave_depth: int,
                        repeats: int, ramp_ms: float,
                        out_name: Optional[str] = None) -> Tuple[str, bool]:
                        repeats: int, ramp_ms: float, bit_depth: int = 16, channels: int = 1) -> Tuple[str, bool]:
    """
    Returns (output_path, skipped_by_dedupe)
    """
    payload = build_payload(user_bytes)
    framed_hash = sha256_hex(payload)
    crc_hex = f"{binascii.crc32(user_bytes) & 0xFFFFFFFF:08x}"

    ensure_dir(out_dir)
    db_path = os.path.abspath(HISTORY_DB)
    db_init(db_path)

    exists, prior_path = db_has_hash(db_path, framed_hash)
    if exists:
        if prior_path and os.path.isfile(prior_path):
            logging.info(f"[i] Duplicate payload detected (sha256={framed_hash[:12]}). Skipping; existing file: {prior_path}")
            return prior_path, True
        # Stale entry: hash exists in DB but file is missing
        logging.info(
            f"[i] Stale DB entry detected for sha256={framed_hash[:12]} (missing file: {prior_path}). Cleaning up."
        )
        try:
            db_remove_hash(db_path, framed_hash)
        except Exception as e:
            logging.warning(f"[!] Failed to remove stale DB entry: {e}")

    freqs = freq_profile(dense, mix_profile)
    order = 8 if dense else 4

    # FEC + interleave
    bits = hamming74_encode_bytes(payload)
    if interleave_depth > 1:
        bits = interleave(bits, interleave_depth)
    symbols = bits_to_symbols(bits, order)

    midi_notes: List[int] = []
    for _ in range(max(1, repeats)):
        for sym in symbols:
            freq = freqs[sym]
            note = int(round(69 + 12 * math.log2(freq / 440.0)))
            midi_notes.append(note)

    total_symbols = len(symbols) * max(1, repeats)
    est_s = total_symbols / baud + preamble_s
    logging.info(f"[i] Mode={'8-FSK' if dense else '4-FSK'} | Freqs={','.join(f'{f:.0f}' for f in freqs)}Hz "
                 f"| SR={samplerate}Hz | Baud={baud:.1f} | Amp={amp:.3f} | {bit_depth}-bit {'stereo' if channels == 2 else 'mono'} "
                 f"| Interleave={interleave_depth} | Repeats={repeats}")
    logging.info(f"[i] Payload bytes={len(user_bytes)} | Framed bytes≈{len(payload)} | Symbols={len(symbols)} "
                 f"| Est duration≈{est_s:.1f}s")

    # Synthesize
    pcm = bytearray()
    phase = 0.0
    if preamble_s > 0.0:
        pre_pcm, phase = preamble(freqs, samplerate, amp, preamble_s, bit_depth=bit_depth)
        pcm.extend(pre_pcm)
    for _ in range(max(1, repeats)):
        tones, phase = symbols_to_audio(symbols, freqs, samplerate, baud, amp, phase,
                                       gap_ms=gap_ms, ramp_ms=ramp_ms, bit_depth=bit_depth)
        pcm.extend(tones)

    # Determine output filename
    safe_hint = "".join(c for c in base_name_hint if c.isalnum() or c in ("-", "_"))[:40] or "msg"
    if out_name:
        if not out_name.lower().endswith(".wav"):
            out_name = f"{out_name}.wav"
    else:
        out_name = f"{safe_hint}_{framed_hash[:12]}.wav"
    logging.info(f"[i] Output filename: {out_name}")
    out_path = os.path.join(out_dir, out_name)

    try:
        write_wav(out_path, samplerate, bytes(pcm), bit_depth=bit_depth, channels=channels)
    except Exception as e:
        logging.error(f"[x] Failed to write WAV: {e}")
        raise

    # Write MIDI sequence mirroring the symbol frequencies
    try:
        import mido
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
        dur_ticks = max(1, round(mid.ticks_per_beat / baud))
        for note in midi_notes:
            track.append(mido.Message("note_on", note=note, velocity=64, time=0))
            track.append(mido.Message("note_off", note=note, velocity=64, time=dur_ticks))
        mid_path = os.path.splitext(out_path)[0] + ".mid"
        mid.save(mid_path)
    except Exception as e:
        logging.warning(f"[!] Failed to write MIDI: {e}")

    # Read back the written WAV for further processing
    try:
        with wave.open(out_path, "rb") as wf:
            read_sr = wf.getframerate()
            channels = wf.getnchannels()
            pcm_data = wf.readframes(wf.getnframes())
    except Exception as e:
        logging.error(f"[x] Failed to read back WAV: {e}")
        raise

    if channels != 1:
        logging.warning(f"[!] Unexpected channel count: {channels}")

    # Generate slowed variants
    for factor, suffix in {0.75: "slow25", 0.5: "slow50", 0.25: "slow100", 0.1: "slow1000"}.items():
        try:
            stretched = stretch_audio(pcm_data, factor)
            slow_path = os.path.splitext(out_path)[0] + f"_{suffix}.wav"
            write_wav(slow_path, read_sr, stretched)
            logging.info(f"[i] Wrote: {os.path.abspath(slow_path)} (speed={factor:.2f})")
        except Exception as e:
            logging.warning(f"[!] Failed to write slowed WAV {suffix}: {e}")

    # Log run
    try:
        db_insert(db_path, mode="encode", input_ref=base_name_hint, h=framed_hash, bytes_len=len(user_bytes),
                  samplerate=samplerate, baud=baud, amp=amp, dense=dense, mix_profile=mix_profile,
                  freqs=freqs, wav_path=out_path, crc_hex=crc_hex)
    except Exception as e:
        logging.warning(f"[!] Failed to log to SQLite: {e}")

    logging.info(f"[i] Wrote: {os.path.abspath(out_path)} (sha256={framed_hash})")
    return out_path, False

# ------------------------
# CLI
# ------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gibberlink: encode text into dense/sparse FSK audio for stealth embedding.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Positional: mode, input, outdir (per user preference)
    p.add_argument("mode", choices=["text", "file", "dir"], help="Input mode.")
    p.add_argument("input", help="For 'text', the message string. For 'file' or 'dir', a path.")
    p.add_argument("outdir", help="Directory to write output WAV(s) + history DB.")
    # Options
    p.add_argument("--samplerate", type=int, default=48000, help="Output sample rate (Hz).")
    p.add_argument("--baud", type=float, default=90.0, help="Symbol rate (symbols/sec).")
    p.add_argument("--amp", type=float, default=0.06, help="Peak amplitude 0..1. Keep low for stealth.")
    p.add_argument("--dense", action="store_true", help="Use dense 8-FSK (default).")
    p.add_argument("--sparse", action="store_true", help="Use sparse 4-FSK instead of dense.")
    p.add_argument("--mix-profile", choices=["streaming", "studio"], default="streaming",
                   help="Frequency set tuned for survivability.")
    p.add_argument("--preamble", type=float, default=0.8, help="Preamble seconds to aid future decoding.")
    p.add_argument("--gap", type=float, default=0.0, help="Intersymbol gap (ms). Usually 0.")
    p.add_argument("--interleave", type=int, default=4, help="Interleave depth (1=off). Helps against masking.")
    p.add_argument("--repeats", type=int, default=2, help="Repeat the encoded stream N times (>=1).")
    p.add_argument("--ramp", type=float, default=5.0, help="Raised-cosine ramp per symbol (ms).")
    p.add_argument("--out-name", help="Explicit output WAV filename (text/file modes only).")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose logging.")
    # Audio format options
    p.add_argument("--bit-depth", choices=[16, 24, 32], type=int, default=16, 
                   help="Output bit depth: 16 (PCM), 24 (PCM), or 32 (float).")
    p.add_argument("--channels", choices=[1, 2], type=int, default=1,
                   help="Output channels: 1 (mono) or 2 (stereo).")
    args = p.parse_args()

    # Resolve dense/sparse default & conflicts
    if args.sparse and args.dense:
        logging.error("[x] Choose either --dense or --sparse, not both.")
        sys.exit(2)
    if not args.sparse:
        args.dense = True  # default dense

    return args

def validate_args(args: argparse.Namespace) -> None:
    if args.samplerate < 16000 or args.samplerate > 192000:
        logging.error("[x] Samplerate must be in 16k..192k.")
        sys.exit(2)
    if not (0.0 < args.amp <= 1.0):
        logging.error("[x] Amp must be in (0,1].")
        sys.exit(2)
    if args.baud <= 10 or args.baud > 2000:
        logging.error("[x] Baud must be in (10,2000].")
        sys.exit(2)
    if args.interleave < 1 or args.interleave > 64:
        logging.error("[x] Interleave depth must be 1..64.")
        sys.exit(2)
    if args.repeats < 1 or args.repeats > 16:
        logging.error("[x] Repeats must be 1..16.")
        sys.exit(2)
    if args.mode in ("file", "dir") and not os.path.exists(args.input):
        logging.error(f"[x] Input path does not exist: {args.input}")
        sys.exit(2)
    if args.out_name and args.mode == "dir":
        logging.error("[x] --out-name is only valid with 'text' or 'file' modes.")
        sys.exit(2)

def iter_inputs(mode: str, input_arg: str) -> Iterable[Tuple[str, bytes]]:
    if mode == "text":
        try:
            yield ("literal", read_utf8_bytes(input_arg, is_literal=True))
        except Exception as e:
            logging.error(f"[x] Skipping literal input: {e}")
    elif mode == "file":
        try:
            yield (os.path.basename(input_arg), read_utf8_bytes(input_arg, is_literal=False))
        except Exception as e:
            logging.error(f"[x] Skipping '{input_arg}': {e}")
    else:  # dir
        files = list_text_files(input_arg)
        if not files:
            logging.warning("[!] No text files found to encode.")
        for fp in files:
            try:
                yield (os.path.basename(fp), read_utf8_bytes(fp, is_literal=False))
            except Exception as e:
                logging.error(f"[x] Skipping '{fp}': {e}")

def main_with_args(args) -> int:
    """Main function that accepts pre-parsed arguments (for API use)"""
    setup_logging(args.verbose)
    validate_args(args)

    ensure_dir(args.outdir)

    made = 0
    skipped = 0
    for name_hint, content in iter_inputs(args.mode, args.input):
        try:
            out_path, was_skipped = encode_bytes_to_wav(
                user_bytes=content,
                out_dir=args.outdir,
                base_name_hint=name_hint if name_hint != "literal" else "msg",
                samplerate=args.samplerate,
                baud=args.baud,
                amp=args.amp,
                dense=args.dense and not args.sparse,
                mix_profile=args.mix_profile,
                gap_ms=args.gap,
                preamble_s=args.preamble,
                interleave_depth=args.interleave,
                repeats=args.repeats,
                ramp_ms=args.ramp,
                out_name=args.out_name
                bit_depth=args.bit_depth,
                channels=args.channels
            )
            if was_skipped:
                skipped += 1
            else:
                made += 1
        except KeyboardInterrupt:
            logging.error("[x] Interrupted by user.")
            return 130
        except Exception as e:
            logging.error(f"[x] Encode failed for '{name_hint}': {e}")

    logging.info(f"[i] Done. Created={made} Skipped={skipped}")
    return 0

def main() -> int:
    args = parse_args()
    return main_with_args(args)

if __name__ == "__main__":
    sys.exit(main())


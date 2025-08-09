# GhostLink — Stealth Text-to-Audio Encoder (Dense 8-FSK)

## Overview
GhostLink hides structured text inside audio as carefully band-placed FSK tones designed to survive consumer playback chains and lossy streaming codecs. It defaults to **dense 8-FSK** with forward error correction, interleaving, and repeats for robustness; a 4-FSK mode is available for extra margin.

### Key Properties
- **Codec-safe by design:** carriers live in 1.5–5 kHz (“streaming” profile, default) or 1.8–6 kHz (“studio”).
- **Dense by default:** 8-FSK + Hamming(7,4) + interleaving + optional repeats.
- **Hash-based dedupe:** payload frame SHA-256 is the unique key; if a prior identical encode exists on disk, the run is skipped.
- **SQLite history:** every encode (or skip) is tracked in `ghostlink_history.db` in the output directory.
- **No external dependencies:** pure Python 3 standard library.
- **Three input modes:** CLI text, single file, or directory of text files.

## Project Layout

- `ghostlink/` – core package (`__main__.py`, `decoder.py`, `profiles.py`)
- `tests/` – unit tests validating encoding/decoding
- `pyproject.toml` – packaging and script entry points
- `requirements.txt` – placeholder for future dependencies

```
GhostLink/
├── ghostlink/
├── tests/
├── pyproject.toml
└── requirements.txt
```

---

## Install

### Prerequisites
- Python 3.8+ (recommended 3.10+)
- macOS, Linux, or Windows

### Clone & Prepare
```bash
git clone https://github.com/13alvone/GhostLink.git
cd GhostLink
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install .
```
---

## Usage

### General Form
```ghostlink <mode> <input> <outdir> [options]```

### Modes
- `text` — Encode a short message passed on CLI
- `file` — Encode a single UTF-8 text file
- `dir` — Encode all files in a directory (non-recursive, processed in sorted order for determinism)

### Examples
```
# 1) Quick start: CLI text -> out/
ghostlink text "trust_no_one" out/

# 2) Single file, dense defaults, streaming-safe band
ghostlink file ./secret.txt out/

# 3) Directory batch; sparse 4-FSK; slightly slower baud
ghostlink dir ./payloads out/ --sparse --baud 60

# 4) Louder lab test run (don’t do this in a real mix)
ghostlink text "HELLO" out/ --amp 0.2 -v

# 5) Studio profile (a bit brighter), higher baud
ghostlink text "msg" out/ --mix-profile studio --baud 120
```

### Decoding
# Recover text from a GhostLink WAV
```ghostlink-decode out/msg_ce67eacbbb93.wav```

---

## Important Options
- `--dense` / `--sparse`  
  Selects 8-FSK (default) or 4-FSK. Dense increases throughput; sparse increases separation.
- `--mix-profile {streaming|studio}`  
  - **streaming** (default): carriers in ~1.5–5 kHz for survival across MP3/AAC/OGG + cheap speakers  
  - **studio**: ~1.8–6 kHz, slightly brighter; still conservative
- `--samplerate <int>`  
  Output sample rate in Hz (default 48000). Range: 16000–192000. Higher rates provide more frequency resolution but larger files.
- `--baud <float>`  
  Symbols per second (default 90). Raise for shorter files, lower for maximum safety.
- `--interleave <int>`  
  Time interleaving depth (default 4). Helps when short segments are masked by transients.
- `--repeats <int>`  
  Repeat the payload N times (default 2). Improves recovery odds in noisy music beds.
- `--amp <float>`  
  Peak amplitude [0..1]. Keep low (0.03–0.08) to remain inaudible in a dense mix.
- `--preamble <seconds>`  
  Training sequence to aid future decoder locking (default 0.8 s).
- `--gap <ms>`, `--ramp <ms>`  
  Intersymbol gap (usually 0) and raised-cosine ramp per symbol to avoid clicks.

---

## Output
Each encode produces:
- `out/<base>_<sha12>.wav` — The audio payload (16-bit mono WAV)
- `out/ghostlink_history.db` — SQLite history of encodes

Filenames include the first 12 hex chars of the framed payload hash (sha256) for traceability.

### Audio Format
- **Current limitation**: GhostLink currently outputs 16-bit mono WAV files only
- **Decoder requirement**: Only accepts 16-bit mono WAV files for decoding
- **Future enhancement**: 32-bit and stereo support planned for future releases

---

## Dedupe Logic
- The unique key is SHA-256 over the framed payload (`magic + length + data + CRC32`).
- If the same payload was already written **and** the target WAV file still exists, GhostLink skips re-encoding.
- Skips and writes are both recorded in SQLite (writes as rows; skips are implied by the UNIQUE constraint + presence check).

---

## Recommended Mix Practices
- Render GhostLink track at low gain (`amp 0.03–0.06`) and tuck beneath steady, broadband content (pads, room tone, cymbal wash).
- Keep the carriers unobvious: avoid boosting 1.5–5 kHz with mastering EQ; a gentle shelf down can help.
- Avoid ultrasonics (>16 kHz); streaming codecs often remove them entirely.
- If worried about dropout under heavy compression, increase `--repeats` or `--interleave` rather than cranking `amp`.

---

## Security / Robustness Notes
- **Hamming(7,4)** corrects single-bit errors per nibble; interleave spreads bursts; repeats add diversity.
- **CRC32** in the frame ensures integrity at decode stage.
- Frequency sets are pre-curated to survive common playback chains; they intentionally avoid sub-1 kHz (masking) and >6 kHz (lossy roll-off).

---

## CLI Reference
```
  ghostlink <mode> <input> <outdir>
      [--samplerate 48000] [--baud 90] [--amp 0.06]
      [--dense|--sparse] [--mix-profile streaming|studio]
      [--preamble 0.8] [--gap 0] [--interleave 4] [--repeats 2] [--ramp 5]
      [-v|--verbose]
  ghostlink-decode <wavfile>
      [--baud 90] [--dense|--sparse] [--mix-profile streaming|studio]
      [--preamble 0.8] [--interleave 4] [--repeats 2] [-v|--verbose]
```

**Audio Format Notes:**
- Output is always 16-bit mono WAV at the specified sample rate
- Decoder only accepts 16-bit mono WAV files
- Sample rate can be configured (16kHz-192kHz range)

**Return codes:**
- `0`   success
- `2`   validation or runtime error
- `130` interrupted (Ctrl-C)

---

## FAQ
**Q:** Can I guarantee zero frequency loss on every platform?  
**A:** No one can—playback chains vary wildly. GhostLink mitigates this by:
1. Confining carriers to a proven codec-survivable band.
2. Spacing carriers to reduce intermod/aliasing issues.
3. Using interleaving + repeats so partial losses don’t kill the message.

**Q:** Why only 16-bit mono WAV output?  
**A:** Current implementation prioritizes simplicity and compatibility. 16-bit mono is universally supported and sufficient for the FSK encoding. 32-bit float and stereo support are planned for future releases to enable higher-quality embedding in professional workflows.

**Q:** Will you provide a decoder?  
**A:** Yes—next iteration can include Goertzel-based symbol detection, timing recovery, and CRC/FEC verification as a sister tool.

---

## License
This project is licensed under the [MIT License](LICENSE).


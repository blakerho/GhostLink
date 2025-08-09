# GhostLink — Stealth Text-to-Audio Encoder (Dense 8-FSK)

## Overview
GhostLink hides structured text inside audio as carefully band-placed FSK tones designed to survive consumer playback chains and lossy streaming codecs.  
It defaults to **dense 8-FSK** with forward error correction, interleaving, and repeats for robustness; a 4-FSK mode is available for extra margin.

### Key Properties
- **Codec-safe by design:** carriers live in 1.5–5 kHz (“streaming” profile, default) or 1.8–6 kHz (“studio”).
- **Dense by default:** 8-FSK + Hamming(7,4) + interleaving + optional repeats.
- **Hash-based dedupe:** payload frame SHA-256 is the unique key; if a prior identical encode exists on disk, the run is skipped.
- **SQLite history:** every encode (or skip) is tracked in `ghostlink_history.db` in the output directory.
- **No external dependencies:** pure Python 3 standard library.
- **Three input modes:** CLI text, single file, or directory of text files.

---

## Install

### Prerequisites
- Python 3.8+ (recommended 3.10+)
- macOS, Linux, or Windows
- **ffmpeg** is NOT required (GhostLink writes standard PCM WAV)

### Clone & Prepare
\tgit clone <your-repo-url>
\tcd <repo>
\tpython3 -m venv .venv
\t. .venv/bin/activate     # Windows: .venv\Scripts\activate
\tpip install -r requirements.txt
\tchmod +x ghostlink.py

---

## Usage

### General Form
\t./ghostlink.py <mode> <input> <outdir> [options]

### Modes
- `text` — Encode a short message passed on CLI
- `file` — Encode a single UTF-8 text file
- `dir` — Encode all files in a directory (non-recursive)

### Examples
\t# 1) Quick start: CLI text -> out/
\t./ghostlink.py text "trust_no_one" out/

\t# 2) Single file, dense defaults, streaming-safe band
\t./ghostlink.py file ./secret.txt out/

\t# 3) Directory batch; sparse 4-FSK; slightly slower baud
\t./ghostlink.py dir ./payloads out/ --sparse --baud 60

\t# 4) Louder lab test run (don’t do this in a real mix)
\t./ghostlink.py text "HELLO" out/ --amp 0.2 -v

\t# 5) Studio profile (a bit brighter), higher baud
\t./ghostlink.py text "msg" out/ --mix-profile studio --baud 120

---

## Important Options
- `--dense` / `--sparse`  
  Selects 8-FSK (default) or 4-FSK. Dense increases throughput; sparse increases separation.
- `--mix-profile {streaming|studio}`  
  - **streaming** (default): carriers in ~1.5–5 kHz for survival across MP3/AAC/OGG + cheap speakers  
  - **studio**: ~1.8–6 kHz, slightly brighter; still conservative
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
- `out/<base>_<sha12>.wav` — The audio payload
- `out/ghostlink_history.db` — SQLite history of encodes

Filenames include the first 12 hex chars of the framed payload hash (sha256) for traceability.

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
\t./ghostlink.py <mode> <input> <outdir>
\t    [--samplerate 48000] [--baud 90] [--amp 0.06]
\t    [--dense|--sparse] [--mix-profile streaming|studio]
\t    [--preamble 0.8] [--gap 0] [--interleave 4] [--repeats 2] [--ramp 5]
\t    [-v|--verbose]

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

**Q:** Will you provide a decoder?  
**A:** Yes—next iteration can include Goertzel-based symbol detection, timing recovery, and CRC/FEC verification as a sister tool.

---

## License
MIT (insert your preferred license here)


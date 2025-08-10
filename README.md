# GhostLink — Stealth Text-to-Audio Encoder (GibberLink Protocol, Dense 8-FSK)

## Overview
GhostLink hides structured text inside audio using the **GibberLink** protocol — carefully band-placed FSK tones designed to survive consumer playback chains and lossy streaming codecs. It ships with two command-line tools: `ghostlink` for encoding and `ghostlink-decode` for recovering messages.
It defaults to **dense 8-FSK** with forward error correction, interleaving, and repeats for robustness; a 4-FSK mode is available for extra margin.

### Key Properties
- **Codec-safe by design:** carriers live in 1.5–5 kHz (“streaming” profile, default) or 1.8–6 kHz (“studio”).
- **Dense by default:** 8-FSK + Hamming(7,4) + interleaving + optional repeats.
- **Hash-based dedupe:** payload frame SHA-256 is the unique key; if a prior identical encode exists on disk, the run is skipped.
- **SQLite history:** every encode (or skip) is tracked in a project-root `ghostlink_history.db`, providing a global log across all runs.
- **Lightweight dependency:** uses `mido` to emit companion MIDI files.
- **Three input modes:** CLI text, single file, or directory of text files.

## Project Layout

- `ghostlink/` – core package providing the `ghostlink` and `ghostlink-decode` CLIs (`__main__.py`, `decoder.py`, `profiles.py`)
- `ghostFace/` – **modern web interface** with one-click app for easy encoding/decoding
- `tests/` – unit tests validating encoding/decoding
- `pyproject.toml` – packaging and script entry points
- `requirements.txt` – placeholder for future dependencies

	GhostLink/
	├── ghostlink/          # Core CLI tools
	├── ghostFace/          # 🎯 Web interface & one-click app
	├── tests/              # Unit tests
	├── pyproject.toml      # Package configuration
	└── requirements.txt    # Dependencies

---

## 🚀 **Quick Start with GhostFace (Recommended)**

For the easiest experience, use our modern web interface:

1. **Clone the repository**
   ```bash
   git clone https://github.com/13alvone/GhostLink.git
   cd GhostLink/ghostFace
   ```

2. **Double-click `GhostFace.app`** (macOS)
   - Or run `python3 launch.py` (all platforms)
   - Your browser opens automatically to http://localhost:5001

3. **Install components** if needed (one-click from the web interface)

4. **Start encoding and decoding!**

See `ghostFace/README_Web_Interface.md` for detailed instructions.

---

## Install (Command Line)

### Prerequisites
- Python 3.8+ (recommended 3.10+)
- macOS, Linux, or Windows

### Clone & Prepare
```bash
git clone https://github.com/blakerho/GhostLink.git
cd GhostLink
python3 -m venv .venv
source .venv/bin/activate  # Windows is trash
pip install .
```
---

## Usage

### General Form
	ghostlink <mode> <input> <outdir> [options]
	ghostlink-decode <wavfile> [options]

### Modes
- `text` — Encode a short message passed on CLI
- `file` — Encode a single UTF-8 text file
- `dir` — Encode all files in a directory (non-recursive, processed in sorted order for determinism)

### Examples
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

        # 6) Custom filename; generates WAV, slowed variants, and MIDI
        ghostlink text "hi" out/ --out-name secret.wav

        # 7) Decode a GhostLink (GibberLink protocol) WAV back to text
        ghostlink-decode out/msg_ce67eacbbb93.wav -v

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
- `--out-name <file.wav>`
  Override the auto-generated base name. Useful when embedding in a project;
  slowed variants (`*_slow25.wav`, `*_slow50.wav`, `*_slow100.wav`, `*_slow1000.wav` ≈10×) and the
  companion MIDI file use the same prefix.
- `--bit-depth {16|24|32}`  
  Output bit depth: 16-bit PCM (default), 24-bit PCM, or 32-bit float.
- `--channels {1|2}`  
  Output channels: 1 (mono, default) or 2 (stereo).

---

## Output
Each encode produces:
- `out/<base>_<sha12>.wav` — The audio payload
- `out/<base>_<sha12>_slow25.wav` — 25% slower (duration ×4/3)
- `out/<base>_<sha12>_slow50.wav` — 50% slower (duration ×2)
- `out/<base>_<sha12>_slow100.wav` — 100% slower (duration ×4)
- `out/<base>_<sha12>_slow1000.wav` — one-tenth speed (duration ×10)
- `out/<base>_<sha12>.mid` — MIDI rendering of the carrier sequence
- `ghostlink_history.db` — SQLite history of all encodes, stored in the project root

Filenames include the first 12 hex chars of the framed payload hash (sha256) for traceability.

## Interoperability
All WAV files generated by GhostLink follow the GibberLink framing, FSK mapping, and CRC/FEC scheme.  
Any decoder that implements the GibberLink specification can recover the embedded text, and future revisions will preserve backward compatibility.

### Audio Format Support
- **Bit depths**: 16-bit PCM, 24-bit PCM, or 32-bit float
- **Channels**: Mono or stereo output
- **Decoder compatibility**: Automatically detects and supports all formats
- **Default**: 16-bit mono for maximum compatibility


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
      [--bit-depth 16|24|32] [--channels 1|2] [-v|--verbose]
  ghostlink-decode <wavfile>
      [--baud 90] [--dense|--sparse] [--mix-profile streaming|studio]
      [--preamble 0.8] [--interleave 4] [--repeats 2] [-v|--verbose]
```

**Audio Format Notes:**
- Output supports 16-bit PCM, 24-bit PCM, or 32-bit float
- Mono or stereo output supported
- Decoder automatically detects and supports all formats
- Sample rate can be configured (16kHz-192kHz range)
- Default: 16-bit mono for maximum compatibility

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

**Q:** What audio formats are supported?  
**A:** GhostLink supports 16-bit PCM, 24-bit PCM, and 32-bit float in both mono and stereo configurations. The decoder automatically detects the format. 16-bit mono is the default for maximum compatibility across playback systems.

**Q:** Will you provide a decoder?  
**A:** Yes—GhostLink includes a decoder CLI (`ghostlink-decode`) implementing Goertzel-based symbol detection, timing recovery, and CRC/FEC verification.

---

## License
This project is licensed under the [MIT License](LICENSE).

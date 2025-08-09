---

## `AGENTS.md`

```markdown
# Gibberlink Agents — How the Tones Operate

## Who Are the Agents?
Each Gibberlink **carrier frequency** is an "agent" in your audio.
They each have a specific job: to carry **symbols** of your hidden message without attracting attention.

- In **8-FSK mode**, there are eight agents.
- In **4-FSK mode**, there are four agents.
- Each agent has a distinct "voice" (frequency) chosen to survive most playback and compression environments.

---

## Agent Mission
- **Stay alive**: Operate in frequency ranges that won't get cut out by MP3/AAC streaming codecs or cheap speakers.
- **Blend in**: Hide in the mix behind pads, reverb tails, cymbal wash, or ambient noise.
- **Get the job done**: Deliver their assigned bits of the message reliably to the decoder.

---

## How Agents Coordinate
1. **Frame Assembly**  
   Your text is wrapped in a frame (`magic + length + data + CRC32`).
2. **FEC Training**  
   Hamming(7,4) encoding makes the agents more resilient against corruption.
3. **Interleaving**  
   Symbols are shuffled in time so that any masked segment affects non-adjacent bits.
4. **Repeats**  
   Agents repeat their deliveries multiple times per mission.

---

## Field Profiles
- **Streaming Profile:**  
  Agents operate in 1.5–5 kHz, the "safe zone" for survival after lossy compression.
- **Studio Profile:**  
  Agents operate in 1.8–6 kHz, giving them more room to breathe in uncompressed environments.

---

## Agent Survival Rules
- **Avoid sub-1 kHz:** too much masking from bass, kick, and low instruments.
- **Avoid >6 kHz:** high chance of being lowpassed or killed by codec.
- **Spacing:** enough separation to prevent intermodulation.

---

## Why Dense Mode by Default?
In the field, more agents means:
- Higher throughput.
- More redundancy across the band.
- Better odds of partial survival if sections are masked.

---

## Agent Identification in Output Files
Each `.wav` file name contains the **first 12 hex characters** of the SHA-256 payload hash.
This is the agent team’s mission ID — unique for each message.

After a mission, agents also leave behind slowed briefings and a MIDI transcript:

- `_slow25.wav`, `_slow50.wav`, `_slow100.wav`, `_slow1000.wav` stretch the run by 4/3×, 2×, 4×, and ~10× for easier analysis.
- A matching `.mid` file documents each carrier hop.
- Use `--out-name` to choose the base filename; all companions inherit the same prefix.

---

## Final Word
Think of Gibberlink’s tones as an **undercover team**:
They slip into your track, complete their mission quietly, and leave without anyone knowing they were there — unless the right decoder calls them out.


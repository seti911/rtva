# 🎙️ Push-To-Talk Voice Assistant

## Quick Start

```bash
cd /home/stef/Development/localAI/rtva
source venv/bin/activate
python3 test_live_microphone.py
```

## Controls

| Key | Action |
|-----|--------|
| **SPACE** | Press and **HOLD** to record, release to send |
| **Q** | Quit the application |

## How It Works

1. **Press SPACE** → Microphone activates (shows 🔴 RECORDING)
2. **Speak** → Real-time level meter shows your voice
3. **Release SPACE** → Recording stops, audio sent to STT
4. **Wait** → STT transcribes, LLM responds, TTS plays
5. **Repeat** → Press SPACE again for next turn

## Example Session

```
Press and HOLD 'space' to record, release to stop

───────────────────────────────────────────────────────────
TURN 1
───────────────────────────────────────────────────────────

🔴 RECORDING...
  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0.245
  ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0.267
  ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0.268
  
⏹️  STOPPED

✓ Recorded 3.2 seconds

📝 Transcribing (Parakeet-TDT)...
✓ You said: "Bonjour, comment allez-vous?"

🧠 Thinking (CroissantLLM)...
✓ AI said: "Bonjour! Je vais bien, merci de demander."

🔊 Synthesizing speech (XTTS v2)...
✓ Generated audio
🎵 Playing...

✓ Done
```

## Advantages Over Silence Detection

- ✅ **Instant feedback** - No waiting for silence detection
- ✅ **Natural timing** - You control when to start/stop
- ✅ **No latency** - No delay waiting for timeout
- ✅ **Precise control** - Exactly what you want recorded
- ✅ **Works with background noise** - No interference from ambient sound
- ✅ **Familiar UX** - Like Walkie-Talkies or Radio

## Tips

1. **Speak clearly** when SPACE is held
2. **Release immediately** after finishing to minimize silence
3. **Press SPACE again** for next question (no menu navigation needed)
4. **Keep audio short** - LLM responds faster to brief prompts
5. **Use French** - Optimized for French language

## Keyboard Requirements

- Linux/Mac: Works with any keyboard
- Windows: May need to run as Administrator for keyboard capture
- SSH/Remote: Requires local keyboard (won't work over SSH)

## Troubleshooting

### Q: Keyboard input not detected?
A: Try running with sudo (or as Administrator on Windows)

### Q: Still have background noise issues?
A: Just press SPACE more briefly - only record your speech

### Q: How do I adjust recording sensitivity?
A: Current implementation records everything while SPACE is held
   → No adjustments needed, you control it!

---

**Enjoy natural conversations! Press SPACE and speak! 🚀**

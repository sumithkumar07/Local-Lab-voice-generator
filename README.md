# 🎙️ Local Lab - AI Voice Generator

**A high-performance, local-first text-to-speech engine optimized for consumer hardware.**

Local Lab provides a seamless, private interface for generating natural-sounding narration using state-of-the-art neural TTS models. It operates entirely on-device, ensuring zero data leakage and extreme low-latency performance.

---

## ⚡ Technical Performance (RTF)

The engine provides two distinct operating modes, verified for real-time performance on mid-range consumer hardware.

| Mode | Model Architecture | Real-Time Factor (RTF) | Accuracy | Device |
| :--- | :--- | :--- | :--- | :--- |
| **Standard** | Kokoro-82M (v0.1) | **~0.08** (12.5x faster than real-time) | High | CPU/GPU |
| **Pro** | StyleTTS 2 (Hardened) | **~0.42** (2.4x faster than real-time) | Premium | NVIDIA |

---

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎤 **20+ Voices** | American, British, Hindi accents |
| ⚡ **Standard Mode** | Fast, works on any PC (Kokoro-82M) |
| 🚀 **Pro Mode** | Premium quality for NVIDIA GPUs (StyleTTS 2) |
| 📥 **Export** | Download as WAV or MP3 |
| 🎚️ **Speed Control** | 0.5x to 2.0x |
| 💻 **100% Local** | No internet needed after setup |
| 🔒 **Privacy** | Your text never leaves your computer |

---

## 📦 Installation

### Requirements
- ✅ Windows 10/11
- ✅ Python 3.9+ ([Download](https://python.org))
- ⭐ NVIDIA GPU (optional, for Pro Mode)

### Steps

1. **Download** → Click "Code" → "Download ZIP"
2. **Extract** the ZIP to a folder
3. **Run** `setup.bat` (first time only, installs dependencies)
4. **Run** `start.bat` to launch the app
5. **Open** http://localhost:8000 in your browser

---

## 🎬 How to Use

1. ✏️ Type or paste your script
2. 🎤 Select a voice (hover to preview!)
3. 🎚️ Adjust speed if needed
4. 🎬 Click **Generate Voice**
5. 📥 Download your audio!

---

## 💡 Pro Tips

- Use `...` for dramatic pauses
- Keep sentences short for better flow
- Use proper punctuation for correct intonation

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.9+ from python.org |
| "No module named X" | Run `setup.bat` again |
| Pro mode locked 🔒 | Install NVIDIA GPU drivers |

---

## 📺 Local Lab YouTube Channel

**Like this tool? Subscribe for more free AI apps!**

[![YouTube](https://img.shields.io/badge/YouTube-Local%20Lab-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/@LocalLab)

---

## 📝 Credits

- [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M) - Standard Mode
- [StyleTTS 2](https://github.com/yl4579/StyleTTS2) - Pro Mode

---

<p align="center">
  Made with ❤️ by <strong>Local Lab</strong><br>
  ⭐ Star this repo if you found it useful!
</p>

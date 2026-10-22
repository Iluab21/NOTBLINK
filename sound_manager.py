import os
import math
import struct
import wave
import threading
import pygame

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")


def generate_wav(filename: str, samples: list, sample_rate: int = 44100):
    """Saves 16-bit mono PCM samples to a WAV file."""
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    filepath = os.path.join(SOUNDS_DIR, filename)
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        packed = bytearray()
        for s in samples:
            val = max(-32767, min(32767, int(s * 32767)))
            packed.extend(struct.pack("<h", val))
        wf.writeframes(packed)
    return filepath


def ensure_default_sounds():
    """Generates procedural sound effects if they don't already exist."""
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    sr = 44100

    blink_path = os.path.join(SOUNDS_DIR, "blink.wav")
    if not os.path.exists(blink_path):
        dur = 0.08
        n_samples = int(sr * dur)
        samples = []
        for i in range(n_samples):
            t = i / sr
            env = math.exp(-i / (sr * 0.015))
            noise = (math.sin(2 * math.pi * 1800 * t) + math.sin(2 * math.pi * 3200 * t)) * 0.5
            samples.append(noise * env * 0.9)
        generate_wav("blink.wav", samples, sr)


    warning_path = os.path.join(SOUNDS_DIR, "warning.wav")
    if not os.path.exists(warning_path):
        dur = 0.5
        n_samples = int(sr * dur)
        samples = []
        for i in range(n_samples):
            t = i / sr
            env = math.exp(-i / (sr * 0.12))
            freq = 140.0 * math.exp(-t * 8.0) + 45.0
            wave_val = math.sin(2 * math.pi * freq * t)
            wave_val += 0.3 * math.sin(2 * math.pi * (freq * 2.0) * t)
            samples.append(wave_val * env * 0.9)
        generate_wav("warning.wav", samples, sr)


    boss_path = os.path.join(SOUNDS_DIR, "boss.wav")
    if not os.path.exists(boss_path):
        dur = 0.9
        n_samples = int(sr * dur)
        samples = []
        for i in range(n_samples):
            t = i / sr
            # Two tone pulsing alarm
            pulse = math.sin(2 * math.pi * 4.0 * t)
            freq = 440.0 if pulse > 0 else 660.0
            env = min(1.0, (dur - t) * 2.0)
            wave_val = 0.6 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * (freq * 1.5) * t)
            samples.append(wave_val * env * 0.9)
        generate_wav("boss.wav", samples, sr)

    scale_path = os.path.join(SOUNDS_DIR, "scale.wav")
    if not os.path.exists(scale_path):
        dur = 0.35
        n_samples = int(sr * dur)
        samples = []
        for i in range(n_samples):
            t = i / sr
            freq = 200.0 + 800.0 * (t / dur)
            env = 1.0 - (t / dur)
            wave_val = math.sin(2 * math.pi * freq * t)
            samples.append(wave_val * env * 0.8)
        generate_wav("scale.wav", samples, sr)

    pause_path = os.path.join(SOUNDS_DIR, "pause.wav")
    if not os.path.exists(pause_path):
        dur = 0.22
        n_samples = int(sr * dur)
        samples = []
        for i in range(n_samples):
            t = i / dur
            freq = 520.0 if t < 0.5 else 340.0
            sub_t = t if t < 0.5 else (t - 0.5)
            env = math.exp(-sub_t * 8.0)
            wave_val = math.sin(2 * math.pi * freq * (i / sr))
            samples.append(wave_val * env * 0.7)
        generate_wav("pause.wav", samples, sr)

    resume_path = os.path.join(SOUNDS_DIR, "resume.wav")
    if not os.path.exists(resume_path):
        dur = 0.22
        n_samples = int(sr * dur)
        samples = []
        for i in range(n_samples):
            t = i / dur
            freq = 340.0 if t < 0.5 else 680.0
            sub_t = t if t < 0.5 else (t - 0.5)
            env = math.exp(-sub_t * 8.0)
            wave_val = math.sin(2 * math.pi * freq * (i / sr))
            samples.append(wave_val * env * 0.7)
        generate_wav("resume.wav", samples, sr)


    screamer_path = os.path.join(SOUNDS_DIR, "screamer.wav")
    if not os.path.exists(screamer_path):
        dur = 0.85
        n_samples = int(sr * dur)
        samples = []
        for i in range(n_samples):
            t = i / sr
            env = math.exp(-t * 3.5)
            s1 = math.sin(2 * math.pi * 880 * t)
            s2 = math.sin(2 * math.pi * 1240 * t)
            s3 = math.sin(2 * math.pi * 1760 * t)
            raw = (s1 + s2 * 0.8 + s3 * 0.6) / 2.4
            crunched = max(-0.9, min(0.9, raw * 2.5))
            samples.append(crunched * env * 0.95)
        generate_wav("screamer.wav", samples, sr)


class SoundManager:
    def __init__(self, enabled: bool = True, volume: float = 0.8):
        self.enabled = enabled
        self.volume = max(0.0, min(1.0, volume))
        self.sounds = {}
        self.initialized = False

        if not self.enabled:
            return

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            ensure_default_sounds()
            self._load_sounds()
            self.initialized = True
        except Exception as e:
            print(f"[SoundManager] Warning: Audio init failed ({e}). Running in silent mode.")
            self.initialized = False

    def _load_sounds(self):
        for name in ["blink", "warning", "boss", "scale", "pause", "resume", "screamer"]:
            path = os.path.join(SOUNDS_DIR, f"{name}.wav")
            if os.path.exists(path):
                snd = pygame.mixer.Sound(path)
                snd.set_volume(self.volume)
                self.sounds[name] = snd

    def play(self, sound_name: str):
        if not self.enabled or not self.initialized:
            return

        def _play():
            try:
                snd = self.sounds.get(sound_name)
                if snd:
                    snd.play()
            except Exception as e:
                print(f"[SoundManager] Play error: {e}")

        threading.Thread(target=_play, daemon=True).start()

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        for snd in self.sounds.values():
            snd.set_volume(self.volume)

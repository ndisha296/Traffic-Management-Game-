"""
Procedural sound effects engine for GridLock AI.
Generates retro-futuristic sound effects dynamically using math and wave synthesis,
removing the need for external asset files.
"""

import math
import struct
import io
import wave
import pygame

class SoundManager:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        self.muted = False
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._generate_sounds()
        except Exception as e:
            print(f"[SoundManager] Audio initialization notice: {e}")
            self.enabled = False

    def _generate_wave(self, duration_s, freq_generator, volume=0.25):
        """Synthesize a sound wave in memory and return a pygame.mixer.Sound object."""
        framerate = 22050
        num_frames = int(duration_s * framerate)
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(framerate)
            
            samples = []
            for i in range(num_frames):
                t = i / framerate
                freq = freq_generator(t, duration_s)
                # Envelope: attack and fade-out to prevent clicks
                envelope = min(1.0, t / 0.02) * max(0.0, 1.0 - (t / duration_s))
                value = math.sin(2.0 * math.pi * freq * t)
                # Soft harmonics
                value += 0.25 * math.sin(4.0 * math.pi * freq * t)
                sample = int(32767 * volume * envelope * (value / 1.25))
                sample = max(-32768, min(32767, sample))
                samples.append(sample)
                
            wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
            
        buffer.seek(0)
        return pygame.mixer.Sound(buffer)

    def _generate_sounds(self):
        # 1. UI Click: snappy chirp
        self.sounds['click'] = self._generate_wave(
            0.05, lambda t, d: 880 + 400 * (t / d), volume=0.15
        )

        # 2. Light Cycle: gentle dual tone
        self.sounds['light_change'] = self._generate_wave(
            0.12, lambda t, d: 520 if t < d / 2 else 659, volume=0.18
        )

        # 3. Vehicle Cleared: bright positive bell
        self.sounds['car_clear'] = self._generate_wave(
            0.15, lambda t, d: 659 + 300 * (t / d), volume=0.18
        )

        # 4. Emergency Mission Cleared: triumphal chord-like sweep
        self.sounds['mission_success'] = self._generate_wave(
            0.4, lambda t, d: 440 + 660 * (t / d), volume=0.28
        )

        # 5. Warning / Gridlock alert: low pulse
        self.sounds['alert'] = self._generate_wave(
            0.25, lambda t, d: 240 + 20 * math.sin(2 * math.pi * 12 * t), volume=0.22
        )

        # 6. Siren Blip: high warble
        self.sounds['siren'] = self._generate_wave(
            0.2, lambda t, d: 880 + 180 * math.sin(2 * math.pi * 8 * t), volume=0.2
        )

        # 7. Collision Thump
        self.sounds['crash'] = self._generate_wave(
            0.18, lambda t, d: 110 * (1.0 - t / d) + 40, volume=0.35
        )

        # 8. Traffic Violation Buzzer
        self.sounds['violation'] = self._generate_wave(
            0.22, lambda t, d: 180 if int(t * 30) % 2 == 0 else 140, volume=0.28
        )

        # 9. GPS Reroute / Refresh Tech Chirp
        self.sounds['gps_refresh'] = self._generate_wave(
            0.16, lambda t, d: 750 + 500 * (t / d) if t < d / 2 else 1250, volume=0.25
        )

        # 10. Vehicle Masters Car Horn: vibrant dual-tone honk
        def horn_freq(t, d):
            return 440.0 if int(t * 120) % 2 == 0 else 554.0
        self.sounds['horn'] = self._generate_wave(0.28, horn_freq, volume=0.32)

        # 11. Gear Shift Lever Click
        self.sounds['gear_shift'] = self._generate_wave(
            0.07, lambda t, d: 280 - 180 * (t / d), volume=0.22
        )

        # 12. Turn Signal Indicator Click-Clack
        self.sounds['turn_signal'] = self._generate_wave(
            0.04, lambda t, d: 900 if t < 0.02 else 450, volume=0.14
        )

        # 13. Perfect Park Fanfare
        def fanfare_freq(t, d):
            if t < d * 0.33:
                return 523.25  # C5
            elif t < d * 0.66:
                return 659.25  # E5
            else:
                return 783.99  # G5
        self.sounds['perfect_park'] = self._generate_wave(0.45, fanfare_freq, volume=0.35)



    def play(self, sound_name):
        if not self.enabled or self.muted:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

"""
Text-to-Speech utilities using Edge TTS (Microsoft neural voices).
"""

import threading
import tempfile
import os
import asyncio

# Edge TTS (Microsoft neural voices - free, high quality)
EDGE_TTS_AVAILABLE = False
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    pass

# Pre-initialize pygame mixer for faster playback
try:
    import pygame
    pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
    print("[TTS] pygame mixer pre-initialized")
except:
    pass


# Available Edge TTS voices (subset of best English voices)
EDGE_VOICES = {
    "jenny": "en-US-JennyNeural",      # Female, natural
    "guy": "en-US-GuyNeural",          # Male, natural
    "aria": "en-US-AriaNeural",        # Female, expressive
    "davis": "en-US-DavisNeural",      # Male, calm
    "jane": "en-US-JaneNeural",        # Female, friendly
    "jason": "en-US-JasonNeural",      # Male, casual
    "sara": "en-US-SaraNeural",        # Female, cheerful
    "tony": "en-US-TonyNeural",        # Male, professional
    "nancy": "en-US-NancyNeural",      # Female, warm
    "default": "en-US-JennyNeural",
}


class TTSPlayer:
    """Text-to-Speech player using Edge TTS."""

    def __init__(self):
        self.is_playing = False
        self.stop_requested = False
        self._play_thread = None

    def play(self, text, voice="default", speed=1.0, callback=None):
        """
        Generate and play TTS audio.

        Args:
            text: Text to speak
            voice: Voice name (see EDGE_VOICES)
            speed: Speech speed multiplier (0.5 to 2.0, default 1.0)
            callback: Optional callback(error) when done
        """
        if self.is_playing:
            self.stop()

        self.stop_requested = False
        self.is_playing = True

        self._play_thread = threading.Thread(
            target=self._play_worker,
            args=(text, voice, speed, callback),
            daemon=True
        )
        self._play_thread.start()

    def _play_worker(self, text, voice, speed, callback):
        """Worker thread for TTS generation and playback."""
        error = None

        try:
            self._play_edge(text, voice, speed)
        except Exception as e:
            error = str(e)
        finally:
            self.is_playing = False
            if callback:
                callback(error)

    def _play_edge(self, text, voice, speed=1.0):
        """Generate and play speech using Edge TTS (Microsoft neural voices) with streaming."""
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError("edge-tts not installed. Install with: pip install edge-tts")

        if self.stop_requested:
            return

        # Get voice name
        voice_name = EDGE_VOICES.get(voice.lower(), EDGE_VOICES["default"])

        # Convert speed multiplier to rate string (e.g., 1.25 -> "+25%", 0.75 -> "-25%")
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

        # Try streaming playback first (much faster)
        try:
            self._play_edge_streaming(text, voice_name, rate_str)
            return
        except Exception as e:
            print(f"[TTS] Streaming failed ({e}), falling back to file-based...")

        # Fallback: Generate full file then play
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name

        async def generate():
            communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
            await communicate.save(temp_path)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate())
            loop.close()
        except Exception as e:
            raise RuntimeError(f"Edge TTS generation failed: {e}")

        if self.stop_requested:
            os.unlink(temp_path)
            return

        self._play_audio_file(temp_path)

    def _play_edge_streaming(self, text, voice_name, rate_str="+0%"):
        """Stream Edge TTS audio for faster playback."""
        import io

        # Collect audio chunks
        audio_chunks = []

        async def stream_audio():
            communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
                if self.stop_requested:
                    break

        # Run the async streaming
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stream_audio())
        loop.close()

        if self.stop_requested or not audio_chunks:
            return

        # Combine chunks and play
        audio_data = b"".join(audio_chunks)

        # Play using pygame
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)

            # Load from bytes
            audio_stream = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_stream, "mp3")
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self.stop_requested:
                    pygame.mixer.music.stop()
                    break
                pygame.time.wait(50)
        except Exception as e:
            # If pygame fails, fall back to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            self._play_audio_file(temp_path)

    def _play_audio_file(self, file_path):
        """Play an audio file and clean up."""
        try:
            # Try pygame for mp3 support
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if self.stop_requested:
                        pygame.mixer.music.stop()
                        break
                    pygame.time.wait(100)
                return
            except ImportError:
                print("[TTS] pygame not installed, trying fallback...")
            except Exception as e:
                print(f"[TTS] pygame playback failed: {e}, trying fallback...")

            # Fallback to system player on Windows
            if os.name == 'nt':
                import subprocess
                # Use Windows Media Player via PowerShell
                try:
                    subprocess.run(
                        ['powershell', '-c',
                         f'Add-Type -AssemblyName presentationCore; '
                         f'$player = New-Object System.Windows.Media.MediaPlayer; '
                         f'$player.Open("{file_path}"); '
                         f'Start-Sleep -Milliseconds 500; '
                         f'$player.Play(); '
                         f'while ($player.Position -lt $player.NaturalDuration.TimeSpan) {{ Start-Sleep -Milliseconds 100 }}; '
                         f'$player.Close()'],
                        capture_output=True,
                        timeout=120
                    )
                except Exception as e:
                    print(f"[TTS] PowerShell playback failed: {e}")
            else:
                os.system(f'afplay "{file_path}" 2>/dev/null || mpg123 -q "{file_path}" 2>/dev/null || mpv --no-video "{file_path}" 2>/dev/null')
        finally:
            # Cleanup temp file after a delay
            try:
                import time
                time.sleep(0.5)
                os.unlink(file_path)
            except:
                pass

    def stop(self):
        """Stop current playback."""
        self.stop_requested = True
        self.is_playing = False

    def is_speaking(self):
        """Check if currently playing audio."""
        return self.is_playing


# Global player instance
_player = None

def get_player():
    global _player
    if _player is None:
        _player = TTSPlayer()
    return _player

def speak(text, voice="default", speed=1.0, callback=None, **kwargs):
    """
    Speak text using Edge TTS.

    Args:
        text: Text to speak
        voice: Voice name (jenny, guy, aria, davis, jane, jason, sara, tony, nancy)
        speed: Speech speed multiplier (0.5 to 2.0, default 1.0)
        callback: Optional callback(error) when done
    """
    get_player().play(text, voice, speed, callback)

def stop():
    """Stop current speech playback."""
    get_player().stop()

def is_speaking():
    """Check if currently speaking."""
    return get_player().is_speaking()

def get_available_voices():
    """Get list of available voices."""
    return list(EDGE_VOICES.keys())

def check_available():
    """Check if TTS is available."""
    return EDGE_TTS_AVAILABLE

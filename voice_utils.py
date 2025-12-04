import whisper
import sounddevice as sd
import numpy as np
import tempfile
import scipy.io.wavfile as wav
import threading

# Load model once (use 'tiny' for speed, 'base' for accuracy)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


class VoiceRecorder:
    """Push-to-talk voice recorder with transcription."""
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_data = []
        self.stream = None
        self.callback = None
        
    def start_recording(self, callback=None):
        """Start recording audio."""
        if self.is_recording:
            return
            
        self.callback = callback
        self.audio_data = []
        self.is_recording = True
        
        def audio_callback(indata, frames, time, status):
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=audio_callback
        )
        self.stream.start()
    
    def stop_recording(self):
        """Stop recording and transcribe."""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Transcribe in background
        if self.audio_data:
            audio = np.concatenate(self.audio_data).flatten()
            threading.Thread(
                target=self._transcribe,
                args=(audio, self.callback),
                daemon=True
            ).start()
    
    def _transcribe(self, audio_data, callback):
        """Transcribe audio data."""
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wav.write(f.name, self.sample_rate, audio_int16)
                
                model = get_model()
                result = model.transcribe(f.name)
                text = result["text"].strip()
                
                if callback:
                    callback(text, None)
        except Exception as e:
            if callback:
                callback(None, str(e))


# Global recorder instance
_recorder = None

def get_recorder():
    global _recorder
    if _recorder is None:
        _recorder = VoiceRecorder()
    return _recorder

def start_recording(callback=None):
    """Start push-to-talk recording."""
    get_recorder().start_recording(callback)

def stop_recording():
    """Stop recording and transcribe."""
    get_recorder().stop_recording()

def is_recording():
    """Check if currently recording."""
    return get_recorder().is_recording

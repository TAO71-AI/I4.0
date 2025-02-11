# Import libraries
from threading import Event
import pyaudio
import numpy as np
import time
import wave
import io

def RAWToWAV(RawBytes: bytes, Channels: int = 1, SampleRate: int = 44100) -> bytes:
    """
    Converts raw audio bytes to WAV format.

    ## Parameters:
    - RawBytes (bytes): Raw audio bytes.

    ## Returns:
    bytes: WAV audio bytes.
    """

    # Create buffer
    buffer = io.BytesIO()

    # Write the WAV header
    with wave.open(buffer, "wb") as wavefile:
        wavefile.setnchannels(Channels)
        wavefile.setsampwidth(2)
        wavefile.setframerate(SampleRate)
        wavefile.writeframesraw(RawBytes)

    # Read the buffer bytes
    buffer.seek(0)
    bufBytes = buffer.read()

    # Close the buffer and return the bytes
    buffer.close()
    return bufBytes

def RecordMicrophoneUntilSilence(SilenceDuration: float = 1.5, VoiceThreshold: int = 150, Channels: int = 1, SampleRate: int = 44100) -> tuple[bool, bytes]:
    """
    Records the audio on your default microphone.

    ## Parameters:
    - SilenceDuration (float): Duration of silence in seconds to stop recording.
    - VoiceThreshold (int): Threshold for detecting silence.
    - Channels (int): Number of audio channels.
    - SampleRate (int): Sample rate of the audio.

    ## Returns:
    tuple: (containsVoice (bool), data (bytes))

    The bytes returned are RAW audio bytes.
    """

    # Create variables
    chunkSize = 1024
    format = pyaudio.paInt16
    frames = []
    silenceStart = None
    containsVoice = False
    stopEvent = Event()

    # Start PyAudeio
    p = pyaudio.PyAudio()

    # Start recording
    stream = p.open(
        format = format,
        channels = Channels,
        rate = SampleRate,
        input = True,
        frames_per_buffer = chunkSize
    )

    # While the event is not completed
    while (not stopEvent.is_set()):
        # Read the chunk data
        data = stream.read(chunkSize)

        # Save into the frames
        frames.append(data)

        # Convert the data to a numpy array for processing
        data = np.frombuffer(data, dtype = np.int16)
        silenceCount = np.sum(np.abs(data) < VoiceThreshold)

        # Check if the audio contains a voice
        if (silenceCount / len(data) >= 0.5):
            # It doesn't
            if (silenceStart is None):
                # Start the silence timer
                silenceStart = time.time()
            elif (time.time() - silenceStart > SilenceDuration):
                # Stop the recording
                stopEvent.set()
        else:
            # It does
            # Reset the timer and set the containsVoice bool to True
            silenceStart = None
            containsVoice = True
        
    # Stop the stream
    stream.stop_stream()
    stream.close()
    
    # Terminate PyAudio
    p.terminate()

    # Return the containsVoice boolean and the bytes of the audio
    return (containsVoice, b"".join(frames))
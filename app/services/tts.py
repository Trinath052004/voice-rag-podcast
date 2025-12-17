import os
import base64
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

# Map agent roles to ElevenLabs voice IDs
# Replace with your preferred voices from https://elevenlabs.io/voice-library
VOICES = {
    "curious": "TxGEqnHWrfWFTfGW9XjX",    # Josh - energetic, curious
    "explainer": "21m00Tcm4TlvDq8ikWAM",  # Rachel - clear, professional
    "moderator": "pNInz6obpgDQGcFmaJgB",  # Adam - warm, authoritative
}

def text_to_speech(text: str, voice: str = "explainer") -> str:
    """
    Convert text to speech using ElevenLabs.
    Returns base64-encoded MP3 audio.
    """
    voice_id = VOICES.get(voice, VOICES["explainer"])
    
    audio_generator = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",  # Best quality
        output_format="mp3_44100_128",
    )
    
    # Collect audio bytes from generator
    audio_bytes = b"".join(audio_generator)
    
    return base64.b64encode(audio_bytes).decode()

def text_to_speech_stream(text: str, voice: str = "explainer"):
    """
    Stream audio for real-time playback.
    Yields audio chunks.
    """
    voice_id = VOICES.get(voice, VOICES["explainer"])
    
    return client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_turbo_v2_5",  # Faster for streaming
        output_format="mp3_44100_128",
    )

def generate_podcast_audio(conversation: dict) -> dict:
    """Generate audio for full podcast turn."""
    return {
        "curious_audio": text_to_speech(conversation["curious"], "curious"),
        "explainer_audio": text_to_speech(conversation["explainer"], "explainer"),
        "moderator_audio": text_to_speech(conversation["moderator"], "moderator"),
    }

def generate_combined_podcast(conversation: dict) -> str:
    """
    Generate a single combined audio file for the full podcast turn.
    Returns base64-encoded MP3.
    """
    # Generate individual segments
    curious_audio = b"".join(client.text_to_speech.convert(
        voice_id=VOICES["curious"],
        text=conversation["curious"],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    ))
    
    explainer_audio = b"".join(client.text_to_speech.convert(
        voice_id=VOICES["explainer"],
        text=conversation["explainer"],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    ))
    
    moderator_audio = b"".join(client.text_to_speech.convert(
        voice_id=VOICES["moderator"],
        text=conversation["moderator"],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    ))
    
    # Combine (simple concatenation - works for MP3)
    combined = curious_audio + explainer_audio + moderator_audio
    
    return base64.b64encode(combined).decode()

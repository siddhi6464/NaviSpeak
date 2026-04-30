import speech_recognition as sr
import io

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes (e.g. from streamlit-mic-recorder) to text using Google STT.
    """
    recognizer = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return f"Could not request results; {e}"
    except Exception as e:
        return f"Error processing audio: {e}"

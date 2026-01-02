import os
import speech_recognition as sr
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import pygame
import tempfile
import time

# Prefer the new Google GenAI client; fall back to the deprecated one
try:
    from google import genai as genai_new  # google-genai
    _USE_NEW_GENAI = True
except Exception:
    import google.generativeai as genai_old  # deprecated, but keep as fallback
    _USE_NEW_GENAI = False

class VoiceAssistant:
    def __init__(self, elevenlabs_api_key, gemini_api_key):
        """Initialize voice assistant with ElevenLabs and Gemini."""
        # ElevenLabs for high-quality voice
        self.elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)
        self.voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam voice

        # Gemini for AI brain (use supported models and client)
        self.model_name = "gemini-1.5-flash"  # fast, capable text model
        self.chat = None
        try:
            if _USE_NEW_GENAI:
                # New client style
                self.genai_client = genai_new.Client(api_key=gemini_api_key)
                # Create a chat session for multi-turn conversations
                self.chat = self.genai_client.chats.create(model=self.model_name, history=[])
            else:
                # Deprecated client fallback
                genai_old.configure(api_key=gemini_api_key)
                self.model = genai_old.GenerativeModel(self.model_name)
                self.chat = self.model.start_chat(history=[])
        except Exception as e:
            print(f"AI Init Error: {e}")

        # Speech recognition
        self.recognizer = sr.Recognizer()

        # Initialize pygame for audio playback
        pygame.mixer.init()

        print("✅ Using ElevenLabs for voice")
        print("✅ Using Gemini AI with model:", self.model_name)
        
    def listen(self):
        """Listen to microphone and convert to text."""
        with sr.Microphone() as source:
            print("\n🎤 Listening... (speak now)")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                print("⏳ Processing speech...")
                text = self.recognizer.recognize_google(audio)
                print(f"You: {text}")
                return text
            except sr.WaitTimeoutError:
                print("⚠️  No speech detected")
                return None
            except sr.UnknownValueError:
                print("⚠️  Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"⚠️  Error: {e}")
                return None
    
    def get_ai_response(self, user_input):
        """Get response from Gemini AI using supported SDK/model."""
        try:
            if _USE_NEW_GENAI:
                # Ensure chat exists
                if self.chat is None:
                    self.chat = self.genai_client.chats.create(model=self.model_name, history=[])
                response = self.chat.send_message(user_input)
            else:
                response = self.chat.send_message(user_input)

            # Try best-effort to extract text across SDK variants
            text = getattr(response, "text", None)
            if not text:
                # Some responses may have candidates/parts
                try:
                    text = "".join(part.text for part in response.candidates[0].content.parts)
                except Exception:
                    text = None
            return text or "I'm having trouble processing that right now."
        except Exception as e:
            print("AI Error:", e)
            # Common cause: 404 for old model names like 'gemini-pro'
            print("Hint: ensure your model is available and API key is valid.")
            return "I'm having trouble processing that right now."
    
    def speak(self, text):
        """Convert text to speech using ElevenLabs."""
        print(f"\n🤖 Assistant: {text}\n")
        
        try:
            # Generate speech with ElevenLabs
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                for chunk in audio_generator:
                    temp_file.write(chunk)
                temp_filename = temp_file.name

            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            # Clean up
            os.unlink(temp_filename)

        except Exception as e:
            print("Speech Error:", e)
            print("Hint: verify your ElevenLabs API key and voice ID.")
    
    def run(self):
        """Main loop for the voice assistant."""
        print("\n" + "="*60)
        print("🎙️  VOICE ASSISTANT STARTED!")
        print("="*60)
        print("Say 'exit', 'quit', or 'goodbye' to stop")
        print("="*60 + "\n")
        
        self.speak("Hello! I'm your voice assistant powered by ElevenLabs and Gemini AI. How can I help you today?")
        
        while True:
            user_input = self.listen()
            
            if user_input is None:
                continue
            
            # Check for exit commands
            if any(word in user_input.lower() for word in ['exit', 'quit', 'stop', 'goodbye', 'bye']):
                self.speak("Goodbye! Have a wonderful day!")
                break
            
            # Get AI response
            response = self.get_ai_response(user_input)
            
            # Speak the response
            self.speak(response)
            
            print("="*60)

def main():
    """Main function."""
    print("\n" + "="*60)
    print("VOICE ASSISTANT - ELEVENLABS + FREE GEMINI AI")
    print("="*60)
    
    # Get ElevenLabs API key
    elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
    if not elevenlabs_key:
        print("\n📝 Enter your ElevenLabs API key:")
        elevenlabs_key = input("ElevenLabs Key: ").strip()
    
    # Get FREE Gemini API key
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("\n📝 Get your FREE Gemini API key:")
        print("   1. Go to: https://makersuite.google.com/app/apikey")
        print("   2. Sign in with Google")
        print("   3. Click 'Create API Key'")
        print("   4. Copy and paste it below\n")
        gemini_key = input("Gemini Key (FREE): ").strip()
    
    if not elevenlabs_key or not gemini_key:
        print("\n❌ Both API keys are required!")
        return
    
    # Create and run assistant
    assistant = VoiceAssistant(elevenlabs_key, gemini_key)
    assistant.run()

if __name__ == "__main__":
    main()


# QUICK SETUP GUIDE:
# 
# 1. Install packages:
#    pip install elevenlabs
#    pip install google-generativeai
#    pip install SpeechRecognition
#    pip install pygame
#    pip install pyaudio
#
# 2. Get FREE Gemini API key:
#    https://makersuite.google.com/app/apikey
#
# 3. Run:
#    python voice_assistant.py
#
# 4. Enter your ElevenLabs key (you have this)
# 5. Enter your Gemini key (FREE - no credit card!)
#
# COST: Only ElevenLabs charges (Gemini is FREE)
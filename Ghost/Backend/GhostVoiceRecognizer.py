import speech_recognition as sr
import os
import logging
from dotenv import load_dotenv
import asyncio  # For async operations
import time  # For time.sleep

# Configure logging for GhostVoiceRecognizer
logging.basicConfig(
    level=logging.WARNING,  # Keep at WARNING for general operation, DEBUG for deep troubleshooting
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class GhostVoiceRecognizer:
    """
    Handles voice input, hotword detection, and speech-to-text conversion.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.hotword = os.getenv("HOTWORD", "ghost").lower()  # Default hotword "ghost"
        self.is_active = False  # Flag to indicate if the assistant is actively listening for commands
        self.energy_threshold = int(os.getenv("ENERGY_THRESHOLD", 300))  # Adjust based on ambient noise
        self.pause_threshold = float(
            os.getenv("PAUSE_THRESHOLD", 0.8))  # Seconds of non-speaking before phrase is considered complete
        self.phrase_time_limit = float(os.getenv("PHRASE_TIME_LIMIT", 5.0))  # Max seconds to listen for a single phrase

        logger.info(f"Voice Recognizer initialized with hotword: '{self.hotword}'")
        logger.info(
            f"Energy Threshold: {self.energy_threshold}, Pause Threshold: {self.pause_threshold}, Phrase Time Limit: {self.phrase_time_limit}")

        # Adjust recognizer settings
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.pause_threshold = self.pause_threshold

        # Try to open microphone once to catch initial errors
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)  # Listen for 1 second to calibrate noise
            logger.info("Adjusted for ambient noise.")
        except Exception as e:
            logger.error(f"Error adjusting for ambient noise. Check microphone setup: {e}", exc_info=True)

    async def listen(self) -> tuple[str, bool]:
        """
        Listens for audio input and attempts to convert it to text.
        Returns (transcribed_text, is_hotword_detected_if_not_active).
        """
        transcribed_text = None
        is_hotword_detected = False

        try:
            with self.microphone as source:
                logger.debug("Microphone source opened.")
                # If not active, listen for hotword (shorter phrase time limit)
                # If active, listen for a full command (longer phrase time limit)
                phrase_limit = 2.0 if not self.is_active else self.phrase_time_limit

                logger.info(f"Listening for audio (is_active={self.is_active}, phrase_limit={phrase_limit})...")
                audio = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.recognizer.listen(source, phrase_time_limit=phrase_limit)
                )
                logger.debug("Audio captured.")

            if audio:
                logger.debug("Attempting to recognize speech...")
                # Google Speech Recognition is blocking, run in executor
                transcribed_text = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.recognizer.recognize_google(audio)
                )
                logger.info(f"Transcribed: '{transcribed_text}'")

                if not self.is_active and self.hotword in transcribed_text.lower():
                    is_hotword_detected = True
                    logger.info(f"Hotword '{self.hotword}' detected!")
            else:
                logger.debug("No audio captured.")

        except sr.UnknownValueError:
            logger.warning("Speech Recognition could not understand audio. Waiting a moment...")
            transcribed_text = None  # Explicitly set to None if not understood
            await asyncio.sleep(0.5)  # Add a small delay after an unknown value error
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service; {e}", exc_info=True)
            transcribed_text = None
            await asyncio.sleep(1.0)  # Add a slightly longer delay for network errors
        except Exception as e:
            logger.critical(f"An unexpected error occurred during audio listening/recognition: {e}", exc_info=True)
            transcribed_text = None
            await asyncio.sleep(1.0)  # Add a delay for critical errors

        return transcribed_text, is_hotword_detected

    def set_hotword(self, new_hotword: str):
        """Sets a new hotword for activation."""
        self.hotword = new_hotword.lower()
        logger.info(f"Hotword updated to: '{self.hotword}'")


# Example usage for testing GhostVoiceRecognizer directly
if __name__ == "__main__":
    voice_recognizer = GhostVoiceRecognizer()
    print(f"Say '{voice_recognizer.hotword}' to test hotword detection, or speak a command.")


    async def main_voice_test():
        while True:
            text, hotword_detected = await voice_recognizer.listen()
            if hotword_detected:
                print(f"Hotword detected! Activating...")
                voice_recognizer.is_active = True
            elif voice_recognizer.is_active and text:
                print(f"Command: {text}")
                if "deactivate" in text.lower():
                    print("Deactivating...")
                    voice_recognizer.is_active = False
            elif text:
                print(f"Heard (but not active): {text}")
            else:
                print("No speech detected or understood.")
            await asyncio.sleep(0.1)  # Small delay


    try:
        asyncio.run(main_voice_test())
    except KeyboardInterrupt:
        print("\nVoice test interrupted.")


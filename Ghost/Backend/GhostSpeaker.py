import asyncio
import edge_tts
import soundfile as sf
import sounddevice as sd
import os
from tempfile import NamedTemporaryFile
import logging # Import logging for better error handling

# Configure logging for GhostSpeaker
logging.basicConfig(
    level=logging.INFO, # Set to INFO to see speech generation messages
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GhostSpeaker:
    """
    Handles text-to-speech conversion and audio playback using edge_tts.
    """
    def __init__(self):
        # Initialize audio settings
        self.sample_rate = 44100
        self.channels = 2
        sd.default.samplerate = self.sample_rate
        sd.default.channels = self.channels
        logger.info(f"GhostSpeaker initialized. Sample rate: {self.sample_rate}, Channels: {self.channels}")

    async def _generate_audio(self, text: str) -> bytes:
        """
        Generate audio bytes using edge_tts with a specified deep male voice.
        """
        # Using 'en-US-GuyNeural' for a natural deep male voice.
        # Other options you might explore for different male voices include:
        # 'en-US-JasonNeural', 'en-US-DavisNeural', 'en-US-AriaNeural' (female, but for comparison)
        # You can find a full list of voices by running 'edge-tts --list-voices' in your terminal
        # if you have edge-tts installed globally.
        VOICE = "en-US-GuyNeural"
        logger.debug(f"Generating audio for text: '{text[:50]}...' using voice: {VOICE}")
        communicate = edge_tts.Communicate(text=text, voice=VOICE)
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        logger.debug("Audio data generated.")
        return bytes(audio_data)

    async def speak_async(self, text: str):
        """
        Async method to speak text without visible media player.
        Generates audio, saves to a temporary file, plays it, and then cleans up.
        """
        temp_path = None # Initialize temp_path to None
        try:
            # Create persistent temporary file (won't auto-delete automatically by OS)
            with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
                logger.info(f"Temporary audio file created at: {temp_path}")

                # Generate and save audio
                audio_data = await self._generate_audio(text)
                temp_file.write(audio_data)
                temp_file.flush() # Ensure all data is written to disk
                logger.debug("Audio data written to temporary file.")

            # Play audio (file will exist until explicitly deleted)
            logger.info(f"Playing audio from: {temp_path}")
            data, samplerate = sf.read(temp_path)
            sd.play(data, samplerate)
            sd.wait()  # Block until playback completes
            logger.info("Audio playback complete.")

        except FileNotFoundError:
            logger.error(f"Temporary file not found: {temp_path}. This might indicate a deletion issue or path error.")
        except Exception as e:
            logger.error(f"An error occurred during audio playback: {e}", exc_info=True)
        finally:
            # Clean up the file after playback completes, if it was created
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.info(f"Temporary audio file deleted: {temp_path}")
                except PermissionError:
                    logger.warning(f"Permission denied when trying to delete {temp_path}. File might be locked.")
                except Exception as e:
                    logger.warning(f"Error deleting temporary file {temp_path}: {e}")

    def speak(self, text: str):
        """
        Synchronous wrapper for speak_async.
        Handles running the async method in an appropriate asyncio loop.
        """
        try:
            # Attempt to run in the current event loop if one is already running
            asyncio.get_running_loop().run_until_complete(self.speak_async(text))
        except RuntimeError:
            # If no event loop is running, create a new one
            logger.debug("No running asyncio loop found. Creating a new one.")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.speak_async(text))
            loop.close()
            logger.debug("New asyncio loop closed.")


# Example usage
if __name__ == "__main__":
    speaker = GhostSpeaker()
    print("Speaking: 'This audio will now play directly in a natural deep male voice.'")
    speaker.speak("This audio will now play directly in a natural deep male voice.")
    print("Speaking: 'I hope this voice meets your expectations.'")
    speaker.speak("I hope this voice meets your expectations.")
    print("Done with examples.")


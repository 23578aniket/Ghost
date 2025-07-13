import asyncio
import speech_recognition as sr
import os
from datetime import datetime
import random
import logging
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any

# --- IMPORTANT: Import QObject and pyqtSignal for PyQt integration ---
from PyQt5.QtCore import QObject, pyqtSignal
# --- End of PyQt imports ---

# Configure logging: Set level to INFO for better debugging visibility during development
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import components from Backend folder
from Backend.GhostVoiceRecognizer import GhostVoiceRecognizer
from Backend.IntentRecognizer import IntentRecognizer
from Backend.LearningAssistant import LearningAssistant
from Backend.GhostSpeaker import GhostSpeaker
# from Backend.RealtimeSearchEngine import RealTimeSearchEngine # Not used in provided _process_command, keeping commented for now


# --- IMPORTANT: GhostCore must inherit from QObject to use PyQt signals ---
class GhostCore(QObject):
    # Define signals that the UI will connect to
    status_update_signal = pyqtSignal(str, str) # text, state_name (e.g., 'listening', 'speaking')
    chat_message_signal = pyqtSignal(str, str, bool) # sender, message, is_user

    def __init__(self):
        super().__init__() # --- IMPORTANT: Call QObject's __init__ first! ---
        logger.debug("GhostCore: __init__ started. QObject super().__init__() called.")

        self.assistant_name = os.getenv("AssistantName", "Ghost")
        self.inactivity_timeout_seconds = 60
        self._is_running = False
        self._last_interaction = datetime.now()
        self._conversation_context = {} # Future use for context management

        self.voice = GhostVoiceRecognizer()
        self.intent_recognizer = IntentRecognizer() # Renamed to avoid confusion with 'intent' variable
        self.learning_assistant = LearningAssistant() # This now maps intents to actions
        self.speaker = GhostSpeaker()
        # self.searcher = RealTimeSearchEngine() # Only uncomment if _process_realtime_query is actively used and integrated
        logger.debug("GhostCore: All components initialized.")


    # This method seems to be for a separate real-time search feature,
    # which isn't currently integrated into the main _process_command flow.
    # Keep it if you plan to integrate it, otherwise, it can be removed or refined.
    # async def _process_realtime_query(self, query: str) -> str:
    #     try:
    #         results = await self.searcher.query(query)
    #         return results
    #     except Exception as e:
    #         logger.critical(f"Search failed: {e}", exc_info=True)
    #         return "Sorry, I couldn't complete that search due to an internal error."

    async def _process_command(self, text: Optional[str], is_activation: bool = False) -> Optional[str]:
        try:
            self._last_interaction = datetime.now()
            response_to_speak = None

            # --- Case 1: Handle activation command directly ---
            if is_activation:
                response_to_speak = "How may I help you?"
                logger.info(f"{self.assistant_name}: {response_to_speak}")
                # Emit status and chat message signals
                self.status_update_signal.emit(response_to_speak, "speaking")
                self.chat_message_signal.emit(self.assistant_name, response_to_speak, False)
                await self.speaker.speak_async(response_to_speak)
                return response_to_speak

            # --- Case 2: Handle deactivation command directly (from voice recognizer) ---
            if text and text.lower() == "deactivate":
                response_to_speak = "Okay, I'm going to sleep."
                logger.info(f"{self.assistant_name}: {response_to_speak}")
                # Emit status and chat message signals
                self.status_update_signal.emit(response_to_speak, "idle")
                self.chat_message_signal.emit(self.assistant_name, response_to_speak, False)
                await self.speaker.speak_async(response_to_speak)
                self._is_running = False
                self.voice.is_active = False # Ensure voice recognizer also deactivates
                return response_to_speak

            # --- Case 3: Process a regular command (requires text) ---
            if text:
                # Emit user message to UI
                self.chat_message_signal.emit("You", text, True)

                # 1. Use IntentRecognizer to get intent, entity, and confidence
                # (predicted_intent, entity, intent_type, confidence)
                # You only need predicted_intent and entity for action dispatching here.
                predicted_intent, entity, _, confidence = self.intent_recognizer.predict_intent(text)

                logger.info(f"You said: '{text}'")
                logger.info(f"Intent recognized: '{predicted_intent}' (Confidence: {confidence:.2f}, Entity: {entity if entity else 'None'})")

                # Emit status to UI (e.g., "Processing...")
                self.status_update_signal.emit("Analyzing Data...", "processing")


                # Handle specific system_info entities identified by IntentRecognizer
                if predicted_intent == "system_info":
                    if entity == "your name":
                        response_to_speak = f"My name is {self.assistant_name}."
                    elif entity == "creator":
                        response_to_speak = "I was created by a human developer. My identity is open-source." # Customize as needed
                    elif entity == "capabilities":
                        response_to_speak = "I can help you with system commands, web searches, media control, and more." # General answer
                    else: # Default for other system info queries
                         response_to_speak = "I am a virtual assistant designed to help you with various tasks."
                elif predicted_intent == "greeting":
                    response_to_speak = random.choice(["Hello! How can I assist you?", "Hi there!", "Greetings!"])
                elif predicted_intent == "exit":
                    response_to_speak = random.choice(["Goodbye!", "See you later!", "Shutting down."])
                    self._is_running = False
                    self.voice.is_active = False
                elif predicted_intent == "get_weather":
                    # IntentRecognizer already extracted the entity (location)
                    # Now, map this intent to an action and execute it.
                    # This could be SystemActions.search_on_google or a dedicated weather API call.
                    # For now, let's make it a Google search for simplicity using the entity.
                    if entity:
                        action_func, action_args = self.learning_assistant.get_action_for_intent("search_on_google", entity=f"{entity} weather")
                    else:
                        action_func, action_args = self.learning_assistant.get_action_for_intent("search_on_google", entity="current weather")

                    if action_func:
                        response_from_action = await action_func(**action_args) # Await the function if it's async
                        response_to_speak = response_from_action
                    else:
                        response_to_speak = "I can't get the weather right now."

                elif predicted_intent == "get_info":
                    # IntentRecognizer extracted the entity (query for wikipedia/google)
                    # Try Wikipedia first, fallback to Google
                    if entity:
                        wiki_action_func, wiki_action_args = self.learning_assistant.get_action_for_intent("wikipedia_search", entity=entity)
                        if wiki_action_func:
                            try:
                                response_from_action = await wiki_action_func(**wiki_action_args)
                                if "No information found on Wikipedia" not in response_from_action:
                                    response_to_speak = response_from_action
                                else: # If Wikipedia failed, try Google
                                    google_action_func, google_action_args = self.learning_assistant.get_action_for_intent("search_on_google", entity=entity)
                                    response_to_speak = await google_action_func(**google_action_args)
                            except Exception as e:
                                logger.warning(f"Wikipedia search failed, trying Google: {e}")
                                google_action_func, google_action_args = self.learning_assistant.get_action_for_intent("search_on_google", entity=entity)
                                response_to_speak = await google_action_func(**google_action_args)
                        else:
                            response_to_speak = "I can't find information on that."
                    else:
                        response_to_speak = "What information are you looking for?"

                elif predicted_intent == "unknown" or confidence < self.intent_recognizer.confidence_threshold:
                    # Low confidence or truly unknown intent
                    response_to_speak = random.choice([
                        "I'm not sure how to help with that. Can you rephrase?",
                        "I didn't quite catch that. Could you say it again?",
                        "Sorry, I didn't understand. Could you try a different command?"
                    ])
                    # Optionally, log to DB for later review
                    # self.intent_recognizer.log_unrecognized_query(text, predicted_intent, confidence)
                else:
                    # 2. Map the predicted intent to an action function using LearningAssistant
                    action_func, action_args = self.learning_assistant.get_action_for_intent(predicted_intent, entity) # Pass entity if needed

                    if action_func:
                        try:
                            # Execute the action function with its arguments
                            # Ensure the function is awaited if it's an async function
                            response_from_action = action_func(**action_args)
                            if hasattr(response_from_action, '__await__'): # Check if it's an awaitable (coroutine)
                                response_from_action = await response_from_action
                            response_to_speak = response_from_action
                        except Exception as e:
                            logger.error(f"Error executing action for intent '{predicted_intent}' with args {action_args}: {e}", exc_info=True)
                            response_to_speak = f"Sorry, I encountered an error while trying to perform that action."
                    else:
                        response_to_speak = f"I understood you wanted to '{predicted_intent.replace('_', ' ')}', but I don't have an action for that yet."
            else:
                return None  # No command to process (e.g., no speech detected)

            # --- Speak and Print the Assistant's Response (centralized) ---
            if response_to_speak:
                logger.info(f"{self.assistant_name}: {response_to_speak}")
                # Emit status and chat message signals
                self.status_update_signal.emit(response_to_speak, "speaking")
                self.chat_message_signal.emit(self.assistant_name, response_to_speak, False)
                await self.speaker.speak_async(response_to_speak)
                # After speaking, revert status to idle
                self.status_update_signal.emit("Awaiting Orders.", "idle")


            return response_to_speak

        except Exception as e:
            logger.critical(f"Unhandled error in _process_command: {e}", exc_info=True)
            error_response = "Sorry, I encountered an internal error while processing your command."
            logger.info(f"{self.assistant_name}: {error_response}")
            # Emit error status and chat message
            self.status_update_signal.emit(error_response, "error")
            self.chat_message_signal.emit(self.assistant_name, error_response, False)
            await self.speaker.speak_async(error_response)
            return "Error occurred."

    async def run_async_loop(self): # Renamed from `run` to avoid conflict with QThread's `run`
        """
        The main asynchronous loop for GhostCore.
        """
        self._is_running = True
        logger.info(f"{self.assistant_name}: Ready. Say '{self.voice.hotword}' to activate.")
        # Emit initial status for UI
        self.status_update_signal.emit("Awaiting Orders.", "idle")


        try:
            while self._is_running:
                current_time = datetime.now()
                if (current_time - self._last_interaction).total_seconds() > self.inactivity_timeout_seconds:
                    logger.info(f"{self.assistant_name}: Going to sleep now due to inactivity.")
                    await self.speaker.speak_async("Going to sleep now.")
                    self._is_running = False
                    self.voice.is_active = False # Ensure voice recognizer also deactivates
                    # Emit final status
                    self.status_update_signal.emit("Offline.", "idle")
                    break

                # Emit status when listening
                self.status_update_signal.emit("Receiving Transmission...", "listening")
                text_from_voice, is_hotword_detected_by_voice_recognizer = await self.voice.listen()

                # IMPORTANT: Decide *how* to call _process_command based on activation state

                # Scenario 1: Hotword detected and assistant is NOT active yet
                if self.voice.hotword.lower() in (text_from_voice or "").lower() and not self.voice.is_active:
                    self.voice.is_active = True  # Activate the assistant
                    self.status_update_signal.emit("Activated. Processing...", "processing") # Update status for activation
                    await self._process_command(text=None, is_activation=True) # Activation
                    self._last_interaction = datetime.now() # Reset timer after activation
                # Scenario 2: Assistant IS active and a command was spoken
                elif self.voice.is_active and text_from_voice:
                    self.status_update_signal.emit("Command Received. Processing...", "processing")
                    await self._process_command(text=text_from_voice, is_activation=False)
                # Scenario 3: Assistant is active but no speech or unrecognizble speech (revert to idle)
                elif self.voice.is_active and not text_from_voice:
                    self.status_update_signal.emit("Awaiting Orders.", "idle")
                # Scenario 4: Assistant is not active AND hotword not detected (do nothing, just keep listening silently)
                # In this case, status should remain "Awaiting Orders." but the voice recognizer is listening for hotword.
                # No change needed if it's already "Awaiting Orders."

                await asyncio.sleep(0.1) # Small delay to prevent busy-waiting

        except KeyboardInterrupt:
            logger.info(f"\n{self.assistant_name}: Assistant interrupted by user (Ctrl+C).")
            # Emit final status
            self.status_update_signal.emit("Offline.", "idle")
        except Exception as e:
            logger.critical(f"An unhandled error occurred in the main run loop: {e}", exc_info=True)
            # Emit error status
            self.status_update_signal.emit("Critical Error.", "error")
        finally:
            self.stop()
            self.intent_recognizer.close() # Close DB connection on exit


    def stop(self):
        self._is_running = False
        logger.info(f"{self.assistant_name}: Assistant stopped.")


if __name__ == "__main__":
    try:
        core = GhostCore()
        asyncio.run(core.run_async_loop())
    except Exception as e:
        logger.critical(f"An unhandled error occurred at the script level: {e}", exc_info=True)
    finally:
        logger.info("Process finished.")


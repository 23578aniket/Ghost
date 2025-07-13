import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import re
import pickle
import os
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, # <--- CHANGE THIS LINE TO WARNING OR ERROR
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntentRecognizer:
    """Enhanced intent recognizer with continuous learning and better error handling"""

    def __init__(self):
        self.model = None
        self.model_path = Path(__file__).parent / "intent_model.pkl"
        self.db_path = Path(__file__).parent / "intents.db"
        self.confidence_threshold = 0.6  # Increased threshold
        self.min_samples_per_class = 3  # Minimum samples per intent class
        self.is_trained = False

        # Common intent patterns for fallback
        self.common_patterns = {
            "greeting": ["hello", "hi", "hey"],
            "get_time": ["time", "clock", "what time"],
            "get_weather": ["weather", "forecast", "temperature"],
            "system_info": ["who made", "created", "what are you", "your name"],
            # Added "your name" here for direct handling
            "exit": ["exit", "quit", "stop", "goodbye", "go to sleep", "shut down", "I am done", "you can stop now"],
            # Added new phrases
            "get_info": ["who is", "where is", "what is", "how", "find", "show me"]
        }

        self._setup_database()
        self._initialize_model()

    def _setup_database(self) -> None:
        """Initialize the SQLite database with error handling"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

            # Create tables if they don't exist
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                intent TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'user'
            )
            """)

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                predicted_intent TEXT,
                correct_intent TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database setup failed: {e}")
            raise

    def _initialize_model(self) -> None:
        """Initialize or load the model with proper checks"""
        try:
            if self._model_exists():
                self._load_model()
                self.is_trained = True
            else:
                self._create_new_model()
                self._add_initial_examples()  # Call initial examples if no model
                self._train_and_save_model()  # Train immediately after adding initial examples
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            self.is_trained = False

    def _model_exists(self) -> bool:
        """Check if model exists and is valid"""
        return self.model_path.exists() and os.path.getsize(self.model_path) > 0

    def _create_new_model(self) -> None:
        """Create a new model pipeline"""
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.85,
                analyzer='word',
                token_pattern=r'\b[a-zA-Z]{3,}\b'
            )),
            ('clf', CalibratedClassifierCV(
                LinearSVC(
                    class_weight='balanced',
                    max_iter=5000,
                    C=0.8
                ),
                cv=3
            ))
        ])
        self.is_trained = False

    def _get_training_data(self) -> Tuple[List[str], List[str]]:
        """Get training data from database with validation"""
        try:
            self.cursor.execute("SELECT text, intent FROM training_data")
            results = self.cursor.fetchall()
            if not results:
                return [], []
            return zip(*results)
        except sqlite3.Error as e:
            logger.error(f"Failed to get training data: {e}")
            return [], []

    def _train_model(self) -> bool:
        """Train the model with data from database"""
        try:
            texts, labels = self._get_training_data()
            if not texts or len(set(labels)) < 2:  # Need at least 2 classes
                logger.warning("Insufficient training data for model fitting.")
                self.is_trained = False
                return False

            # Check for minimum samples per class
            from collections import Counter
            label_counts = Counter(labels)
            for intent, count in label_counts.items():
                if count < self.min_samples_per_class:
                    logger.warning(
                        f"Intent '{intent}' has only {count} samples, "
                        f"which is less than the required {self.min_samples_per_class} for robust training."
                    )
                    self.is_trained = False
                    return False

            self.model.fit(texts, labels)
            self.is_trained = True
            return True
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            self.is_trained = False
            return False

    def _train_and_save_model(self) -> None:
        """Train and save a new model with validation"""
        logger.info("Attempting to train and save model with database data...")
        if self._train_model():
            self._save_model()
        else:
            logger.warning("Model not trained due to insufficient or invalid data. Skipping save.")

    def _save_model(self) -> None:
        """Save the trained model with error handling"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def _load_model(self) -> None:
        """Load the trained model with error handling"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"Model loaded from {self.model_path}")
            self.is_trained = True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_trained = False

    def _add_single_training_example_to_db(self, text: str, intent: str, source: str = 'initial') -> bool:
        """Adds a single training example to the database."""
        clean_text = self._preprocess_text(text)
        if not clean_text or not intent.strip():
            logger.warning(f"Skipping empty or invalid training example: text='{text}', intent='{intent}'")
            return False

        try:
            self.cursor.execute(
                "INSERT INTO training_data (text, intent, source) VALUES (?, ?, ?)",
                (clean_text, intent.lower(), source)
            )
            self.conn.commit()
            logger.info(f"Added training example to DB: '{text}' -> {intent}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to add training example to DB: {e}")
            self.conn.rollback()
            return False

    def _add_initial_examples(self):
        """Add initial training examples to the database if the database is new/empty."""
        self.cursor.execute("SELECT COUNT(*) FROM training_data")
        if self.cursor.fetchone()[0] == 0:
            logger.info("Adding initial training examples to an empty database.")
            test_phrases = [
                ("what time is it now", "get_time"),
                ("current time", "get_time"),
                ("what's the current time", "get_time"),
                ("tell me the time", "get_time"),
                ("what's the time", "get_time"),

                ("hello there", "greeting"),
                ("hi", "greeting"),
                ("hey", "greeting"),
                ("howdy", "greeting"),
                ("good morning", "greeting"),
                ("good afternoon", "greeting"),
                ("good evening", "greeting"),

                ("what's the weather in London", "get_weather"),
                ("tell me the temperature", "get_weather"),
                ("how's the weather looking today", "get_weather"),
                ("will it rain tomorrow in Paris", "get_weather"),
                ("weather in Delhi", "get_weather"),
                ("temperature in Mumbai", "get_weather"),
                ("is it sunny in New York", "get_weather"),
                ("weather for paudi garhwal", "get_weather"),  # Added for your specific testing
                ("how is the weather today", "get_weather"),  # Common phrase
                ("weather", "get_weather"),  # Simple weather query

                ("who made you", "system_info"),
                ("what can you do", "system_info"),
                ("tell me about yourself", "system_info"),
                ("what is your purpose", "system_info"),
                ("what is your name", "system_info"),  # Added for direct handling
                ("who created you", "system_info"),  # Added for direct handling
                ("about yourself", "system_info"),

                ("exit the program", "exit"),
                ("stop listening", "exit"),
                ("terminate program", "exit"),
                ("goodbye", "exit"),
                ("go to sleep", "exit"),
                ("shut down", "exit"),
                ("I am done", "exit"),
                ("you can stop now", "exit"),
                ("quit", "exit"),  # General quit command

                ("who is Albert Einstein", "get_info"),
                ("what is the capital of France", "get_info"),
                ("where is the Eiffel Tower", "get_info"),
                ("how does a volcano erupt", "get_info"),
                ("find information about gravity", "get_info"),
                ("show me facts about space", "get_info"),
                ("tell me about artificial intelligence", "get_info"),
                ("who is Honey Singh", "get_info"),  # Added your specific query
                ("who is narendra modi", "get_info")  # Added your specific query
            ]

            for text, intent in test_phrases:
                self._add_single_training_example_to_db(text, intent, source='initial')
            logger.info("Initial examples added. Model will be trained upon initialization.")
        else:
            logger.info("Database already contains training data. Skipping initial examples addition.")

    def add_training_example(self, text: str, intent: str, source: str = 'user_feedback') -> bool:
        """Add new training example to database and potentially trigger retraining."""
        success = self._add_single_training_example_to_db(text, intent, source)
        if success:
            # Check if we have enough samples to retrain AFTER adding this one
            self.cursor.execute("SELECT COUNT(DISTINCT intent) FROM training_data")
            distinct_intents = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT intent, COUNT(*) FROM training_data GROUP BY intent")
            intent_counts = dict(self.cursor.fetchall())

            # Check if all intents now have at least min_samples_per_class
            all_intents_have_min = all(count >= self.min_samples_per_class for count in intent_counts.values())

            # Trigger retraining if we have enough distinct intents (at least 2) AND
            # all intents have at least min_samples_per_class
            if distinct_intents >= 2 and all_intents_have_min:
                self._train_and_save_model()
            else:
                logger.warning(
                    f"Not enough data for robust training yet. "
                    f"Distinct intents: {distinct_intents}. "
                    f"Minimum samples needed per class: {self.min_samples_per_class}. "
                    f"Current counts: {intent_counts}"
                )
            return True
        return False

    def predict_intent(self, text: str) -> Tuple[str, Optional[str], str, float]:
        """Predict intent with enhanced error handling and confidence"""
        if not text.strip():
            self._log_query(text, predicted_intent="unknown", confidence=0.0)
            return ("unknown", None, "unknown", 0.0)

        clean_text = self._preprocess_text(text)
        if not clean_text:
            self._log_query(text, predicted_intent="unknown", confidence=0.0)
            return ("unknown", None, "unknown", 0.0)

        predicted_intent = "unknown"
        confidence = 0.0
        entity = None
        intent_type = "unknown"

        try:
            if not self.is_trained or self.model is None:  # Explicitly check for model existence
                logger.warning("Model not trained or loaded. Using fallback patterns.")
                predicted_intent, entity, intent_type, confidence = self._fallback_intent(text, 0.0)
            else:
                # Get prediction from model
                predicted_intent = self.model.predict([clean_text])[0]
                probas = self.model.predict_proba([clean_text])[0]
                confidence = max(probas)

                # Fallback for low confidence
                if confidence < self.confidence_threshold:
                    predicted_intent, entity, intent_type, confidence = self._fallback_intent(text, confidence)
                else:
                    # If model prediction is confident, resolve intent and entity based on that prediction
                    resolved_tuple = self._resolve_intent(predicted_intent, text)
                    predicted_intent = resolved_tuple[0]  # The resolved intent might be slightly different or confirmed
                    entity = resolved_tuple[1]
                    intent_type = resolved_tuple[2]

            self._log_query(text, predicted_intent=predicted_intent, confidence=confidence)

            return (predicted_intent, entity, intent_type, confidence)

        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            self._log_query(text, predicted_intent="error", confidence=0.0)
            # Ensure a valid tuple is always returned even on error
            return self._fallback_intent(text, 0.0)

    def _fallback_intent(self, text: str, confidence: float) -> Tuple[str, Optional[str], str, float]:
        """Handle low-confidence predictions with pattern matching"""
        clean_text = text.lower()

        # Check common patterns
        for intent, triggers in self.common_patterns.items():
            if any(trigger in clean_text for trigger in triggers):
                logger.info(f"Used fallback pattern for: {intent}")
                # Ensure _resolve_intent returns 3 values (intent, entity, intent_type)
                result = self._resolve_intent(intent, text)
                # Unpack the 3 values from result and then add the confidence
                return (*result, max(confidence, 0.8))  # Boost confidence for matched patterns

        # If no pattern matches, default to unknown
        return ("unknown", None, "unknown", confidence)

    def _log_query(self, text: str, predicted_intent: Optional[str] = None, confidence: Optional[float] = None) -> None:
        """Log user query to database, including predicted intent and confidence."""
        try:
            self.cursor.execute(
                "INSERT INTO queries (text, predicted_intent, confidence) VALUES (?, ?, ?)",
                (text, predicted_intent, confidence)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to log query: {e}")

    def provide_feedback(self, text: str, correct_intent: str) -> bool:
        """Provide feedback to improve model with validation"""
        if not text.strip() or not correct_intent.strip():
            logger.warning("Skipping feedback: text or correct_intent is empty.")
            return False

        try:
            # Update the most recent query that matches 'text' with the correct_intent
            self.cursor.execute(
                """UPDATE queries
                   SET correct_intent = ?
                   WHERE id = (
                       SELECT id FROM queries
                       WHERE text = ?
                       ORDER BY timestamp DESC
                       LIMIT 1
                   )""",
                (correct_intent.lower(), text)
            )

            # Check if this example is already in training_data with the correct intent
            self.cursor.execute(
                "SELECT COUNT(*) FROM training_data WHERE text = ? AND intent = ?",
                (self._preprocess_text(text), correct_intent.lower())
            )
            already_trained = self.cursor.fetchone()[0] > 0

            # If not already trained with this intent, add it
            if not already_trained:
                logger.info(f"Adding '{text}' with correct intent '{correct_intent}' to training data due to feedback.")
                # Use the main add_training_example which handles the retraining logic
                return self.add_training_example(text, correct_intent)
            else:
                logger.info(
                    f"Feedback recorded: '{text}' should be '{correct_intent}' (already in training data with correct intent)."
                )
                self.conn.commit()  # Commit the update to queries table
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error while providing feedback: {e}", exc_info=True)
            self.conn.rollback()
            return False

    def _preprocess_text(self, text: str) -> str:
        """Enhanced text cleaning and normalization"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with space
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        words = [w for w in text.split() if len(w) > 2]  # Remove short words
        return ' '.join(words)

    def _resolve_intent(self, intent: str, text: str) -> Tuple[str, Optional[str], str]:
        """Resolve intent to type and extract entities with more cases"""
        text_lower = text.lower()
        entity = None
        intent_type = "unknown"  # Default type

        if intent == "get_time":
            intent_type = "time_query"
        elif intent == "get_weather":
            entity = self._extract_location(text)
            intent_type = "weather_query"
        elif intent == "system_info":
            intent_type = "system_query"
            # Specific entity extraction for system_info questions
            if "what is your name" in text_lower:
                entity = "your name"
            elif "who created you" in text_lower or "who made you" in text_lower:
                entity = "creator"
            elif "what can you do" in text_lower or "your purpose" in text_lower:
                entity = "capabilities"
        elif intent == "greeting":
            intent_type = "greeting"
        elif intent == "exit":
            intent_type = "exit_command"
            entity = "terminate"
        elif intent == "get_info":
            intent_type = "information_query"
            # Extract the noun phrase after common query starters
            info_match = re.search(r'(?:who is|what is|where is|how does|find|show me|tell me about)\s+(.+)', text,
                                   re.IGNORECASE)
            if info_match:
                entity = info_match.group(1).strip()
                entity = re.sub(r'\?$', '', entity)  # Remove trailing question mark
                if entity.lower().startswith(("the ", "a ", "an ")):
                    entity = ' '.join(entity.split()[1:])
                if entity.lower() == "your name" or entity.lower() == "who created you" or entity.lower() == "who made you":
                    # Avoid searching for self-referential questions
                    entity = None  # Set to None so GhostCore can handle it locally

        return (intent, entity, intent_type)

    def _extract_location(self, text: str) -> Optional[str]:
        """Enhanced location extraction from queries"""
        text_lower = text.lower()

        # Priority 1: Look for explicit "weather in X" or "weather for X" patterns
        location_match = re.search(
            r'\b(?:in|at|for|near|around)\s+([\w\s]+?)(?:\s+(?:please|thanks|thank you|now))?$',
            text_lower
        )
        if location_match:
            location = location_match.group(1).strip()
            if len(location.split()) == 1 and location.lower() in ["the", "a", "an", "this", "that", "it", "today",
                                                                   "tomorrow"]:
                return None
            return location

        # Priority 2: Look for capitalized words as potential locations (e.g., "London", "New York", "Paudi Garhwal")
        # This is a heuristic and can lead to false positives, but helps with unpatterned locations.
        capitalized_words_matches = re.findall(r'\b[A-Z][a-zA-Z]*(?:\s[A-Z][a-zA-Z]*)*\b', text)
        if capitalized_words_matches:
            # Filter out common non-location capitalized words if possible (e.g., "Today", "Tomorrow")
            filtered_locations = [
                w for w in capitalized_words_matches
                if w.lower() not in ["today", "tomorrow", "weather", "forecast", "temperature", "india"]  # Added India
            ]
            if filtered_locations:
                return ' '.join(filtered_locations)

        return None

    def get_uncertain_queries(self, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Get queries with low prediction confidence"""
        try:
            self.cursor.execute("""
                SELECT text, confidence FROM queries 
                WHERE confidence < ? AND correct_intent IS NULL
                ORDER BY timestamp DESC
            """, (threshold,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Failed to get uncertain queries: {e}")
            return []

    def close(self):
        """Close database connection safely"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to close database: {e}")


# If you run this file directly, it will re-initialize the model and add examples
if __name__ == "__main__":
    # This block is primarily for testing and initial setup of the model/DB
    # In normal operation, GhostCore will initialize IntentRecognizer
    recognizer = IntentRecognizer()
    logger.info("IntentRecognizer initialized. Database and model setup complete.")

    # You can add further testing here if needed
    print("\n--- Testing Intent Recognition ---")
    test_phrases_for_prediction = [
        "what is the time now",
        "hello",
        "how is the weather in paudi garhwal",
        "who made you",
        "go to sleep",
        "who is narendra modi",
        "tell me about honey singh",
        "what is your name",  # Test system info directly
        "this is a random sentence",
        "shut down"
    ]

    for phrase in test_phrases_for_prediction:
        intent, entity, intent_type, confidence = recognizer.predict_intent(phrase)
        print(f"\nPhrase: '{phrase}'")
        print(f"  -> Intent: {intent} ({intent_type})")
        print(f"  -> Confidence: {confidence:.2f}")
        print(f"  -> Entity: {entity if entity else 'None'}")

        # Simulate feedback for unknown/low confidence
        if confidence < recognizer.confidence_threshold or intent == "unknown":
            feedback = input(f"   What should '{phrase}' be? (e.g., get_info, exit, or skip): ").strip()
            if feedback:
                recognizer.provide_feedback(phrase, feedback)
            else:
                logger.info("   No feedback provided.")

    recognizer.close()
    logger.info("IntentRecognizer test finished.")
import asyncio
from googlesearch import search as google_search
from groq import Groq
import json
import datetime
import os
from dotenv import load_dotenv
import logging
import re
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RealTimeSearchEngine:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GroqAPIKey"))
        self.assistant_name = os.getenv("Assistantname", "AI Assistant")
        self._setup_data_storage()
        self.system_instructions = self._create_system_instructions()

    def _setup_data_storage(self):
        """Initialize data directory and chat log"""
        self.data_dir = "Data"
        self.chat_log_path = os.path.join(self.data_dir, "ChatLog.json")
        os.makedirs(self.data_dir, exist_ok=True)
        self.messages = self._load_chat_history()

    def _create_system_instructions(self):
        """Generate system instructions for the assistant"""
        return f"""
        You are {self.assistant_name}, an AI assistant that provides concise information.
        Respond with:
        - Complete, well-structured paragraphs
        - Current, accurate data
        - Natural flowing text
        - No sources or timestamps
        """

    def _load_chat_history(self) -> List[Dict]:
        """Load chat history from JSON file"""
        try:
            if os.path.exists(self.chat_log_path):
                with open(self.chat_log_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Chat history error: {e}")
            return []

    def _clean_response(self, text: str) -> str:
        """Format the response into clean, well-spaced paragraphs"""
        if not text:
            return ""

        # Remove all technical references
        text = re.sub(
            r'(at \d{1,2}:\d{2} [AP]M)|(as of .*?\d{4})|(http\S+|www\S+)',
            '',
            text,
            flags=re.IGNORECASE
        )
        text = re.split(r'Sources:|References:|According to', text, flags=re.IGNORECASE)[0]

        # Clean up punctuation and spacing
        text = re.sub(r'\s+,', ',', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s{2,}', ' ', text).strip()

        # Ensure proper capitalization
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        # Split into sentences and create paragraphs
        sentences = [s.strip() + '.' for s in re.split(r'\.\s+', text) if s.strip()]

        # Group sentences into paragraphs (3-4 sentences per paragraph)
        paragraphs = []
        for i in range(0, len(sentences), 3):
            paragraph = ' '.join(sentences[i:i + 3])
            paragraphs.append(paragraph)

        return '\n\n'.join(paragraphs) or "No information available"


    def _search_web(self, query: str) -> List[str]:
        """Perform Google search and return results"""
        try:
            return list(google_search(
                query, num=5, stop=5, pause=2.0, lang="en"
            ))
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _get_search_context(self, query: str) -> str:
        """Generate context for the query"""
        return (
            f"Current time: {datetime.datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}\n"
            f"Sources:\n{'\n'.join(self._search_web(query)) or 'No sources found'}"
        )

    async def query(self, query: str) -> str:
        """Process user query and return formatted response"""
        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": f"Query: {query}\nContext:\n{self._get_search_context(query)}"}
                ],
                temperature=0.7,
                max_tokens=1024
            ).choices[0].message.content

            return self._clean_response(response) if response else "No response generated"

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return f"Error: {str(e)}"

    def _save_chat_history(self):
        """Save current conversation to file"""
        try:
            with open(self.chat_log_path, 'w') as f:
                json.dump(self.messages, f, indent=4)
        except Exception as e:
            logger.error(f"History save failed: {e}")

    async def chat_loop(self):
        """Run interactive chat loop"""
        print(f"{self.assistant_name}: Ask me anything about current information!")

        while True:
            try:
                user_input = input("\nYour query (or 'quit'): ").strip()
                if user_input.lower() in ('quit', 'exit'):
                    break

                print("\nGathering information...")
                response = await self.query(user_input)
                print(f"\n{self.assistant_name}: {response}")

                # Update and save history
                self.messages.extend([
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": response}
                ])
                self._save_chat_history()

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break


if __name__ == "__main__":
    assistant = RealTimeSearchEngine()
    asyncio.run(assistant.chat_loop())
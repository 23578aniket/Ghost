👻 Ghost AI Assistant

A high-performance, responsive desktop assistant built in Python. This project features a unique hybrid concurrency model combining PyQt5 for a non-blocking GUI with an asyncio-powered backend running on a dedicated QThread.

🚀 Core Capabilities

This architecture is engineered for reliability, ensuring the user interface remains completely fluid and responsive even during intensive tasks like real-time voice processing and external API calls.

Feature Area

Icon

Description

Hybrid Concurrency

🚀

A dedicated QThread hosts and manages the asyncio event loop, completely isolating the AI core's heavy lifting from the main GUI thread.

Thread Safety

🛡️

All communication between the worker thread and the main thread is strictly handled via PyQt Signals (pyqtSignal) to prevent race conditions and deadlocks.

Asynchronous Core

👂

The GhostCore logic is optimized for I/O-bound tasks (mic input, API latency, TTS) using asynchronous coroutines.

Real-Time Feedback

🗣️

Instant status updates (Idle, Listening, Thinking, Speaking) are signaled back to the UI for a fluid user experience.

UI Responsiveness

🎨

Built with PyQt5 to ensure window management, drawing, and button clicks are instantaneous, regardless of backend activity.

Graceful Shutdown

🧹

Robust logic to ensure the worker thread and its embedded event loop are terminated cleanly and safely on application exit.

🛠️ Technology Stack (Architecture)

This project demonstrates an advanced understanding of managing concurrency in Python desktop applications by bridging two powerful, but fundamentally different, frameworks.

Category

Library/Module

Core Functionality Demonstrated

GUI Framework

PyQt5

Main application window, custom top bar, navigation, and user interaction components.

Concurrency Model

QThread, QObject

Provides a dedicated, managed operating system thread to run the intensive backend processes.

Asynchronous Engine

asyncio

The heart of the AI processing logic, managing I/O without blocking the worker thread.

Communication Bridge

pyqtSignal, call_soon_threadsafe

The mechanism for thread-safe input (GUI → Core) and output (Core → GUI).

Configuration

python-dotenv

Loads assistant configuration and API credentials from a local .env file.

🔧 Setup and Installation

1. Project Structure

Ensure your project files are organized as follows:

/Ghost-AI-Assistant
├── Backend/
│   └── GhostCore.py       # (Your AI Logic goes here)
├── Frontend/
│   ├── Files/             # Runtime data and state files
│   └── Graphics/          # UI icons and assets
├── .env                   # Configuration file
└── assistant_gui.py       # Main Application


2. Install Dependencies

# Recommended: Create and activate a virtual environment first

# Install core GUI and configuration libraries
pip install PyQt5 python-dotenv

# Note: Additional libraries required by GhostCore (e.g., sounddevice, Google GenAI SDKs, etc.)
# must also be installed, typically via a requirements.txt file.


3. Environment Configuration

Create a file named .env in the root directory to define the assistant's name:

Assistantname="Ghost"
# Add any required API keys (e.g., for LLMs) here


4. Run the Application

python assistant_gui.py


⚙️ How to Use

The application launches the AI engine in the background worker thread immediately upon startup.

Interaction Flow

Home Screen: The application starts on the InitialScreen (Home), displaying the current status (e.g., "Idle").

Activate Listening: Click the large microphone icon. This emits a signal that safely activates the listening coroutine in the backend event loop. The UI status will change to "Listening".

Interact: Speak your command. The status will transition through "Processing" and "Speaking".

View History: Click the "Chat" button in the top bar to review a running log of all commands and AI responses in the ChatSection.

Exit Safely: Click the close button (X) in the top bar. The MainWindow will execute a controlled, graceful shutdown, stopping the worker thread before closing the application.

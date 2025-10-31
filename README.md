Ghost AI Assistant

A robust, multi-threaded AI Assistant application featuring a responsive Graphical User Interface (GUI) built with PyQt5 and an asynchronous backend core powered by asyncio. This architecture is designed specifically to handle intensive, non-blocking operations like voice processing, real-time audio streams, and external AI API calls concurrently without ever freezing the main user interface.

🚀 Key Features

Responsive GUI (PyQt5): A custom, frameless desktop application interface ensures a modern look and feel. The UI is built entirely in the main thread, guaranteeing fluid animations and instant button responses.

Hybrid Concurrency Model (QThread + Asyncio): The most critical feature. A dedicated QThread hosts and manages the asyncio event loop where all intensive logic resides, effectively isolating the GUI from the computational load.

Asynchronous Core (GhostCore): The core AI logic operates asynchronously, making it highly efficient for managing numerous I/O-bound tasks (mic input, API requests, text-to-speech output).

Thread-Safe Communication: Communication is strictly managed using PyQt Signals (pyqtSignal). This guarantees that data passed between the backend Worker Thread and the frontend Main Thread is safe and prevents concurrency issues.

Real-time Status Updates: Provides immediate visual feedback (e.g., Idle, Listening, Thinking) to the user via signals, enhancing the interactive experience.

Graceful Shutdown: Robust logic in MainWindow.closeEvent ensures the worker thread and the embedded asyncio event loop are terminated cleanly, preventing application deadlocks on exit.

🛠️ Architecture Deep Dive

The project solves the "GUI-blocking" problem by separating responsibilities into two independent environments:

1. Main Thread (UI Layer)

The primary execution thread. It contains:

assistant_gui.py: Initializes the application and the MainWindow.

UI Components: InitialScreen (Home/Mic), ChatSection (Message Log).

Role: Only handles visual updates and capturing initial user input (like clicking the microphone button).

2. Worker Thread (Logic Layer)

A secondary, dedicated thread responsible for concurrency and heavy lifting. It contains:

GhostCoreWorker (QObject): This is the bridge object that lives inside the QThread. Its role is to start the asyncio event loop and safely expose entry points (Slots) for the Main Thread.

GhostCore (Async Logic): Contains the actual AI routines, microphone handling, and API call logic.

Communication Bridge

The GhostCoreWorker is key to crossing the thread barrier:

Direction

Trigger Mechanism

Method Used

Purpose

GUI → Core

mic_toggle_requested Signal (from UI click)

asyncio.run_coroutine_threadsafe()

Safely queues the synchronous Qt input into the asynchronous Python event loop running in the worker thread.

Core → GUI

status_update_signal, chat_message_signal

pyqtSignal

Carries generated text or status strings from the Worker Thread back to the Main Thread for display without blocking the UI.

⚙️ Prerequisites

You must have Python 3.8+ installed.

Dependencies

This project requires PyQt5, python-dotenv, and the custom GhostCore module (which handles the core AI/voice logic).

pip install PyQt5 python-dotenv
# Additional dependencies for voice/AI processing (e.g., sounddevice, openai, etc.) may be required by GhostCore.py


Project Structure

A clean, modular structure is used to separate the frontend, backend logic, and application assets:

/Ghost-AI-Assistant
├── Backend/
│   └── GhostCore.py       # (Critical: Contains the core asyncio AI/voice processing logic)
├── Frontend/
│   ├── Files/             # Runtime files (e.g., Mic.data, Status.data for temporary state tracking)
│   └── Graphics/          # UI assets (Jarvis.gif, Mic_on.png, Mic_off.png, etc.)
├── .env                   # Configuration file (Assistantname, API keys, etc.)
└── assistant_gui.py       # The main PyQt application entry point


🏁 Getting Started

Setup: Ensure you have the project structure defined above, including the critical GhostCore.py file.

Install Dependencies: Run the installation command:

pip install PyQt5 python-dotenv


Configure Environment: Create a file named .env in the root directory to store configuration:

Assistantname="Ghost"
# Add your API keys and configuration specific to the GhostCore backend here.


Run the Application: Execute the main script:

python assistant_gui.py


💡 Usage

Initial Screen: The application launches to the InitialScreen (Home). The status label will typically display "Idle" initially.

Activate Voice: Click the large microphone icon.

This sends a signal from the Main Thread.

The GhostCoreWorker receives the signal and starts the listening coroutine in the asyncio loop.

The icon updates to the "Listening" state once the backend confirms the change.

View Chat History: Click the "Chat" button in the top bar. This switches the view to the ChatSection, displaying a real-time log of all interactions (user commands and AI responses).

Shutdown: Use the close button (X) in the top bar. The application executes a controlled shutdown sequence:

Tells the worker thread to quit (.quit()).

Waits for the worker thread to finish its event loop cleanup (.wait()).

If termination is delayed, it forcefully terminates the thread (as a fallback).
This process is crucial for preventing zombie processes and deadlocks.

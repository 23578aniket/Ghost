# 👻 Ghost AI Assistant

A high-performance, responsive desktop assistant built with a hybrid concurrency model: PyQt5 for the UI and an asynchronous (asyncio) backend core, ensuring zero UI freezing.

## ✨ Features at a Glance

- **Hybrid Concurrency (🚀):** A dedicated QThread manages the asyncio event loop for the AI core, completely isolating heavy lifting from the UI.

- **Thread Safety (🛡️):** Uses PyQt's Signals (pyqtSignal) for all cross-thread communication, ensuring stable and reliable data transfer.

- **Asynchronous Core (GhostCore) (👂):** Optimized for I/O-bound tasks like mic processing, API latency, and TTS generation.

- **Real-Time Feedback (🗣️):** Instant status updates (Idle, Listening, Thinking) are signaled back to the UI for a fluid user experience.

- **Chat History (💬):** Dedicated screen for logging and viewing command history and AI responses.

- **Graceful Shutdown (🧹):** Implements robust cleanup logic to terminate the worker thread and event loop cleanly upon exit.

## 🏗️ Architecture Deep Dive: The Hybrid Model

The core innovation of this project is solving the common problem of GUI applications freezing when the backend is busy. We achieve this by strictly dividing labor:

### 1. The Main Thread (The Presenter)

 - **Role:** Runs the PyQt application (assistant_gui.py). Handles window management, drawing pixels, and capturing simple user input (e.g., button clicks).

 - **Status:** Must remain unblocked at all times to ensure a responsive feel.

### 2. The Worker Thread (The Processor)

- **Role:** Launched by MainWindow, this dedicated QThread hosts the GhostCoreWorker. This worker's primary job is to instantiate and run the Python asyncio   event loop.

 - **Logic**: The AI logic (GhostCore) runs inside this loop, where it can manage multiple I/O operations (like waiting for mic input or an API response) concurrently without blocking the worker thread itself.

## The Communication Bridge

To safely bridge the synchronous GUI world and the asynchronous backend world, the GhostCoreWorker uses specialized, thread-safe methods:

- GUI → Core (Request Signal / Synchronous Input):
  - The Main Thread's UI triggers a Qt signal which is connected to a slot in the GhostCoreWorker.
  - The worker slot then uses asyncio.run_coroutine_threadsafe() to safely push the command into the running asynchronous event loop.

- Core → GUI (Response Signal / Asynchronous Output):
  - The GhostCore instance emits standard pyqtSignal objects when it has text or status to report.
  - Qt automatically queues and delivers these signals safely to the Main Thread for immediate UI updates.

## 📁 Project Structure

**/Ghost-AI-Assistant**

├── Backend/

│   └── * (All Python logic and non-GUI modules reside here)*

├── Frontend/

│   ├── Files/             # Runtime files (Mic.data, Status.data for temporary state tracking).

│   └── Graphics/          # UI assets (GIFs, PNG icons).

├── .env                   # Configuration file (Assistantname, API keys).

└── assistant_gui.py       # Main PyQt application entry point and thread manager.


## ⚙️ Installation and Setup

### 1. Prerequisites

Ensure you have a modern Python environment (Python 3.8+).

### 2. Install Dependencies

pip install PyQt5 python-dotenv
NOTE: Depending on your GhostCore.py, additional dependencies for voice (e.g., PyAudio, sounddevice)
and AI services (e.g., Google GenAI SDKs) may be required.


### 3. Environment Configuration

Create a file named .env in the root directory to define the assistant's name and API credentials:

Assistantname="Ghost"
Placeholder for any sensitive API keys or configuration needed by GhostCore.py
OPENAI_API_KEY="sk-..."


### 4. Run the Application

python assistant_gui.py


## 🎤 Usage

- **1. Home Screen:** The application launches to the InitialScreen. Look for the status message (e.g., "Idle").

- **2. Activate Listening:** Click the microphone icon. This triggers the thread-safe activation sequence. The icon and status will update to "Listening".

- **3. Interact:** Speak your command or trigger phrase.

- **4. View Log:** Click the "Chat" button in the top bar to review the full interaction history in the ChatSection.

- **5. Exit:** Use the close button (X) in the top bar. The application will execute its graceful shutdown routine to stop the worker thread before closing.

Ghost AI Assistant

A robust, multi-threaded AI Assistant application featuring a responsive Graphical User Interface (GUI) built with PyQt5 and an asynchronous backend core powered by asyncio. The project is designed to handle intensive, non-blocking operations like voice processing and AI interaction concurrently without freezing the UI.

🚀 Key Features

Responsive GUI: A custom, frameless desktop application interface built using PyQt5.

Hybrid Concurrency Model: Utilizes a dedicated QThread to run the asyncio event loop for the AI logic, ensuring the main GUI thread remains responsive at all times.

Asynchronous Core (GhostCore): The AI logic runs asynchronously, capable of handling complex I/O tasks efficiently.

Thread-Safe Communication: All interaction between the GUI (Main Thread) and the AI Core (Worker Thread) is managed safely using custom PyQt Signals (pyqtSignal).

Real-time Status Updates: Provides immediate feedback on the assistant's state (e.g., Idle, Listening, Processing).

Graceful Shutdown: Implements robust thread shutdown logic in closeEvent to ensure clean exit of the worker thread and the asyncio loop.

🛠️ Architecture Overview

The application is structured into two primary concurrent components:

Main Thread (GUI): Runs the PyQt application (MainWindow, InitialScreen, ChatSection). Responsible solely for drawing the UI and handling user input events (like button clicks).

Worker Thread (Backend Logic): A separate QThread hosts the GhostCoreWorker object.

The GhostCoreWorker starts and manages the asyncio event loop.

The GhostCore instance runs its main logic within this loop.

Communication Bridge

A key design element is the safe transition between the synchronous Qt environment and the asynchronous Python environment:

GUI to Core (Sync -> Async): When the user clicks the microphone button, the InitialScreen emits a mic_toggle_requested signal. This signal is connected to the GhostCoreWorker.toggle_mic slot, which is executed in the worker thread. Inside this slot, asyncio.run_coroutine_threadsafe() is used to safely queue the command into the running asyncio loop.

Core to GUI (Async -> Sync): When the GhostCore has a message or a status update, it emits pre-defined signals (status_update_signal, chat_message_signal). These signals carry data across the thread boundary and are handled by the slots in the main GUI thread (update_status_label, add_chat_message).

⚙️ Prerequisites

You must have Python 3.8+ installed.

Dependencies

This project requires PyQt5, python-dotenv, and the custom GhostCore module which handles the core AI and voice logic.

pip install PyQt5 python-dotenv


Project Structure

Ensure your file structure includes the necessary components, particularly the Backend directory containing the AI logic:

/Ghost-AI-Assistant
├── Backend/
│   └── GhostCore.py       # (Critical dependency for AI logic)
├── Frontend/
│   ├── Files/             # Temp directory for status files (Mic.data, Status.data)
│   └── Graphics/          # Contains necessary assets (Jarvis.gif, Mic_on.png, etc.)
├── .env                   # Configuration file (e.g., Assistantname)
└── assistant_gui.py       # The main application script


🏁 Getting Started

Clone the Repository (or download files):

# (Assuming you have GhostCore.py and assets in place)


Install Dependencies:

pip install PyQt5 python-dotenv


Configure Environment:
Create a file named .env in the root directory:

Assistantname="Ghost"
# Add any other required backend configuration here


Run the Application:

python assistant_gui.py


💡 Usage

Start Screen: The application launches to the InitialScreen (Home). The status label will display the current state.

Activate Voice: Click the microphone icon. This emits a signal to the backend to start the listening process. The icon will update once the GhostCore confirms it is in an "active" state.

View Chat: Click the "Chat" button in the top bar to switch to the MessageScreen and see a log of all interactions.

Shutdown: Use the close button (X) in the top bar. The application is configured to attempt a clean shutdown of the worker thread before closing the window.

from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QHBoxLayout, QVBoxLayout, \
    QPushButton, QFrame, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat, QMovie
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QObject # Import QThread, pyqtSignal, QObject
from dotenv import dotenv_values
import sys
import os
import asyncio # Import asyncio to run the loop in a thread

# --- IMPORTANT: Import GhostCore ---
from Backend.GhostCore import GhostCore # Make sure this path is correct based on your project structure

# --- Global Configurations ---
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "Assistant")

current_dir = os.getcwd()

# Using os.path.join for cross-platform compatibility
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")

# Ensure the directories exist
os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(GraphicsDirPath, exist_ok=True)

def SetMicrophoneStatus(command):
    with open(os.path.join(TempDirPath, 'Mic.data'), "w", encoding='utf-8') as file:
        file.write(command)

def GetMicrophoneStatus():
    try:
        with open(os.path.join(TempDirPath, 'Mic.data'), "r", encoding='utf-8') as file:
            status = file.read()
        return status
    except FileNotFoundError:
        SetMicrophoneStatus("False")
        return "False"

def SetAssistantStatus(status):
    with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(status)

def GetAssistantStatus():
    try:
        with open(os.path.join(TempDirPath, 'Status.data'), "r", encoding='utf-8') as file:
            status = file.read()
        return status
    except FileNotFoundError:
        SetAssistantStatus("Idle")
        return "Idle"

def GraphicsDirectoryPath(filename):
    return os.path.join(GraphicsDirPath, filename)

def TempDirectoryPath(filename):
    return os.path.join(TempDirPath, filename)


# --- NEW: Worker class to run GhostCore in a separate thread ---
class GhostCoreWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, ghost_core_instance):
        super().__init__()
        self.ghost_core = ghost_core_instance

    def run(self):
        try:
            asyncio.run(self.ghost_core.run_async_loop())
        except Exception as e:
            print(f"Error in GhostCoreWorker: {e}")
        finally:
            self.finished.emit()


# --- ChatSection Class ---
class ChatSection(QWidget):

    def __init__(self, parent=None): # Added parent for better widget hierarchy
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)
        self.setStyleSheet("background-color: black;")
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Initial text color for chat
        text_char_format = QTextCharFormat()
        text_char_format.setForeground(QColor(Qt.blue))
        self.chat_text_edit.setCurrentCharFormat(text_char_format)

        # GIF label setup
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)

        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)


        self.chat_text_edit.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                subcontrol-position: top;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    # Slot to receive chat messages from GhostCore
    def add_chat_message(self, sender: str, message: str, is_user: bool):
        cursor = self.chat_text_edit.textCursor()
        text_format = QTextCharFormat()
        block_format = QTextBlockFormat()
        block_format.setTopMargin(10)
        block_format.setLeftMargin(10)

        # Use different colors for user and assistant
        if is_user:
            text_format.setForeground(QColor("lightblue")) # User messages
            block_format.setAlignment(Qt.AlignRight) # Align user messages to the right
        else:
            text_format.setForeground(QColor("white")) # Assistant messages
            block_format.setAlignment(Qt.AlignLeft) # Align assistant messages to the left

        cursor.setCharFormat(text_format)
        cursor.setBlockFormat(block_format)
        cursor.insertText(f"{sender}: {message}\n")
        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.ensureCursorVisible() # Auto-scroll to the bottom


# --- InitialScreen Class ---
class InitialScreen(QWidget):
    # Signal to communicate microphone toggle to GhostCore
    mic_toggle_requested = pyqtSignal(bool) # True for activate, False for deactivate

    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(0, 0, 0, 0)

        gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        gif_label.setMovie(movie)
        max_gif_size_H = int(screen_width / 16 * 9)
        movie.setScaledSize(QSize(screen_width, max_gif_size_H))
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-bottom:0;")
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # IMPORTANT: Initial toggle state should be based on GhostCore's actual state, not file
        # For now, we initialize to False (mic off) and let GhostCore update it.
        self.is_mic_active_in_ui = False # Tracks the UI's perception of mic state
        self._set_mic_icon_state(self.is_mic_active_in_ui) # Set initial icon to off
        self.icon_label.mousePressEvent = self._handle_mic_click # Assign click handler
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        content_layout.setContentsMargins(0, 0, 0, 150)
        self.setStyleSheet("background-color: black;")


    # NEW: Slot to receive status updates from GhostCore
    def update_status_label(self, text: str, state_name: str):
        self.label.setText(text)
        # Optionally, change icon or visual elements based on state_name
        # For example, if state_name is 'listening', update mic icon to 'on'
        if state_name == 'listening' or state_name == 'speaking' or state_name == 'processing':
            if not self.is_mic_active_in_ui: # Only change if UI thinks it's off
                self._set_mic_icon_state(True)
                self.is_mic_active_in_ui = True
        elif state_name == 'idle' or state_name == 'error' or state_name == 'offline':
            if self.is_mic_active_in_ui: # Only change if UI thinks it's on
                self._set_mic_icon_state(False)
                self.is_mic_active_in_ui = False


    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(new_pixmap)

    def _set_mic_icon_state(self, active: bool):
        """Helper to set the mic icon based on its active state."""
        if active:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)


    def _handle_mic_click(self, event=None):
        """Handles click on the microphone icon."""
        # Toggle UI state first, then emit signal to GhostCore
        self.is_mic_active_in_ui = not self.is_mic_active_in_ui
        self._set_mic_icon_state(self.is_mic_active_in_ui)

        # Emit signal to GhostCore to inform it of the requested mic state change
        self.mic_toggle_requested.emit(self.is_mic_active_in_ui)


# --- MessageScreen Class (No changes needed here unless it needs GhostCore signals directly) ---
class MessageScreen(QWidget):
    def __init__(self, chat_section_instance, parent=None): # Pass chat_section
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(chat_section_instance) # Use the passed instance
        self.setStyleSheet("background-color: black;")


# --- CustomTopBar Class (No changes needed here as it controls UI navigation only) ---
class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.initUI()
        self.draggable = True
        self.offset = None

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)

        title_label = QLabel(f" {str(Assistantname).capitalize()} AI")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color: white;")
        layout.addWidget(title_label)
        layout.addStretch(1)

        home_button = QPushButton()
        home_button.setIcon(QIcon(GraphicsDirectoryPath("Home.png")))
        home_button.setText(" Home")
        home_button.setStyleSheet(
            "QPushButton { height: 40px; line-height: 40px; background-color: white; color: black; border: 1px solid gray; padding: 0 10px; } QPushButton:hover { background-color: #f0f0f0; }")
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(home_button)

        message_button = QPushButton()
        message_button.setIcon(QIcon(GraphicsDirectoryPath("Chats.png")))
        message_button.setText(" Chat")
        message_button.setStyleSheet(
            "QPushButton { height: 40px; line-height: 40px; background-color: white; color: black; border: 1px solid gray; padding: 0 10px; } QPushButton:hover { background-color: #f0f0f0; }")
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(message_button)

        layout.addStretch(1)

        minimize_button = QPushButton()
        minimize_button.setIcon(QIcon(GraphicsDirectoryPath("Minimize2.png")))
        minimize_button.setStyleSheet(
            "QPushButton { background-color: white; border: none; } QPushButton:hover { background-color: #e0e0e0; }")
        minimize_button.clicked.connect(self.minimizeWindow)
        layout.addWidget(minimize_button)

        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath("Maximize.png"))
        self.restore_icon = QIcon(GraphicsDirectoryPath("Restore.png"))
        if not os.path.exists(GraphicsDirectoryPath("Restore.png")):
            self.restore_icon = QIcon(GraphicsDirectoryPath("Minimize2.png"))

        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet(
            "QPushButton { background-color: white; border: none; } QPushButton:hover { background-color: #e0e0e0; }")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        layout.addWidget(self.maximize_button)

        close_button = QPushButton()
        close_button.setIcon(QIcon(GraphicsDirectoryPath("Close.png")))
        close_button.setStyleSheet(
            "QPushButton { background-color: white; border: none; } QPushButton:hover { background-color: #e0e0e0; }")
        close_button.clicked.connect(self.closeWindow)
        layout.addWidget(close_button)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset is not None:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def mouseReleaseEvent(self, event):
        self.offset = None


# --- MainWindow Class (Central Hub for Integration) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ghost_core = None # Will hold the GhostCore instance
        self.ghost_core_thread = None # Will hold the QThread for GhostCore
        self.ghost_core_worker = None # Will hold the GhostCoreWorker
        self.initUI()
        self.start_ghost_core() # Start the backend

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget(self) # Make stacked_widget an instance attribute

        self.chat_section = ChatSection() # Create ChatSection instance here
        self.initial_screen = InitialScreen() # Create InitialScreen instance here

        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(MessageScreen(self.chat_section)) # Pass the same chat_section instance

        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")

        top_bar = CustomTopBar(self, self.stacked_widget)
        main_layout.addWidget(top_bar)

        line_separator = QFrame()
        line_separator.setFixedHeight(1)
        line_separator.setFrameShape(QFrame.HLine)
        line_separator.setFrameShadow(QFrame.Sunken)
        line_separator.setStyleSheet("background-color: gray;")
        main_layout.addWidget(line_separator)

        main_layout.addWidget(self.stacked_widget)

        self.setCentralWidget(central_widget)

    def start_ghost_core(self):
        """Initializes and starts GhostCore in a separate thread."""
        self.ghost_core = GhostCore() # Instantiate your backend
        self.ghost_core_thread = QThread() # Create a new thread
        self.ghost_core_worker = GhostCoreWorker(self.ghost_core) # Create worker with core instance

        # Move the worker to the new thread
        self.ghost_core_worker.moveToThread(self.ghost_core_thread)

        # Connect signals and slots
        self.ghost_core_thread.started.connect(self.ghost_core_worker.run)
        self.ghost_core_worker.finished.connect(self.ghost_core_thread.quit)
        self.ghost_core_worker.finished.connect(self.ghost_core_worker.deleteLater)
        self.ghost_core_thread.finished.connect(self.ghost_core_thread.deleteLater)

        # --- IMPORTANT: Connect GhostCore's signals to UI slots ---
        self.ghost_core.status_update_signal.connect(self.initial_screen.update_status_label)
        self.ghost_core.chat_message_signal.connect(self.chat_section.add_chat_message)

        # Connect UI's mic toggle request to GhostCore's state
        self.initial_screen.mic_toggle_requested.connect(self._handle_mic_toggle_request)

        # Start the thread
        self.ghost_core_thread.start()

    def _handle_mic_toggle_request(self, activate_mic: bool):
        """Slot to receive mic toggle requests from the UI and pass to GhostCore."""
        if activate_mic:
            self.ghost_core.voice.is_active = True
            asyncio.run_coroutine_threadsafe(
                self.ghost_core._process_command(text=self.ghost_core.voice.hotword, is_activation=True),
                asyncio.get_event_loop()
            )

        else:
            self.ghost_core.voice.is_active = False
            asyncio.run_coroutine_threadsafe(
                self.ghost_core._process_command(text="deactivate", is_activation=False),
                asyncio.get_event_loop()
            )
            # Again, better to have a direct deactivate method in GhostCore.

    def closeEvent(self, event):
        """Handle window close event for graceful shutdown."""
        if self.ghost_core:
            self.ghost_core.stop() # Tell GhostCore to stop its loop
            self.ghost_core_thread.quit() # Request the thread to quit
            self.ghost_core_thread.wait(5000) # Wait for the thread to finish (max 5 seconds)
            if self.ghost_core_thread.isRunning():
                self.ghost_core_thread.terminate() # Force terminate if it doesn't quit gracefully
                self.ghost_core_thread.wait()
        super().closeEvent(event)


# --- Application Entry Point ---
def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    GraphicalUserInterface()
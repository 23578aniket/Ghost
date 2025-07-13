import datetime
import webbrowser
import subprocess
import requests
import psutil
import platform
import os
import time
import pyautogui
import logging
import calendar # For get_today_date
import wikipedia # For questions (if kept here)
import pywhatkit as wk # For YouTube actions (if kept here)
import sqlite3 # For user database (if kept here)

# Initialize logging for this module
logger = logging.getLogger(__name__)

class SystemActions:
    """
    This class encapsulates all direct system interaction actions that the AI assistant
    can perform. It should be used as a toolset by the main assistant logic.
    """
    def __init__(self):
        # Placeholder for any initialization needed for system interactions
        pass

    # --- Core Information Retrieval ---

    async def get_current_time(self) -> str:
        """Returns the current time in HH:MM AM/PM format."""
        return datetime.datetime.now().strftime("%I:%M %p")

    async def get_today_date(self) -> str:
        """Returns today's date in a friendly format (e.g., 'Today is Wednesday, May the 28th, 2025')."""
        now = datetime.datetime.now()
        date_now = datetime.datetime.today()
        week_now = calendar.day_name[date_now.weekday()]
        month_now = now.month
        day_now = now.day
        year_now = now.year

        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        # Handle ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
        def get_ordinal_suffix(day):
            if 10 <= day % 100 <= 20:
                return 'th'
            else:
                return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

        day_ordinal = f"{day_now}{get_ordinal_suffix(day_now)}"
        today = f"Today is {week_now}, {months[month_now - 1]} the {day_ordinal}, {year_now}"
        return today

    async def get_ip_address(self) -> str:
        """Retrieves the public IP address of the system."""
        try:
            response = requests.get("https://api.ipify.org?format=json")
            response.raise_for_status() # Raise an exception for HTTP errors
            ip_data = response.json()
            return f"Your public IP address is {ip_data['ip']}."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting IP address: {e}")
            return "Sorry, I couldn't retrieve your IP address at this moment."

    # --- Application Control ---

    async def open_application(self, app_name: str) -> str:
        """Opens a specified application like 'notepad', 'chrome', 'calculator', etc."""
        app_name_lower = app_name.lower()
        if platform.system() == "Windows":
            try:
                # Direct executable names for common apps
                if "notepad" in app_name_lower or "text editor" in app_name_lower:
                    subprocess.Popen(["notepad.exe"])
                elif "chrome" in app_name_lower:
                    webbrowser.open("http://google.com") # Opens Chrome to Google
                elif "calculator" in app_name_lower:
                    subprocess.Popen(["calc.exe"])
                elif "task manager" in app_name_lower:
                    subprocess.Popen(["taskmgr.exe"])
                elif "files" in app_name_lower or "explorer" in app_name_lower or "file explorer" in app_name_lower:
                    subprocess.Popen(["explorer.exe"])
                elif "calendar" in app_name_lower:
                    # Windows 10/11 default calendar app
                    subprocess.Popen(["outlookcal:"])
                elif "control panel" in app_name_lower:
                    subprocess.Popen(["control"])
                elif "command prompt" in app_name_lower or "cmd" in app_name_lower:
                    subprocess.Popen(["cmd.exe"])
                elif "power settings" in app_name_lower:
                    subprocess.Popen(["powercfg.cpl"])
                elif "device manager" in app_name_lower:
                    subprocess.Popen(["devmgmt.msc"])
                elif "system properties" in app_name_lower:
                    subprocess.Popen(["sysdm.cpl"])
                elif "network connections" in app_name_lower:
                    subprocess.Popen(["ncpa.cpl"])
                elif "firefox" in app_name_lower:
                    subprocess.Popen(["firefox.exe"])
                elif "edge" in app_name_lower:
                    subprocess.Popen(["msedge.exe"])
                elif "opera" in app_name_lower:
                    subprocess.Popen(["opera.exe"])
                elif "media player" in app_name_lower or "windows media player" in app_name_lower:
                    subprocess.Popen(["wmplayer.exe"])
                else:
                    return f"Sorry, I don't know how to open {app_name} on Windows."
                return f"Opening {app_name} for you."
            except FileNotFoundError:
                return f"Could not find '{app_name}'. Make sure it's installed and in your system's PATH."
            except Exception as e:
                logger.error(f"Error opening {app_name}: {e}")
                return f"An error occurred while trying to open {app_name}."
        else: # For other OS, adapt these commands
            return f"Opening applications is not fully implemented for {platform.system()} yet."

    async def close_application(self, app_name: str) -> str:
        """Closes a running application by its name (e.g., 'notepad', 'chrome', 'firefox')."""
        app_name_lower = app_name.lower()
        # Map common names to actual process names for Windows
        process_names_map = {
            "notepad": "notepad.exe",
            "text editor": "notepad.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "opera": "opera.exe",
            "media player": "wmplayer.exe",
            "windows media player": "wmplayer.exe",
            "task manager": "taskmgr.exe"
            # Add more as needed
        }
        process_to_close = process_names_map.get(app_name_lower, app_name_lower) # Fallback to original if not mapped

        if platform.system() == "Windows":
            try:
                found_and_terminated = False
                for proc in psutil.process_iter(['pid', 'name']):
                    if process_to_close in proc.info['name'].lower():
                        proc.terminate() # Try graceful termination first
                        found_and_terminated = True
                        time.sleep(0.5) # Give it a moment to terminate
                        if proc.is_running(): # If still running, try kill
                            proc.kill()
                if found_and_terminated:
                    return f"Attempted to close {app_name}."
                else:
                    return f"No running process found for {app_name}."
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.warning(f"Error closing {app_name}: {e}")
                return f"Could not close {app_name} due to permissions or process not found."
            except Exception as e:
                logger.error(f"Unexpected error closing {app_name}: {e}")
                return f"An unexpected error occurred while trying to close {app_name}."
        else:
            return f"Closing applications is not fully implemented for {platform.system()} yet."

    # --- System Control ---

    async def shutdown_system(self) -> str:
        """Shuts down the computer system."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["shutdown", "/s", "/t", "1"])
                return "Shutting down your computer."
            else:
                return f"Shutdown command not implemented for {platform.system()}."
        except Exception as e:
            logger.error(f"Error shutting down system: {e}")
            return "Sorry, I couldn't shut down the computer."

    async def restart_system(self) -> str:
        """Restarts the computer system."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["shutdown", "/r", "/t", "1"])
                return "Restarting your computer."
            else:
                return f"Restart command not implemented for {platform.system()}."
        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            return "Sorry, I couldn't restart the computer."

    async def sleep_system(self) -> str:
        """Puts the computer system to sleep."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
                return "Putting the system to sleep."
            else:
                return f"Sleep command not implemented for {platform.system()}."
        except Exception as e:
            logger.error(f"Error putting system to sleep: {e}")
            return "Sorry, I couldn't put the system to sleep."

    async def hibernate_system(self) -> str:
        """Puts the computer system into hibernation."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,1"])
                return "Hibernating the system."
            else:
                return f"Hibernate command not implemented for {platform.system()}."
        except Exception as e:
            logger.error(f"Error hibernating system: {e}")
            return "Sorry, I couldn't hibernate the system."

    async def lock_system(self) -> str:
        """Locks the computer screen."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
                return "Locking the system."
            else:
                return f"Lock command not implemented for {platform.system()}."
        except Exception as e:
            logger.error(f"Error locking system: {e}")
            return "Sorry, I couldn't lock the system."

    # --- UI Control ---

    async def take_screenshot(self, filename: str = "screenshot") -> str:
        """Takes a screenshot of the current screen and saves it as a PNG file."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            full_filename = f"{filename}_{timestamp}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(full_filename)
            return f"Screenshot saved as {full_filename}."
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return "Sorry, I couldn't take a screenshot."

    async def adjust_volume(self, direction: str, steps: int = 5) -> str:
        """Adjusts the system volume up or down."""
        try:
            if direction.lower() == "up":
                for _ in range(steps):
                    pyautogui.press('volumeup')
                return "Volume increased."
            elif direction.lower() == "down":
                for _ in range(steps):
                    pyautogui.press('volumedown')
                return "Volume decreased."
            else:
                return "Invalid volume adjustment direction. Use 'up' or 'down'."
        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")
            return "Sorry, I couldn't adjust the volume."

    async def minimize_all_windows(self) -> str:
        """Minimizes all open windows to show the desktop."""
        try:
            pyautogui.hotkey('win', 'd')
            return "All windows minimized."
        except Exception as e:
            logger.error(f"Error minimizing all windows: {e}")
            return "Sorry, I couldn't minimize all windows."

    async def maximize_window(self) -> str:
        """Maximizes the current active window."""
        try:
            pyautogui.hotkey('win', 'up')
            return "Current window maximized."
        except Exception as e:
            logger.error(f"Error maximizing window: {e}")
            return "Sorry, I couldn't maximize the window."

    async def minimize_window(self) -> str:
        """Minimizes the current active window."""
        try:
            pyautogui.hotkey('win', 'down')
            return "Current window minimized."
        except Exception as e:
            logger.error(f"Error minimizing window: {e}")
            return "Sorry, I couldn't minimize the window."

    # --- Browser Control (via PyAutoGUI hotkeys) ---

    async def control_browser_tab(self, action: str) -> str:
        """
        Controls browser tabs: 'new', 'next', 'previous', 'home', 'close',
        'close_window', 'download_page', 'address_bar', 'login_to_different_user'.
        """
        try:
            if action == "new":
                pyautogui.hotkey('ctrl', 't')
            elif action == "next":
                pyautogui.hotkey('ctrl', 'tab')
            elif action == "previous":
                pyautogui.hotkey('ctrl', 'shift', 'tab')
            elif action == "home":
                pyautogui.hotkey('alt', 'home')
            elif action == "close":
                pyautogui.hotkey('ctrl', 'w')
            elif action == "close_window":
                pyautogui.hotkey('ctrl', 'shift', 'w')
            elif action == "download_page":
                pyautogui.hotkey('ctrl', 'j')
            elif action == "address_bar":
                pyautogui.hotkey('ctrl', 'l')
            elif action == "login_to_different_user":
                pyautogui.hotkey('ctrl', 'shift', 'm')
            else:
                return f"Unsupported browser tab action: {action}."
            return f"Attempted to perform '{action}' browser action."
        except Exception as e:
            logger.error(f"Error controlling browser tab: {e}")
            return f"Sorry, I couldn't perform the browser action '{action}'."

    # --- Media Playback Control ---

    async def control_media_playback(self, action: str) -> str:
        """Controls media playback (play, pause, stop, next, previous)."""
        try:
            if action == "play" or action == "pause" or action == "toggle":
                pyautogui.press('playpause')
            elif action == "stop":
                pyautogui.press('stop')
            elif action == "next":
                pyautogui.press('nexttrack')
            elif action == "previous":
                pyautogui.press('prevtrack')
            else:
                return f"Unsupported media action: {action}."
            return f"Attempted to {action} media playback."
        except Exception as e:
            logger.error(f"Error controlling media playback: {e}")
            return "Sorry, I couldn't control media playback."

    # --- Integrated Search / External Tools ---

    async def play_on_youtube(self, query: str) -> str:
        """Plays a video on YouTube based on the query."""
        try:
            wk.playonyt(query)
            # pyautogui.press('enter') # This press is often not reliable, better to just open
            return f"Playing '{query}' on YouTube."
        except Exception as e:
            logger.error(f"Error playing on YouTube: {e}")
            return "Sorry, I couldn't play that on YouTube."

    async def search_on_youtube(self, query: str) -> str:
        """Searches for a query on YouTube and opens the search results."""
        try:
            wk.search(query) # This opens default browser to Youtube results
            # pyautogui.press('enter') # This press is often not reliable
            return f"Searching for '{query}' on YouTube."
        except Exception as e:
            logger.error(f"Error searching on YouTube: {e}")
            return "Sorry, I couldn't search that on YouTube."

    async def search_on_google(self, query: str) -> str:
        """Performs a Google search and opens the browser to the search results."""
        try:
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            webbrowser.open(search_url)
            return f"Searching Google for {query}."
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            return "Sorry, I couldn't perform the Google search."

    async def wikipedia_search(self, query: str, sentences: int = 2) -> str:
        """Searches Wikipedia for a query and returns a summary."""
        try:
            summary = wikipedia.summary(query, sentences=sentences)
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            # Handle cases where query is ambiguous
            options = ", ".join(e.options[:5]) # Show up to 5 options
            return f"Ambiguous search query. Did you mean: {options}? Please refine your search."
        except wikipedia.exceptions.PageError:
            return "No information found on Wikipedia for that query. Please try again."
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return "Sorry, I couldn't perform the Wikipedia search."

    # --- System Features (Windows-specific, via PowerToys or similar hotkeys) ---
    async def open_system_feature(self, feature_name: str, search_query: str = None) -> str:
        """
        Opens a specific system feature, primarily designed for Windows PowerToys.
        Args:
            feature_name (str): The name of the feature (e.g., 'spotlight', 'text extractor', 'fancy zone', 'always on top').
            search_query (str): Optional query for features like 'spotlight'.
        """
        try:
            if platform.system() != "Windows":
                return f"System features are not implemented for {platform.system()}."

            feature_name_lower = feature_name.lower()
            if feature_name_lower == "spotlight" or feature_name_lower == "windows search":
                # Assuming PowerToys Run (Alt+Space) or Windows Search (Win+S)
                pyautogui.hotkey("alt", "space") # PowerToys Run
                # If you want Windows Search instead: pyautogui.hotkey("win", "s")
                time.sleep(1) # Give time for search bar to appear
                if search_query:
                    pyautogui.typewrite(search_query, interval=0.05)
                    pyautogui.press("enter")
                    return f"Opened {feature_name} and searched for '{search_query}'."
                return f"Opened {feature_name}."
            elif feature_name_lower == "text extractor":
                pyautogui.hotkey("win", "shift", "t")
                return f"Activated {feature_name}."
            elif feature_name_lower == "fancy zone" or feature_name_lower == "fancyzones":
                pyautogui.hotkey("win", "shift", "`") # Default PowerToys FancyZones Editor activation
                return f"Opened {feature_name}."
            elif feature_name_lower == "always on top":
                pyautogui.hotkey('win', 'ctrl', 't') # Default PowerToys Always On Top activation
                return f"Toggled {feature_name}."
            else:
                return f"Unknown system feature: {feature_name}."
        except Exception as e:
            logger.error(f"Error opening system feature {feature_name}: {e}")
            return f"Sorry, I couldn't open {feature_name}."

    # --- User Database Actions (if handled by actions class, otherwise by main app) ---
    # These are less "system actions" and more "app-specific data management"
    # but I'll include them here based on your previous code. You might move this
    # to a separate "UserManagement" or "Personalization" class later.

    async def initialize_user_database(self) -> str:
        """Initializes the SQLite database for user profiles."""
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS users
                              (name TEXT PRIMARY KEY, age INTEGER, sex TEXT, dob TEXT)''')
            conn.commit()
            conn.close()
            return "User database initialized successfully."
        except Exception as e:
            logger.error(f"Error initializing user database: {e}")
            return "Failed to initialize user database."

    async def add_user_to_database(self, name: str, age: int, sex: str, dob: str) -> str:
        """Adds a new user to the database."""
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, age, sex, dob) VALUES (?, ?, ?, ?)", (name, age, sex, dob))
            conn.commit()
            conn.close()
            return f"User '{name}' added to database."
        except sqlite3.IntegrityError:
            return f"User '{name}' already exists in the database."
        except Exception as e:
            logger.error(f"Error adding user to database: {e}")
            return "Failed to add user to database."

    async def check_user_in_database(self, name: str) -> dict or None:
        """Checks if a user exists in the database and returns their info."""
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, age, sex, dob FROM users WHERE name=?", (name,))
            user_data = cursor.fetchone()
            conn.close()
            if user_data:
                return {"name": user_data[0], "age": user_data[1], "sex": user_data[2], "dob": user_data[3]}
            return None
        except Exception as e:
            logger.error(f"Error checking user in database: {e}")
            return None

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
import calendar
import wikipedia
import pywhatkit as wk
import sqlite3
from typing import Optional
from typing import List, Tuple, Optional, Dict, Any, Callable # Added Callable

# This import assumes SystemActions is in the same 'Backend' directory
from Backend.SystemActions import SystemActions

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Keep LearningAssistant logs visible for debugging

class LearningAssistant:
    """
    This class acts as the bridge between recognized intents (from IntentRecognizer)
    and the actual system actions (from SystemActions).
    It manages the mapping and dynamic execution of actions.
    """
    def __init__(self):
        self.system_actions = SystemActions()
        self._setup_dispatcher()

    def _setup_dispatcher(self):
        """Map intents to action functions and define how they take arguments."""
        self.action_dispatcher = {
            # --- System Information ---
            "get_time": {"function": self.system_actions.get_current_time, "args": {}},
            "get_today_date": {"function": self.system_actions.get_today_date, "args": {}},
            "get_ip_address": {"function": self.system_actions.get_ip_address, "args": {}},
            "wikipedia_search": {"function": self.system_actions.wikipedia_search, "args": {"query": None}}, # Needs 'query'

            # --- Application Control (Open) ---
            "open_notepad": {"function": self.system_actions.open_application, "args": {"app_name": "notepad"}},
            "open_chrome": {"function": self.system_actions.open_application, "args": {"app_name": "chrome"}},
            "open_calculator": {"function": self.system_actions.open_application, "args": {"app_name": "calculator"}},
            "open_file_explorer": {"function": self.system_actions.open_application, "args": {"app_name": "file explorer"}},
            "open_calendar": {"function": self.system_actions.open_application, "args": {"app_name": "calendar"}},
            "open_control_panel": {"function": self.system_actions.open_application, "args": {"app_name": "control panel"}},
            "open_command_prompt": {"function": self.system_actions.open_application, "args": {"app_name": "command prompt"}},
            "open_power_settings": {"function": self.system_actions.open_application, "args": {"app_name": "power settings"}},
            "open_device_manager": {"function": self.system_actions.open_application, "args": {"app_name": "device manager"}},
            "open_system_properties": {"function": self.system_actions.open_application, "args": {"app_name": "system properties"}},
            "open_network_connections": {"function": self.system_actions.open_application, "args": {"app_name": "network connections"}},
            "open_firefox": {"function": self.system_actions.open_application, "args": {"app_name": "firefox"}},
            "open_edge": {"function": self.system_actions.open_application, "args": {"app_name": "msedge"}}, # Note: Edge's process name is msedge
            "open_opera": {"function": self.system_actions.open_application, "args": {"app_name": "opera"}},
            "open_media_player": {"function": self.system_actions.open_application, "args": {"app_name": "media player"}},
            "open_task_manager": {"function": self.system_actions.open_application, "args": {"app_name": "task manager"}},


            # --- Application Control (Close) ---
            "close_notepad": {"function": self.system_actions.close_application, "args": {"app_name": "notepad"}},
            "close_chrome": {"function": self.system_actions.close_application, "args": {"app_name": "chrome"}},
            "close_firefox": {"function": self.system_actions.close_application, "args": {"app_name": "firefox"}},
            "close_edge": {"function": self.system_actions.close_application, "args": {"app_name": "msedge"}},
            "close_opera": {"function": self.system_actions.close_application, "args": {"app_name": "opera"}},
            "close_media_player": {"function": self.system_actions.close_application, "args": {"app_name": "media player"}},
            "close_task_manager": {"function": self.system_actions.close_application, "args": {"app_name": "task manager"}},

            # --- System Control ---
            "shutdown_system": {"function": self.system_actions.shutdown_system, "args": {}},
            "restart_system": {"function": self.system_actions.restart_system, "args": {}},
            "sleep_system": {"function": self.system_actions.sleep_system, "args": {}},
            "hibernate_system": {"function": self.system_actions.hibernate_system, "args": {}},
            "lock_system": {"function": self.system_actions.lock_system, "args": {}},
            "take_screenshot": {"function": self.system_actions.take_screenshot, "args": {}},
            "minimize_all_windows": {"function": self.system_actions.minimize_all_windows, "args": {}},
            "maximize_window": {"function": self.system_actions.maximize_window, "args": {}},
            "minimize_window": {"function": self.system_actions.minimize_window, "args": {}},

            # --- Volume Control ---
            "adjust_volume_up": {"function": self.system_actions.adjust_volume, "args": {"direction": "up"}},
            "adjust_volume_down": {"function": self.system_actions.adjust_volume, "args": {"direction": "down"}},

            # --- Browser Control ---
            "browser_new_tab": {"function": self.system_actions.control_browser_tab, "args": {"action": "new"}},
            "browser_next_tab": {"function": self.system_actions.control_browser_tab, "args": {"action": "next"}},
            "browser_previous_tab": {"function": self.system_actions.control_browser_tab, "args": {"action": "previous"}},
            "browser_home_page": {"function": self.system_actions.control_browser_tab, "args": {"action": "home"}},
            "browser_close_tab": {"function": self.system_actions.control_browser_tab, "args": {"action": "close"}},
            "browser_close_window": {"function": self.system_actions.control_browser_tab, "args": {"action": "close_window"}},
            "browser_download_page": {"function": self.system_actions.control_browser_tab, "args": {"action": "download_page"}},
            "browser_address_bar": {"function": self.system_actions.control_browser_tab, "args": {"action": "address_bar"}},
            "browser_login_user": {"function": self.system_actions.control_browser_tab, "args": {"action": "login_to_different_user"}},

            # --- Media Playback Control ---
            "media_play": {"function": self.system_actions.control_media_playback, "args": {"action": "play"}},
            "media_pause": {"function": self.system_actions.control_media_playback, "args": {"action": "pause"}},
            "media_stop": {"function": self.system_actions.control_media_playback, "args": {"action": "stop"}},
            "media_next": {"function": self.system_actions.control_media_playback, "args": {"action": "next"}},
            "media_previous": {"function": self.system_actions.control_media_playback, "args": {"action": "previous"}},
            "media_toggle_play_pause": {"function": self.system_actions.control_media_playback, "args": {"action": "toggle"}},


            # --- Integrated Search / External Tools ---
            "play_on_youtube": {"function": self.system_actions.play_on_youtube, "args": {"query": None}}, # Needs 'query'
            "search_on_youtube": {"function": self.system_actions.search_on_youtube, "args": {"query": None}}, # Needs 'query'
            "search_on_google": {"function": self.system_actions.search_on_google, "args": {"query": None}}, # Needs 'query'

            # --- System Features (PowerToys) ---
            "open_spotlight": {"function": self.system_actions.open_system_feature, "args": {"feature_name": "spotlight", "search_query": None}}, # Can take optional search_query
            "open_text_extractor": {"function": self.system_actions.open_system_feature, "args": {"feature_name": "text extractor"}},
            "open_fancy_zone": {"function": self.system_actions.open_system_feature, "args": {"feature_name": "fancy zone"}},
            "toggle_always_on_top": {"function": self.system_actions.open_system_feature, "args": {"feature_name": "always on top"}},

            # --- User Database Actions ---
            "initialize_user_db": {"function": self.system_actions.initialize_user_database, "args": {}},
            "add_user_db": {"function": self.system_actions.add_user_to_database, "args": {"name": None, "age": None, "sex": None, "dob": None}}, # Needs args
            "check_user_db": {"function": self.system_actions.check_user_in_database, "args": {"name": None}}, # Needs args
        }

    def get_action_for_intent(self, intent_name: str, entity: Optional[str] = None) -> Tuple[Optional[callable], Dict[str, Any]]:
        """
        Retrieves the action function and its default arguments for a given intent.
        Dynamically populates arguments if an entity is provided.
        """
        action_info = self.action_dispatcher.get(intent_name)

        if not action_info:
            logger.warning(f"No action defined for intent: {intent_name}")
            return None, {}

        action_function = action_info["function"]
        # Create a mutable copy of the default arguments
        action_args = action_info["args"].copy()

        # Dynamically populate arguments based on intent and entity
        if intent_name == "wikipedia_search" and entity:
            action_args["query"] = entity
        elif intent_name == "play_on_youtube" and entity:
            action_args["query"] = entity
        elif intent_name == "search_on_youtube" and entity:
            action_args["query"] = entity
        elif intent_name == "search_on_google" and entity:
            action_args["query"] = entity
        elif intent_name == "open_spotlight" and entity: # If entity is a search query for spotlight
            action_args["search_query"] = entity


        logger.info(f"Resolved intent '{intent_name}' to function '{action_function.__name__}' with args: {action_args}")
        return action_function, action_args

# Example Usage (for testing LearningAssistant independently)
if __name__ == "__main__":
    assistant = LearningAssistant()

    print("\n--- Testing LearningAssistant Action Dispatch ---")

    # Test cases: (intent_name, entity)
    test_cases = [
        ("get_time", None),
        ("open_notepad", None),
        ("play_on_youtube", "latest despacito song"),
        ("wikipedia_search", "Mount Everest"),
        ("adjust_volume_up", None),
        ("non_existent_intent", None)
    ]

    for intent, entity in test_cases:
        print(f"\nRequesting action for intent: '{intent}' (Entity: {entity})")
        action_func, args = assistant.get_action_for_intent(intent, entity)

        if action_func:
            print(f"  -> Found Function: {action_func.__name__}")
            print(f"  -> Arguments: {args}")
            # Simulate execution (some might open apps/browsers)
            try:
                result = action_func(**args)
                print(f"  -> Action Result: {result}")
            except Exception as e:
                print(f"  -> Error executing action: {e}")
        else:
            print(f"  -> No action found for intent '{intent}'.")
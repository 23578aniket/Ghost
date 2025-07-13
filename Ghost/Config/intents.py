INTENT_CATEGORIES = {
    "greeting": {
        "type": "greeting",
        "actions": ["respond_to_greeting"],
        "responses": [
            "Hello! How can I help?",
            "Hi there!",
            "Greetings! What can I do for you?"
        ]
    },
    "general_query": {
        "type": "general",
        "actions": ["answer_general_question"],
        "responses": [
            "Let me think about that",
            "I can answer that",
            "Here's what I know"
        ]
    },
    "realtime_query": {
        "type": "realtime",
        "actions": ["search_online", "fetch_from_api"],
        "responses": [
            "Let me check that for you",
            "Searching for the latest information",
            "I'll find that online"
        ],
        "sources": {
            "weather": "weather_api",
            "news": "news_api",
            "sports": "sports_api"
        }
    },
    "task_execution": {
        "type": "task",
        "subcategories": {
            "media": {
                "actions": ["control_media"],
                "responses": ["Working on your media request"]
            },
            "system": {
                "actions": ["control_system"],
                "responses": ["Executing system command"]
            },
            "app": {
                "actions": ["manage_application"],
                "responses": ["Handling application request"]
            },
            "file": {
                "actions": ["manage_files"],
                "responses": ["Processing file operation"]
            }
        }
    }
}

# Example usage in your automation system:
# 1. First check intent_type to know which category it belongs to
# 2. Then use the specific intent to determine exact action
# 3. Finally use extracted entity if available
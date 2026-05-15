"""
config.py
Contains configuration settings, API URL, and constant lists for the dashboard.
"""

# OpenRouter Base API URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Free models available on OpenRouter (common examples)
FREE_MODELS = [
    "google/gemma-7b-it:free",
    "mistralai/mistral-7b-instruct:free",
    "openchat/openchat-7b:free",
    "nousresearch/nous-capybara-7b:free",
    "huggingfaceh4/zephyr-7b-beta:free",
]

# Popular paid models available on OpenRouter
PAID_MODELS = [
    "openai/gpt-4-turbo",
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    "google/gemini-pro-1.5",
    "meta-llama/llama-3-70b-instruct",
    "mistralai/mixtral-8x7b-instruct",
]

# Task categories for prompt generation
TASK_CATEGORIES = [
    "General Chat",
    "Coding & Logic",
    "Creative Writing",
    "Data Extraction",
    "Summarization",
    "Translation"
]

# Streamlit Page Configuration
PAGE_CONFIG = {
    "page_title": "AI Model Explorer & Benchmark",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

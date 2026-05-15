"""
utils/helpers.py
Utility functions that don't involve API calls.
"""
import pandas as pd

def format_pricing(price_per_token: float) -> str:
    """Formats the token pricing into a readable format (e.g. per 1M tokens)"""
    if price_per_token == 0:
        return "Free"
    
    # Calculate price per 1 million tokens
    price_per_million = price_per_token * 1_000_000
    return f"${price_per_million:.2f} / 1M tokens"

def format_price(price_per_million: float) -> str:
    """Formats the per-million token pricing into a readable format"""
    if pd.isna(price_per_million) or price_per_million == 0:
        return "Free"
    return f"${price_per_million:.2f} / 1M tokens"

def categorize_provider(model_id: str) -> str:
    """Returns provider name by parsing model_id
    e.g. "openai/gpt-4o" -> "OpenAI"
    """
    if pd.isna(model_id):
        return "Other"
        
    model_id_lower = str(model_id).lower()
    
    if "openai" in model_id_lower:
        return "OpenAI"
    elif "anthropic" in model_id_lower:
        return "Anthropic"
    elif "google" in model_id_lower:
        return "Google"
    elif "meta-llama" in model_id_lower or "llama" in model_id_lower:
        return "Meta"
    elif "mistralai" in model_id_lower or "mistral" in model_id_lower:
        return "Mistral"
    elif "qwen" in model_id_lower:
        return "Alibaba/Qwen"
    else:
        # Fallback to extracting the prefix before the slash if present
        if "/" in model_id:
            return model_id.split("/")[0].capitalize()
        return "Other"

def get_context_tier(context_length: int) -> str:
    """Categorizes context length into easy-to-understand tiers"""
    if pd.isna(context_length) or context_length <= 0:
        return "Unknown"
    
    if context_length < 8000:
        return "Small (<8K)"
    elif context_length < 32000:
        return "Medium (8K-32K)"
    elif context_length < 128000:
        return "Large (32K-128K)"
    else:
        return "Ultra (128K+)"

def get_speed_tier(model_id: str) -> str:
    """Estimates speed tier based on model name heuristics"""
    if pd.isna(model_id):
        return "Medium 🚀"
        
    model_id_lower = str(model_id).lower()
    
    # Fast heuristics
    fast_keywords = ["turbo", "flash", "haiku", "mini", "instant", "8b", "7b", "quant"]
    # Slow heuristics
    slow_keywords = ["opus", "ultra", "large", "72b", "405b", "70b"]
    
    for kw in fast_keywords:
        if kw in model_id_lower:
            return "Fast ⚡"
            
    for kw in slow_keywords:
        if kw in model_id_lower:
            return "Slow 🐢"
            
    return "Medium 🚀"

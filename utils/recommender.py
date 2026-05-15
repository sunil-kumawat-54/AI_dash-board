import pandas as pd

def recommend_model(task_type: str, priority: str, budget: str) -> list:
    """
    Returns top 3 recommended models based on priority, budget, and task.
    priority: "Speed", "Quality", "Cost", "Balanced"
    budget: "Free Only", "Under $0.01", "Any Budget"
    """
    # Base dictionary of some known models with estimated stats
    models_db = [
        {"id": "google/gemma-2-9b-it:free", "name": "Gemma 2 9B IT (Free)", "provider": "Google", "speed": 9, "quality": 6, "cost": 0, "traits": ["fast", "free"]},
        {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B Instruct (Free)", "provider": "Mistral", "speed": 9, "quality": 6, "cost": 0, "traits": ["fast", "free"]},
        {"id": "meta-llama/llama-3.1-8b-instruct:free", "name": "Llama 3.1 8B Instruct (Free)", "provider": "Meta", "speed": 8, "quality": 7, "cost": 0, "traits": ["fast", "free"]},
        {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "OpenAI", "speed": 7, "quality": 10, "cost": 0.005, "traits": ["quality", "creative", "code"]},
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "Anthropic", "speed": 8, "quality": 10, "cost": 0.003, "traits": ["quality", "creative", "code"]},
        {"id": "deepseek/deepseek-coder", "name": "DeepSeek Coder", "provider": "DeepSeek", "speed": 7, "quality": 8, "cost": 0.0005, "traits": ["code", "cost-efficient"]},
        {"id": "qwen/qwen-2.5-72b-instruct", "name": "Qwen 2.5 72B Instruct", "provider": "Alibaba", "speed": 6, "quality": 9, "cost": 0.0008, "traits": ["cost-efficient", "quality"]},
        {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI", "speed": 10, "quality": 8, "cost": 0.00015, "traits": ["fast", "cost-efficient", "balanced"]},
        {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "provider": "Anthropic", "speed": 10, "quality": 8, "cost": 0.00025, "traits": ["fast", "cost-efficient", "balanced"]},
    ]
    
    filtered = []
    for m in models_db:
        # Budget filter
        if budget == "Free Only" and m["cost"] > 0:
            continue
        if budget == "Under $0.01" and m["cost"] >= 0.01:
            continue
            
        score = 0
        reasoning = []
        
        # Priority scoring
        if priority == "Speed":
            score += m["speed"] * 2
            if "fast" in m["traits"]: reasoning.append("Excellent speed.")
        elif priority == "Quality":
            score += m["quality"] * 2
            if "quality" in m["traits"]: reasoning.append("Top-tier reasoning.")
        elif priority == "Cost":
            score += (10 - min(m["cost"]*1000, 10)) * 2
            if "cost-efficient" in m["traits"] or m["cost"] == 0: reasoning.append("Highly cost-effective.")
        else: # Balanced
            score += m["speed"] + m["quality"] + (10 - min(m["cost"]*1000, 10))
            if "balanced" in m["traits"]: reasoning.append("Great balance of speed, cost, and quality.")
            
        # Task scoring
        task_lower = task_type.lower()
        if "code" in task_lower and "code" in m["traits"]:
            score += 5
            reasoning.append("Strong coding capabilities.")
        if "creative" in task_lower and "creative" in m["traits"]:
            score += 5
            reasoning.append("Excellent at creative tasks.")
            
        if not reasoning:
            reasoning.append("Solid overall choice.")
            
        filtered.append({
            "id": m["id"],
            "name": m["name"],
            "provider": m["provider"],
            "cost": m["cost"],
            "score": score,
            "reasoning": " ".join(reasoning)
        })
        
    # Sort by score desc and return top 3
    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered[:3]

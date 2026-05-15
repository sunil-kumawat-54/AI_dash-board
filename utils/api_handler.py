"""
utils/api_handler.py
Handles all interactions with the OpenRouter API.
"""
import requests
import pandas as pd
import streamlit as st
import time
import concurrent.futures
from config import OPENROUTER_BASE_URL

@st.cache_data(ttl=3600, show_spinner=False) # Cache for 1 hour to prevent redundant API calls
def fetch_all_models(api_key: str) -> pd.DataFrame:
    """
    Fetches the live list of models from OpenRouter API.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8501", 
        "X-Title": "AI Model Explorer Dashboard" 
    }
    
    url = f"{OPENROUTER_BASE_URL}/models"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        
        data = response.json()
        models = data.get("data", [])
        
        if not models:
            return pd.DataFrame()
            
        clean_models = []
        for m in models:
            pricing = m.get("pricing", {})
            prompt_price = float(pricing.get("prompt", 0))
            completion_price = float(pricing.get("completion", 0))
            is_free = (prompt_price == 0 and completion_price == 0)
            model_id = m.get("id", "")
            
            clean_models.append({
                "id": model_id,
                "name": m.get("name", model_id),
                "pricing_prompt": prompt_price,
                "pricing_completion": completion_price,
                "context_length": m.get("context_length", 0),
                "is_free": is_free
            })
            
        df = pd.DataFrame(clean_models)
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching models from OpenRouter: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

def query_single_model(api_key: str, model_id: str, prompt: str, models_df: pd.DataFrame, system_prompt: str = "You are a helpful assistant") -> dict:
    """
    Sends a chat completion request to a single OpenRouter model and tracks metrics.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "AI Model Benchmark"
    }
    
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000
    }
    
    result = {
        "model_id": model_id,
        "response_text": "",
        "response_time_ms": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "total_cost": 0.0,
        "error": None
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        end_time = time.time()
        result["response_time_ms"] = (end_time - start_time) * 1000
        
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            result["response_text"] = data["choices"][0]["message"]["content"]
            
        usage = data.get("usage", {})
        result["prompt_tokens"] = usage.get("prompt_tokens", 0)
        result["completion_tokens"] = usage.get("completion_tokens", 0)
        result["total_tokens"] = usage.get("total_tokens", 0)
        
        model_data = models_df[models_df["id"] == model_id]
        if not model_data.empty:
            # We calculate cost based on the per-token price fetched earlier
            price_prompt = model_data.iloc[0]["pricing_prompt"]
            price_completion = model_data.iloc[0]["pricing_completion"]
            
            result["input_cost"] = result["prompt_tokens"] * price_prompt
            result["output_cost"] = result["completion_tokens"] * price_completion
            result["total_cost"] = result["input_cost"] + result["output_cost"]
            
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        result["response_time_ms"] = (end_time - start_time) * 1000
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(e))
        except Exception:
            error_msg = str(e)
        result["error"] = f"API Error: {error_msg}"
        
    except Exception as e:
        end_time = time.time()
        result["response_time_ms"] = (end_time - start_time) * 1000
        result["error"] = f"Unexpected Error: {str(e)}"
        
    return result

def query_all_models(api_key: str, selected_model_ids: list, prompt: str, models_df: pd.DataFrame, system_prompt: str = "You are a helpful assistant") -> list:
    """
    Executes multiple model queries in parallel using ThreadPoolExecutor.
    """
    results = []
    
    status = st.status("Querying models...", expanded=True)
    progress_bar = status.progress(0)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_model = {
            executor.submit(query_single_model, api_key, m_id, prompt, models_df, system_prompt): m_id
            for m_id in selected_model_ids
        }
        
        completed = 0
        total = len(selected_model_ids)
        
        for future in concurrent.futures.as_completed(future_to_model):
            m_id = future_to_model[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                results.append({
                    "model_id": m_id,
                    "response_text": "",
                    "response_time_ms": 0.0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "input_cost": 0.0,
                    "output_cost": 0.0,
                    "total_cost": 0.0,
                    "error": f"Thread exception: {exc}"
                })
                
            completed += 1
            progress_bar.progress(completed / total, text=f"Completed {completed}/{total} models")
            status.write(f"✅ Received response from {m_id}")
            
    status.update(label="All queries finished!", state="complete", expanded=False)
    
    # Return sorted by response time ascending
    results.sort(key=lambda x: x["response_time_ms"])
    
    return results

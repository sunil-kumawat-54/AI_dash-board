import json
import os
import pandas as pd
from datetime import datetime

LEADERBOARD_FILE = "leaderboard.json"

def update_leaderboard(results_df: pd.DataFrame, task_name: str):
    leaderboard = []
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                leaderboard = json.load(f)
        except json.JSONDecodeError:
            pass

    timestamp = datetime.now().isoformat()
    
    for _, row in results_df.iterrows():
        if pd.isna(row.get("error")) or row.get("error") == "":
            entry = {
                "model_id": row["model_id"],
                "task_name": task_name,
                "score": float(row.get("benchmark_score", 0)),
                "response_time_ms": float(row.get("response_time_ms", 0)),
                "total_cost": float(row.get("total_cost", 0)),
                "timestamp": timestamp
            }
            leaderboard.append(entry)
            
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=2)

def get_leaderboard_df() -> pd.DataFrame:
    if not os.path.exists(LEADERBOARD_FILE):
        return pd.DataFrame()
        
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            leaderboard = json.load(f)
    except json.JSONDecodeError:
        return pd.DataFrame()
        
    if not leaderboard:
        return pd.DataFrame()
        
    df = pd.DataFrame(leaderboard)
    
    # Group by model_id
    grouped = df.groupby("model_id").agg(
        avg_score=("score", "mean"),
        avg_time=("response_time_ms", "mean"),
        avg_cost=("total_cost", "mean"),
        run_count=("model_id", "count")
    ).reset_index()
    
    grouped.sort_values(by="avg_score", ascending=False, inplace=True)
    return grouped

"""
utils/scoring.py
Logic for calculating benchmark scores, ranks, and value tiers.
"""
import pandas as pd
import numpy as np

def calculate_scores(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates benchmark scores for the models based on speed, cost, and response length.
    Adds benchmark_score, rank, and value_tier to the dataframe.
    """
    df = results_df.copy()
    
    # Helper to min-max normalize a series to 0-1
    def normalize(series):
        if series.max() == series.min():
            return np.ones(len(series))
        return (series - series.min()) / (series.max() - series.min() + 1e-9)
        
    # Valid results only for scoring (no errors)
    valid_mask = df["error"].isna() | (df["error"] == "")
    
    df["benchmark_score"] = 0.0
    df["rank"] = 0
    df["value_tier"] = "N/A"
    df["resp_len"] = df["response_text"].apply(lambda x: len(str(x)))
    
    if valid_mask.sum() == 0:
        return df
        
    # Speed score: 1 / response_time_ms (Faster is better)
    speed_inv = 1 / df.loc[valid_mask, "response_time_ms"].replace(0, np.nan).fillna(1)
    speed_score = normalize(speed_inv) * 30
    
    # Cost score: 1 / (total_cost + 0.000001) (Cheaper is better)
    cost_inv = 1 / (df.loc[valid_mask, "total_cost"] + 0.000001)
    cost_score = normalize(cost_inv) * 30
    
    # Length score: len(response_text) (Longer is considered more thorough)
    length_score = normalize(df.loc[valid_mask, "resp_len"]) * 20
    
    # Value score: blend of speed and cost
    value_score = speed_score * 0.5 + cost_score * 0.5
    
    # Total score (out of 100 max depending on overlap)
    total_score = speed_score + cost_score + length_score + value_score
    
    df.loc[valid_mask, "benchmark_score"] = total_score.round(1)
    
    # Ranks (1 = best)
    df.loc[valid_mask, "rank"] = df.loc[valid_mask, "benchmark_score"].rank(ascending=False, method="min").astype(int)
    
    # Value tiers
    def get_tier(score):
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
            
    df.loc[valid_mask, "value_tier"] = df.loc[valid_mask, "benchmark_score"].apply(get_tier)
    
    return df

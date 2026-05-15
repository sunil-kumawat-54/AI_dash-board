"""
utils/visualizations.py
Functions to generate Plotly charts for the performance dashboard.
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def _apply_common_layout(fig, title):
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#888888"),
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False
    )
    return fig

def make_response_time_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    
    sorted_df = df.sort_values(by="response_time_ms", ascending=False)
    
    times = sorted_df["response_time_ms"].values
    if len(times) > 0 and times.max() > times.min():
        norm_times = (times - times.min()) / (times.max() - times.min() + 1e-9)
        # teal to coral: rgb(0, 206, 209) to rgb(255, 127, 80)
        colors = [f"rgba({int(0 + 255*t)}, {int(206 - 79*t)}, {int(209 - 129*t)}, 0.8)" for t in norm_times]
    else:
        colors = ["rgba(0, 206, 209, 0.8)"] * len(times)
        
    text_labels = [f"{t/1000:.2f}s" for t in times]
    
    fig.add_trace(go.Bar(
        x=sorted_df["response_time_ms"],
        y=sorted_df["model_name_short"],
        orientation='h',
        marker_color=colors,
        text=text_labels,
        textposition="inside",
        insidetextanchor="end"
    ))
    
    fig.update_xaxes(title="Response Time (ms)", gridcolor="rgba(128,128,128,0.2)")
    fig.update_yaxes(title="")
    return _apply_common_layout(fig, "Response Time by Model")

def make_token_usage_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df["model_name_short"],
        y=df["prompt_tokens"],
        name="Prompt Tokens",
        marker_color="rgba(65, 105, 225, 0.8)" # Blue
    ))
    
    fig.add_trace(go.Bar(
        x=df["model_name_short"],
        y=df["completion_tokens"],
        name="Completion Tokens",
        marker_color="rgba(138, 43, 226, 0.8)", # Purple
        text=[f"Total: {t}" for t in df["total_tokens"]],
        textposition="outside"
    ))
    
    fig.update_layout(barmode='group', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Tokens", gridcolor="rgba(128,128,128,0.2)")
    
    fig.update_layout(
        title="Token Usage Breakdown",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#888888"),
        height=350,
        margin=dict(l=10, r=10, t=60, b=10)
    )
    return fig

def make_cost_comparison_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    
    costs = df["total_cost"].values
    colors = []
    for c in costs:
        if c == 0:
            colors.append("rgba(46, 125, 50, 0.8)") # Green
        elif c < 0.001:
            colors.append("rgba(255, 193, 7, 0.8)") # Amber
        else:
            colors.append("rgba(255, 127, 80, 0.8)") # Coral
            
    text_labels = [f"${c:.4f}" if c > 0 else "Free" for c in costs]
    
    fig.add_trace(go.Bar(
        x=df["model_name_short"],
        y=costs,
        marker_color=colors,
        text=text_labels,
        textposition="outside"
    ))
    
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Cost ($)", gridcolor="rgba(128,128,128,0.2)")
    fig.update_layout(cliponaxis=False)
    
    return _apply_common_layout(fig, "Cost Per Query")

def make_cost_vs_speed_scatter(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    
    valid_df = df[df["total_tokens"] > 0].copy()
    if valid_df.empty:
        return _apply_common_layout(fig, "Cost vs Speed Tradeoff")
        
    x = valid_df["response_time_ms"]
    y = valid_df["total_cost"]
    sizes = valid_df["total_tokens"].fillna(0).values
    
    if len(sizes) > 0 and sizes.max() > sizes.min():
        scaled_sizes = 10 + 20 * (sizes - sizes.min()) / (sizes.max() - sizes.min() + 1e-9)
    else:
        scaled_sizes = [20] * len(sizes)
        
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        marker=dict(
            size=scaled_sizes,
            color="rgba(30, 144, 255, 0.7)", 
            line=dict(width=1, color="rgba(255,255,255,0.5)")
        ),
        text=valid_df["model_name_short"],
        textposition="top center",
        textfont=dict(color="#aaaaaa", size=10)
    ))
    
    if len(x) > 1:
        med_x = x.median()
        med_y = y.median()
        
        fig.add_vline(x=med_x, line_dash="dash", line_color="rgba(128,128,128,0.5)")
        fig.add_hline(y=med_y, line_dash="dash", line_color="rgba(128,128,128,0.5)")
        
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        
        offset_x = (x_max - x_min) * 0.1
        offset_y = (y_max - y_min) * 0.1
        
        if x_max > x_min and y_max > y_min:
            annotations = [
                dict(x=med_x - offset_x, y=med_y - offset_y, text="Best Value", showarrow=False, font=dict(color="rgba(46, 125, 50, 0.8)")),
                dict(x=med_x - offset_x, y=med_y + offset_y, text="Fast but Pricey", showarrow=False, font=dict(color="rgba(255, 193, 7, 0.8)")),
                dict(x=med_x + offset_x, y=med_y - offset_y, text="Slow but Cheap", showarrow=False, font=dict(color="rgba(30, 144, 255, 0.8)")),
                dict(x=med_x + offset_x, y=med_y + offset_y, text="Avoid", showarrow=False, font=dict(color="rgba(255, 127, 80, 0.8)"))
            ]
            fig.update_layout(annotations=annotations)

    fig.update_xaxes(title="Response Time (ms)", gridcolor="rgba(128,128,128,0.2)")
    fig.update_yaxes(title="Cost ($)", gridcolor="rgba(128,128,128,0.2)")
    
    return _apply_common_layout(fig, "Cost vs Speed Tradeoff")

def make_response_length_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    
    sorted_df = df.sort_values(by="resp_len", ascending=True)
    
    fig.add_trace(go.Bar(
        x=sorted_df["resp_len"],
        y=sorted_df["model_name_short"],
        orientation='h',
        marker_color="rgba(72, 209, 204, 0.8)", # Medium Turquoise
        text=sorted_df["resp_len"],
        textposition="inside",
        insidetextanchor="end"
    ))
    
    fig.update_xaxes(title="Characters", gridcolor="rgba(128,128,128,0.2)")
    fig.update_yaxes(title="")
    return _apply_common_layout(fig, "Response Length (characters)")

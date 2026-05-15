import io
import pandas as pd
from fpdf import FPDF
from datetime import datetime

def export_to_csv(results_df: pd.DataFrame, task_name: str) -> io.BytesIO:
    buffer = io.BytesIO()
    # Add task name and date info implicitly through the filename later, just save csv
    results_df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

def export_to_pdf(results_df: pd.DataFrame, task_name: str, charts_dict: dict = None) -> io.BytesIO:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page 1
    pdf.add_page()
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "AI Benchmark Report", border=0, ln=1, align="C", fill=True)
    
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
    pdf.cell(0, 10, f"Task: {task_name}", ln=1)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Summary Table", ln=1)
    pdf.set_font("Helvetica", "B", 10)
    
    # Table header
    cols = ["Rank", "Model", "Score", "Time (ms)", "Cost ($)"]
    col_widths = [20, 80, 25, 30, 35]
    pdf.set_fill_color(200, 220, 255)
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 10, col, border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 10)
    valid_df = results_df[results_df["error"].isna() | (results_df["error"] == "")].copy()
    if "rank" in valid_df.columns:
        valid_df = valid_df.sort_values(by="rank")
        
    alt = False
    for _, row in valid_df.iterrows():
        pdf.set_fill_color(245, 245, 245) if alt else pdf.set_fill_color(255, 255, 255)
        alt = not alt
        pdf.cell(col_widths[0], 10, str(row.get("rank", "-")), border=1, fill=True)
        # Handle long model names
        m_name = str(row.get("model_name_short", row.get("model_id", "")))[:25]
        pdf.cell(col_widths[1], 10, m_name, border=1, fill=True)
        pdf.cell(col_widths[2], 10, f"{row.get('benchmark_score', 0):.1f}", border=1, fill=True)
        pdf.cell(col_widths[3], 10, f"{row.get('response_time_ms', 0):.0f}", border=1, fill=True)
        pdf.cell(col_widths[4], 10, f"${row.get('total_cost', 0):.5f}", border=1, fill=True)
        pdf.ln()
        
    # Page 2
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Metrics & Leaderboard", ln=1)
    pdf.set_font("Helvetica", "", 12)
    
    if not valid_df.empty:
        fastest = valid_df.loc[valid_df['response_time_ms'].idxmin()]
        cheapest = valid_df.loc[valid_df['total_cost'].idxmin()]
        best = valid_df.loc[valid_df['benchmark_score'].idxmax()]
        
        pdf.cell(0, 10, f"- Fastest Model: {fastest.get('model_name_short', fastest['model_id'])} ({fastest['response_time_ms']:.0f}ms)", ln=1)
        cost_str = "FREE" if cheapest['total_cost'] == 0 else f"${cheapest['total_cost']:.5f}"
        pdf.cell(0, 10, f"- Cheapest Model: {cheapest.get('model_name_short', cheapest['model_id'])} ({cost_str})", ln=1)
        pdf.cell(0, 10, f"- Highest Score: {best.get('model_name_short', best['model_id'])} ({best.get('benchmark_score', 0):.1f}/100)", ln=1)
        pdf.cell(0, 10, f"- Total Cost of Run: ${valid_df['total_cost'].sum():.5f}", ln=1)
        
    # Page 3
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Model Responses", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    
    for _, row in valid_df.iterrows():
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, str(row.get("model_name", row["model_id"])), ln=1)
        pdf.set_font("Helvetica", "", 10)
        
        resp = str(row.get("response_text", ""))
        # Clean special chars that FPDF might not like
        resp = resp.encode('latin-1', 'replace').decode('latin-1')
        if len(resp) > 300:
            resp = resp[:297] + "..."
        pdf.multi_cell(0, 6, resp)
        pdf.ln(5)

    # Return bytes
    buffer = io.BytesIO(pdf.output(dest="S"))
    buffer.seek(0)
    return buffer

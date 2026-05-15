"""
app.py
Main Streamlit application file.
"""
import streamlit as st
import pandas as pd
import datetime
from config import PAGE_CONFIG
from utils.api_handler import fetch_all_models, query_all_models
from utils.helpers import categorize_provider, get_context_tier, get_speed_tier, format_price
from utils.task_templates import TASKS
from utils.scoring import calculate_scores
from utils.visualizations import (
    make_response_time_chart, 
    make_token_usage_chart, 
    make_cost_comparison_chart, 
    make_cost_vs_speed_scatter, 
    make_response_length_chart
)
from utils.leaderboard import update_leaderboard, get_leaderboard_df
from utils.exporter import export_to_csv, export_to_pdf
from utils.recommender import recommend_model
import plotly.express as px

# 1. Set Page Configuration (Must be the first Streamlit command)
st.set_page_config(**PAGE_CONFIG)

# Custom CSS for UI enhancements
st.markdown("""
<style>
    .free-badge {
        background-color: #2e7d32;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .paid-badge {
        background-color: #ef6c00;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .response-box {
        background-color: rgba(128,128,128,0.1);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(128,128,128,0.2);
        height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# 2. Initialize Session State Variables
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "models_df" not in st.session_state:
    st.session_state.models_df = pd.DataFrame()
if "selected_models" not in st.session_state:
    st.session_state.selected_models = []
if "results" not in st.session_state:
    st.session_state.results = []
if "timestamp" not in st.session_state:
    st.session_state.timestamp = None
if "run_history" not in st.session_state:
    st.session_state.run_history = []

# 3. Sidebar Configuration
with st.sidebar:
    st.title("⚙️ Settings")
    
    st.subheader("OpenRouter Configuration")
    api_key_input = st.text_input(
        "Enter your OpenRouter API Key:", 
        type="password", 
        value=st.session_state.api_key,
        help="Get your key at https://openrouter.ai/keys"
    )
    st.session_state.api_key = api_key_input
    
    if st.button("Connect to OpenRouter", use_container_width=True):
        if not st.session_state.api_key:
            st.warning("Please enter an API key first.")
        else:
            with st.spinner("Connecting and fetching models..."):
                df = fetch_all_models(st.session_state.api_key)
                if not df.empty:
                    df['Provider'] = df['id'].apply(categorize_provider)
                    df['Context_Tier'] = df['context_length'].apply(get_context_tier)
                    df['Speed_Tier'] = df['id'].apply(get_speed_tier)
                    df['Price_1M_Prompt'] = df['pricing_prompt'] * 1000000
                    df['Price_1M_Completion'] = df['pricing_completion'] * 1000000
                    
                    st.session_state.models_df = df
                    st.success(f"Successfully connected! Fetched {len(df)} models.")
                else:
                    st.error("Failed to fetch models. Please check your API key.")

    st.markdown("---")

    # SIDEBAR SECTION A - Model Filters
    if not st.session_state.models_df.empty:
        st.header("🔍 Find Models")
        filtered_df = st.session_state.models_df.copy()
        
        search_query = st.text_input("Search by Name or Provider:", "").lower()
        if search_query:
            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(search_query) | 
                filtered_df['Provider'].str.lower().str.contains(search_query)
            ]
            
        pricing_filter = st.radio("Pricing Options", ["All Models", "Free Only 🆓", "Paid Only 💰"], horizontal=True)
        if pricing_filter == "Free Only 🆓":
            filtered_df = filtered_df[filtered_df['is_free']]
        elif pricing_filter == "Paid Only 💰":
            filtered_df = filtered_df[~filtered_df['is_free']]
            
        all_providers = sorted(st.session_state.models_df['Provider'].unique().tolist())
        selected_providers = st.multiselect("Filter by Provider", options=all_providers)
        if selected_providers:
            filtered_df = filtered_df[filtered_df['Provider'].isin(selected_providers)]
            
        max_context = int(st.session_state.models_df['context_length'].max())
        if pd.isna(max_context) or max_context < 4096:
            max_context = 1000000 
            
        min_context = st.slider("Minimum Context Length (Tokens)", 4096, max_context if max_context > 4096 else 128000, 4096, 4096)
        filtered_df = filtered_df[filtered_df['context_length'] >= min_context]
        
        st.markdown(f"**Showing {len(filtered_df)} of {len(st.session_state.models_df)} models**")
        st.markdown("---")
        
        # SIDEBAR SECTION B - Filtered Model Table
        st.subheader("📋 Filtered Models Table")
        
        display_df = filtered_df[['name', 'Provider', 'context_length', 'Price_1M_Prompt', 'Price_1M_Completion', 'is_free']].copy()
        display_df.rename(columns={
            'name': 'Model Name', 'context_length': 'Context', 'Price_1M_Prompt': 'Input Price',
            'Price_1M_Completion': 'Output Price', 'is_free': 'Free/Paid'
        }, inplace=True)
        display_df['Free/Paid'] = display_df['Free/Paid'].apply(lambda x: "Free" if x else "Paid")
        
        def highlight_free_rows(row):
            if row['Free/Paid'] == "Free":
                return ['background-color: rgba(46, 125, 50, 0.2)'] * len(row)
            return [''] * len(row)
            
        st.dataframe(display_df.style.apply(highlight_free_rows, axis=1), use_container_width=True, hide_index=True)
        st.markdown("---")
        
        # SIDEBAR SECTION C - Model Selection
        st.subheader("⚖️ Compare Models")
        model_options = filtered_df['id'].tolist()
        
        def format_model_id(m_id):
            matches = st.session_state.models_df[st.session_state.models_df['id'] == m_id]['name']
            return matches.values[0] if not matches.empty else m_id
            
        selected = st.multiselect(
            "Select models to compare (max 5)", options=model_options,
            default=[m for m in st.session_state.selected_models if m in model_options],
            format_func=format_model_id, max_selections=5
        )
        st.session_state.selected_models = selected
        
        if len(selected) > 5:
            st.warning("⚠️ You can only select up to 5 models for comparison.")
            
        if selected:
            for m_id in selected:
                model_data = st.session_state.models_df[st.session_state.models_df['id'] == m_id].iloc[0]
                with st.container():
                    st.markdown(f"**{model_data['name']}**")
                    badge_html = "<span class='free-badge'>Free</span>" if model_data['is_free'] else "<span class='paid-badge'>Paid</span>"
                    st.markdown(f"Provider: {model_data['Provider']} &nbsp; {badge_html}", unsafe_allow_html=True)
                    st.markdown(f"Context: {model_data['Context_Tier']} ({int(model_data['context_length']):,})")
                    st.markdown(f"Speed: {model_data['Speed_Tier']}")
                    st.markdown(f"Input: {format_price(model_data['Price_1M_Prompt'])} | Output: {format_price(model_data['Price_1M_Completion'])}")
                    st.divider()
                    
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div style='text-align: center; color: #888;'>✨ Built with Streamlit & OpenRouter</div>", unsafe_allow_html=True)

# 4. Main Area Configuration
st.title("🤖 AI Model Explorer & Benchmark Dashboard")
st.markdown("### Compare, test, and benchmark various LLMs through OpenRouter")

main_tabs = st.tabs(["🔬 Benchmark", "🏆 Leaderboard", "🤖 AI Recommender", "📊 Run History"])

with main_tabs[0]:
    if st.session_state.models_df.empty:
        st.info("👋 Welcome! Please connect your OpenRouter API key in the sidebar to begin exploring models.")
    else:
        if not st.session_state.selected_models:
            st.info("👆 **Select models from the sidebar to begin**", icon="ℹ️")
        
            st.markdown("#### Overview of All Models")
            overview_df = st.session_state.models_df[['name', 'Provider', 'Context_Tier', 'Speed_Tier', 'is_free']].copy()
            overview_df['is_free'] = overview_df['is_free'].apply(lambda x: "Free" if x else "Paid")
            st.dataframe(overview_df, use_container_width=True, hide_index=True)
        
        else:
            # Show comparison preview cards
            st.markdown("### 📊 Selected Models")
            cols = st.columns(len(st.session_state.selected_models))
            for i, m_id in enumerate(st.session_state.selected_models):
                model_data = st.session_state.models_df[st.session_state.models_df['id'] == m_id].iloc[0]
                with cols[i]:
                    st.markdown(f"#### {model_data['name']}")
                    badge = "🟢 Free" if model_data['is_free'] else "🟠 Paid"
                    st.markdown(f"**{badge}** | {model_data['Provider']}")
                    st.metric("Context Size", f"{int(model_data['context_length']):,}")
                
            st.markdown("---")
        
            # TASK CONFIGURATION PANEL
            st.header("🎯 Task Configuration")
        
            task_names = list(TASKS.keys())
            selected_task_name = st.selectbox("Choose Task Type", options=task_names)
            task_info = TASKS[selected_task_name]
        
            st.markdown(f"*{task_info['description']}*")
        
            tab1, tab2 = st.tabs(["Use Example Prompt", "Write Custom Prompt"])
            with tab1:
                example_prompt = st.text_area("Example Input (editable):", value=task_info['example_input'], height=150)
            with tab2:
                custom_prompt = st.text_area("Custom Input:", placeholder="Type your own prompt here...", height=150)
            
            active_prompt = custom_prompt if custom_prompt.strip() else example_prompt
            system_prompt = task_info['system_prompt']
        
            # RUN BUTTON
            st.markdown("<br>", unsafe_allow_html=True)
            num_models = len(st.session_state.selected_models)
            run_btn = st.button(f"🚀 Run Benchmark on {num_models} Model{'s' if num_models > 1 else ''}", type="primary", use_container_width=True)
        
            if run_btn:
                if not active_prompt.strip():
                    st.error("Please enter a prompt before running the benchmark.")
                else:
                    import random
                    msgs = ["🤖 Querying the AI hive mind...", "⚡ Racing the models...", "🧠 Comparing intelligences..."]
                    with st.spinner(random.choice(msgs)):
                        st.session_state.results = query_all_models(
                            api_key=st.session_state.api_key,
                            selected_model_ids=st.session_state.selected_models,
                            prompt=active_prompt,
                            models_df=st.session_state.models_df,
                            system_prompt=system_prompt
                        )
                    st.session_state.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Also pre-process immediately so we can save to history
                    res_df = pd.DataFrame(st.session_state.results)
                    res_df['model_name'] = res_df['model_id'].apply(
                        lambda x: st.session_state.models_df[st.session_state.models_df['id'] == x]['name'].values[0] 
                        if not st.session_state.models_df[st.session_state.models_df['id'] == x].empty else x
                    )
                    res_df['Provider'] = res_df['model_id'].apply(categorize_provider)
                    res_df['model_name_short'] = res_df['model_name'].apply(lambda x: x[:20] + "..." if len(x) > 20 else x)
                    scored_df_tmp = calculate_scores(res_df)
                    
                    update_leaderboard(scored_df_tmp, selected_task_name)
                    st.toast("📊 Leaderboard updated!")
                    
                    best_model_name = None
                    valid_tmp = scored_df_tmp[scored_df_tmp["error"].isna() | (scored_df_tmp["error"] == "")]
                    if not valid_tmp.empty:
                        best_model_name = valid_tmp.loc[valid_tmp['benchmark_score'].idxmax()]['model_name']
                        
                    st.session_state.run_history.append({
                        "task": selected_task_name,
                        "timestamp": st.session_state.timestamp,
                        "models": st.session_state.selected_models.copy(),
                        "best_model": best_model_name,
                        "prompt": active_prompt,
                        "scored_df": scored_df_tmp
                    })
                    
                    st.success("✅ Benchmark complete! Scroll down to see results.")
                    st.toast("✅ Results ready!")
        
            # PERFORMANCE DASHBOARD & VISUALIZATIONS
            if st.session_state.results:
                st.markdown("---")
                st.header("🏆 Performance Dashboard")
                st.caption(f"Last run: {st.session_state.timestamp} | Task: {selected_task_name}")
            
                # Process results into dataframe
                res_df = pd.DataFrame(st.session_state.results)
            
                # Add shortened names and providers
                res_df['model_name'] = res_df['model_id'].apply(
                    lambda x: st.session_state.models_df[st.session_state.models_df['id'] == x]['name'].values[0] 
                    if not st.session_state.models_df[st.session_state.models_df['id'] == x].empty else x
                )
                res_df['Provider'] = res_df['model_id'].apply(categorize_provider)
                res_df['model_name_short'] = res_df['model_name'].apply(lambda x: x[:20] + "..." if len(x) > 20 else x)
            
                # Calculate Scores
                scored_df = calculate_scores(res_df)
                valid_df = scored_df[scored_df["error"].isna() | (scored_df["error"] == "")].copy()
                
                # We already updated the leaderboard during the run_btn phase, but if the app reloads, 
                # we don't need to update again unless they just clicked.
                
                if valid_df.empty:
                    st.error("All models failed. Check errors below.")
                else:
                    # SECTION A - Summary Metric Cards
                    st.markdown("### 📈 Executive Summary")
                    col1, col2, col3, col4 = st.columns(4)
                
                    # Card 1: Fastest
                    fastest_row = valid_df.loc[valid_df['response_time_ms'].idxmin()]
                    avg_time = valid_df['response_time_ms'].mean()
                    diff_time = fastest_row['response_time_ms'] - avg_time
                    col1.metric("Fastest Model", f"{fastest_row['model_name_short']} ({fastest_row['response_time_ms']:.0f}ms)", f"{diff_time:.0f}ms vs avg", delta_color="inverse")
                
                    # Card 2: Cheapest
                    cheapest_row = valid_df.loc[valid_df['total_cost'].idxmin()]
                    avg_cost = valid_df['total_cost'].mean()
                    diff_cost = cheapest_row['total_cost'] - avg_cost
                    cost_str = "FREE" if cheapest_row['total_cost'] == 0 else f"${cheapest_row['total_cost']:.5f}"
                    col2.metric("Cheapest Model", f"{cheapest_row['model_name_short']} ({cost_str})", f"${diff_cost:.5f} vs avg", delta_color="inverse")
                
                    # Card 3: Highest Score
                    best_row = valid_df.loc[valid_df['benchmark_score'].idxmax()]
                    avg_score = valid_df['benchmark_score'].mean()
                    diff_score = best_row['benchmark_score'] - avg_score
                    col3.metric("Highest Score", f"{best_row['model_name_short']} ({best_row['benchmark_score']:.1f}/100)", f"{diff_score:.1f} vs avg")
                
                    # Card 4: Total Cost
                    run_cost = valid_df['total_cost'].sum()
                    col4.metric("Total Cost of Run", f"${run_cost:.5f}")
                
                    # SECTION B - Charts
                    st.markdown("### 📊 Visualizations")
                    ch_col1, ch_col2 = st.columns(2)
                
                    with ch_col1:
                        st.plotly_chart(make_response_time_chart(valid_df), use_container_width=True)
                        st.plotly_chart(make_cost_comparison_chart(valid_df), use_container_width=True)
                        st.plotly_chart(make_response_length_chart(valid_df), use_container_width=True)
                    
                    with ch_col2:
                        st.plotly_chart(make_token_usage_chart(valid_df), use_container_width=True)
                        st.plotly_chart(make_cost_vs_speed_scatter(valid_df), use_container_width=True)
                
                    # SECTION C - Detailed Comparison Table
                    st.markdown("### 📑 Detailed Comparison Table")
                    table_df = valid_df[['rank', 'model_name', 'Provider', 'benchmark_score', 'response_time_ms', 'total_tokens', 'total_cost', 'resp_len']].copy()
                    table_df.rename(columns={
                        'rank': 'Rank', 'model_name': 'Model', 'benchmark_score': 'Score',
                        'response_time_ms': 'Time(ms)', 'total_tokens': 'Tokens',
                        'total_cost': 'Cost ($)', 'resp_len': 'Response Length'
                    }, inplace=True)
                
                    table_df.sort_values(by="Rank", inplace=True)
                
                    def highlight_rank_1(row):
                        if row['Rank'] == 1:
                            return ['background-color: rgba(46, 125, 50, 0.3)'] * len(row)
                        return [''] * len(row)
                    
                    st.dataframe(
                        table_df.style.apply(highlight_rank_1, axis=1).format({'Time(ms)': '{:.0f}', 'Cost ($)': '${:.6f}', 'Score': '{:.1f}'}),
                        use_container_width=True, hide_index=True
                    )
                
                    csv = table_df.to_csv(index=False)
                    st.download_button("📥 Download Results CSV", data=csv, file_name=f"benchmark_{selected_task_name.replace(' ', '_')}.csv", mime="text/csv")
                
                    # SECTION D - Side-by-Side Response Viewer
                    st.markdown("### 🆚 Side-by-Side Response Viewer")
                    model_choices = valid_df['model_name'].tolist()
                    viewer_col1, viewer_col2 = st.columns(2)
                
                    with viewer_col1:
                        model_a = st.selectbox("Model A", options=model_choices, index=0)
                        row_a = valid_df[valid_df['model_name'] == model_a].iloc[0]
                        badge_a = "<span class='free-badge'>Free</span>" if row_a['total_cost'] == 0 else "<span class='paid-badge'>Paid</span>"
                        st.markdown(f"#### {row_a['model_name']} {badge_a}", unsafe_allow_html=True)
                        st.markdown(f"**Provider:** {row_a['Provider']} | **Rank:** {row_a['rank']}")
                        st.markdown(f"<div class='response-box'>{row_a['response_text']}</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Time", f"{row_a['response_time_ms']/1000:.2f}s")
                        c2.metric("Tokens", row_a['total_tokens'])
                        c3.metric("Cost", f"${row_a['total_cost']:.5f}")
                    
                    with viewer_col2:
                        model_b = st.selectbox("Model B", options=model_choices, index=min(1, len(model_choices)-1))
                        row_b = valid_df[valid_df['model_name'] == model_b].iloc[0]
                        badge_b = "<span class='free-badge'>Free</span>" if row_b['total_cost'] == 0 else "<span class='paid-badge'>Paid</span>"
                        st.markdown(f"#### {row_b['model_name']} {badge_b}", unsafe_allow_html=True)
                        st.markdown(f"**Provider:** {row_b['Provider']} | **Rank:** {row_b['rank']}")
                        st.markdown(f"<div class='response-box'>{row_b['response_text']}</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Time", f"{row_b['response_time_ms']/1000:.2f}s")
                        c2.metric("Tokens", row_b['total_tokens'])
                        c3.metric("Cost", f"${row_b['total_cost']:.5f}")

                # Display errors if any
                error_df = scored_df[~(scored_df["error"].isna() | (scored_df["error"] == ""))]
                if not error_df.empty:
                    st.markdown("### ⚠️ Errors")
                    for _, row in error_df.iterrows():
                        st.error(f"**{row['model_name']}** failed: {row['error']}")



with main_tabs[1]:
    st.header("🏆 AI Model Leaderboard")
    st.markdown("Cumulative rankings across all your benchmark runs.")
    
    ldf = get_leaderboard_df()
    if ldf.empty:
        st.info("No leaderboard data yet. Run a benchmark first!")
    else:
        # Merge with models_df for names
        if not st.session_state.models_df.empty:
            ldf['Model Name'] = ldf['model_id'].apply(
                lambda x: st.session_state.models_df[st.session_state.models_df['id'] == x]['name'].values[0] 
                if not st.session_state.models_df[st.session_state.models_df['id'] == x].empty else x
            )
        else:
            ldf['Model Name'] = ldf['model_id']
            
        # Podium
        top_n = min(3, len(ldf))
        medals = ["🥇 1st Place", "🥈 2nd Place", "🥉 3rd Place"]
        cols = st.columns(3)
        for i in range(top_n):
            with cols[i]:
                st.markdown(f"### {medals[i]}")
                st.markdown(f"**{ldf.iloc[i]['Model Name']}**")
                st.metric("Avg Score", f"{ldf.iloc[i]['avg_score']:.1f}")
                
        st.markdown("---")
        
        # Chart
        st.subheader("Top 10 Models by Average Score")
        top_10 = ldf.head(10).sort_values(by="avg_score", ascending=True)
        fig = px.bar(top_10, x="avg_score", y="Model Name", orientation='h', color="avg_score", color_continuous_scale="Viridis")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        display_ldf = ldf[['Model Name', 'avg_score', 'avg_time', 'avg_cost', 'run_count']].copy()
        display_ldf.rename(columns={'avg_score': 'Avg Score', 'avg_time': 'Avg Time(ms)', 'avg_cost': 'Avg Cost($)', 'run_count': 'Runs'}, inplace=True)
        st.dataframe(display_ldf.style.format({'Avg Score': '{:.1f}', 'Avg Time(ms)': '{:.0f}', 'Avg Cost($)': '${:.5f}'}), use_container_width=True, hide_index=True)
        
        csv = display_ldf.to_csv(index=False)
        st.download_button("📥 Download Full Leaderboard CSV", data=csv, file_name="leaderboard.csv", mime="text/csv")


with main_tabs[2]:
    st.header("🤖 AI Recommender")
    st.markdown("Not sure which model to use? Get personalized recommendations based on your needs.")
    
    with st.form("recommender_form"):
        task_names = list(TASKS.keys())
        rec_task = st.selectbox("What is your task?", options=task_names)
        
        rec_priority = st.radio("What matters most?", ["Speed", "Quality", "Cost", "Balanced"], horizontal=True)
        rec_budget = st.radio("Budget?", ["Free Only", "Under $0.01", "Any Budget"], horizontal=True)
        
        submit_rec = st.form_submit_button("🎯 Get Recommendations", type="primary")
        
    if submit_rec:
        recs = recommend_model(rec_task, rec_priority, rec_budget)
        if not recs:
            st.warning("No models found matching those exact criteria. Try loosening your constraints.")
        else:
            st.markdown("### Top Recommendations")
            for r in recs:
                with st.container():
                    col_info, col_btn = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"#### {r['name']} ({r['provider']})")
                        st.markdown(f"**Why:** {r['reasoning']}")
                        st.markdown(f"**Cost:** ${r['cost']} / query")
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button(f"➕ Add", key=f"add_{r['id']}", use_container_width=True):
                            if r['id'] not in st.session_state.selected_models:
                                if len(st.session_state.selected_models) < 5:
                                    st.session_state.selected_models.append(r['id'])
                                    st.toast(f"Added {r['name']} to comparison!")
                                else:
                                    st.error("Max 5 models selected.")
                            else:
                                st.warning("Already selected.")
                    st.divider()

with main_tabs[3]:
    st.header("📊 Run History")
    if not st.session_state.run_history:
        st.info("No runs yet in this session.")
    else:
        history_opts = [f"Run {i+1}: {rh['task']} ({rh['timestamp']})" for i, rh in enumerate(st.session_state.run_history)]
        
        # Display timeline
        for i, rh in reversed(list(enumerate(st.session_state.run_history))):
            with st.expander(f"Run {i+1}: {rh['task']} @ {rh['timestamp']}", expanded=(i == len(st.session_state.run_history)-1)):
                st.markdown(f"**Models:** {', '.join(rh['models'])}")
                if rh['best_model']:
                    st.markdown(f"**Best Model:** 🏆 {rh['best_model']}")
                st.markdown(f"**Prompt:** {rh['prompt'][:100]}...")
                
        st.markdown("---")
        st.subheader("Compare Past Runs")
        comp_runs = st.multiselect("Select exactly 2 runs to compare scores", options=history_opts, max_selections=2)
        if len(comp_runs) == 2:
            idx1 = history_opts.index(comp_runs[0])
            idx2 = history_opts.index(comp_runs[1])
            
            df1 = st.session_state.run_history[idx1]['scored_df'].copy()
            df2 = st.session_state.run_history[idx2]['scored_df'].copy()
            
            df1['Run'] = f"Run {idx1+1}"
            df2['Run'] = f"Run {idx2+1}"
            
            comb = pd.concat([df1, df2])
            if not comb.empty and 'model_name_short' in comb.columns and 'benchmark_score' in comb.columns:
                fig = px.bar(comb, x="model_name_short", y="benchmark_score", color="Run", barmode="group", title="Score Comparison Between Runs")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

# EXPORT SECTION
if st.session_state.results and 'scored_df' in locals() and not scored_df.empty:
    st.divider()
    st.subheader("📥 Export Results")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_buf = export_to_csv(scored_df, selected_task_name)
        st.download_button(
            label="Download CSV",
            data=csv_buf,
            file_name=f"benchmark_{selected_task_name.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col2:
        with st.spinner("Generating PDF..."):
            try:
                pdf_buf = export_to_pdf(scored_df, selected_task_name)
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_buf,
                    file_name=f"benchmark_{selected_task_name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Failed to generate PDF: {e}")

tabs_code = """
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
"""

with open('ai_dashboard/app.py', 'a', encoding='utf-8') as f:
    f.write('\n\n' + tabs_code)

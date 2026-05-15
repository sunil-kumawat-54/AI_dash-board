import sys

with open('ai_dashboard/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_main = False
for i, line in enumerate(lines):
    if line.startswith('if st.session_state.models_df.empty:'):
        in_main = True
        new_lines.append('main_tabs = st.tabs(["🔬 Benchmark", "🏆 Leaderboard", "🤖 AI Recommender", "📊 Run History"])\n\n')
        new_lines.append('with main_tabs[0]:\n')
        new_lines.append('    ' + line)
    elif in_main:
        if line.strip() == '':
            new_lines.append(line)
        else:
            new_lines.append('    ' + line)
    else:
        new_lines.append(line)

with open('ai_dashboard/app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

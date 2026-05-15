# 🤖 AI Model Explorer & Benchmark Dashboard

A comprehensive, interactive Streamlit application that allows users to benchmark, compare, and analyze various Large Language Models (LLMs) via the OpenRouter API. This tool acts as an all-in-one suite to identify the best model for any given task based on speed, cost, and output quality.

## ✨ Features
- **Live Model Fetching:** Connects securely to OpenRouter and pulls down the complete list of available AI models, their context windows, speeds, and pricing.
- **Robust Filtering:** Sort and search models by free vs. paid, specific providers, and context length requirements.
- **Automated Benchmarking:** Select up to 5 models and run them concurrently on specific tasks. 
- **Pre-built Task Templates:** Choose from common prompts like coding, creative writing, data extraction, and logical reasoning, or write custom prompts.
- **Dynamic Performance Dashboard:** View stunning Plotly visualizations comparing response times, token usage, cost efficiencies, and response lengths.
- **Value Scoring:** Automatically calculates a "Benchmark Score" factoring in speed, token efficiency, length, and total query cost.
- **Leaderboard:** Keeps a persistent record of model performance across all your sessions.
- **AI Recommender:** Suggests the perfect models for your workload based on your priority (speed, quality, cost) and budget.
- **Side-by-Side Viewer:** Interactively examine the exact response text from two models at once.
- **Export to PDF / CSV:** Download fully-formatted benchmark reports with charts and tables in just one click.

## 🚀 Installation

Follow these exact steps to run the application locally:

```bash
# 1. Clone or download the repository
# (Assuming you are in the project folder)

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Windows:
venv\\Scripts\\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the Streamlit app
streamlit run app.py
```

## 🔑 Getting an OpenRouter API Key
This app uses OpenRouter to access hundreds of models through a single API interface.
1. Create a free account at [OpenRouter.ai](https://openrouter.ai/).
2. Navigate to [https://openrouter.ai/keys](https://openrouter.ai/keys).
3. Click "Create Key", give it a name, and copy the key.
4. Paste it into the Settings sidebar of this dashboard.

## 📖 How to Use the Dashboard

1. **Connect:** Enter your OpenRouter API key in the sidebar and click "Connect".
2. **Filter & Select:** Use the sidebar filters to find the right models (e.g., Free only, specific providers). Check the boxes for up to 5 models.
3. **Configure Task:** In the "Benchmark" tab, choose a task preset or write your own prompt.
4. **Run Benchmark:** Click "Run Benchmark". The app will query all selected models simultaneously and calculate scores.
5. **Analyze:** Scroll down to the Performance Dashboard to view the data visualizations and comparison tables.
6. **Compare Responses:** Use the "Side-by-Side Response Viewer" at the bottom of the benchmark tab to manually evaluate output quality.
7. **Export:** Click the download buttons at the bottom of the page to save the results as a CSV or a professional PDF report.

## 📂 Folder Structure

```text
ai_dashboard/
├── app.py                     # Main Streamlit application entry point
├── config.py                  # Page and UI configuration settings
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── leaderboard.json           # Persisted leaderboard data (auto-generated)
└── utils/                     # Helper modules
    ├── __init__.py
    ├── api_handler.py         # OpenRouter API communication logic
    ├── exporter.py            # PDF and CSV generation tools
    ├── helpers.py             # Data formatting and categorization 
    ├── leaderboard.py         # Leaderboard file reading/writing
    ├── recommender.py         # Logic for AI model recommendations
    ├── scoring.py             # Formula for benchmark score calculation
    ├── task_templates.py      # Pre-defined prompts and system messages
    └── visualizations.py      # Plotly chart generation functions
```

## 🛠️ Technologies Used

| Technology | Usage |
|---|---|
| **Python 3** | Core programming language |
| **Streamlit** | Web framework for the interactive UI |
| **Pandas** | Data processing, manipulation, and metric calculation |
| **Plotly Graph Objects** | Interactive, custom data visualizations |
| **Requests** | Handling REST API calls to OpenRouter |
| **fpdf2** | Generating formatted PDF reports |

## 📸 Screenshots
*(Placeholder for future screenshots of the dashboard interface, charts, and recommender tab)*

## ⚠️ Known Limitations
- Model performance (speed/time) can fluctuate heavily based on current OpenRouter server loads and the specific provider's latency.
- Cost calculations are estimates based on OpenRouter's reported token prices and might not precisely mirror final billing (though usually accurate to 5 decimal places).
- For large context models or free-tier rate limits, requests might occasionally time out or return errors. The dashboard handles these gracefully by omitting failed runs from the scoring.

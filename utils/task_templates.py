"""
utils/task_templates.py
Pre-defined benchmark tasks with prompts and evaluation criteria.
"""

TASKS = {
    "Summarize Text": {
        "description": "Paste any paragraph and get a summary",
        "example_input": "The rapid advancement of artificial intelligence has led to significant shifts in the global economy. Many traditional jobs are being automated, requiring the workforce to adapt through reskilling. At the same time, new industries are emerging, creating opportunities in machine learning engineering, data ethics, and AI system management. While some economists warn of short-term job displacement, others argue that AI will ultimately augment human capabilities and lead to unprecedented levels of productivity and innovation. The key to navigating this transition will be proactive education policies and robust social safety nets to support those most affected by the changes.",
        "system_prompt": "You are a professional summarizer. Be concise and accurate.",
        "evaluation_criteria": ["accuracy", "brevity", "key points covered"]
    },
    "Code Generation": {
        "description": "Generate Python code for a given task",
        "example_input": "Write a Python function that reads a CSV file and returns the top 5 rows sorted by a given column name in descending order. Include error handling for missing files or missing columns.",
        "system_prompt": "You are an expert Python developer. Write clean, commented code.",
        "evaluation_criteria": ["correctness", "readability", "comments"]
    },
    "SQL Query Writing": {
        "description": "Translate a natural language request into a SQL query",
        "example_input": "Write a PostgreSQL query to find the top 3 customers who have spent the most money in the last 30 days. We have two tables: 'customers' (id, name, email) and 'orders' (id, customer_id, amount, order_date).",
        "system_prompt": "You are a database administrator and SQL expert. Write valid, optimized SQL queries.",
        "evaluation_criteria": ["syntax correctness", "efficiency", "accuracy"]
    },
    "Concept Explanation": {
        "description": "Explain a complex concept to a beginner",
        "example_input": "Explain how quantum computing works and how it differs from classical computing. Use an analogy that a 10-year-old would understand.",
        "system_prompt": "You are an enthusiastic science teacher. Explain complex topics simply, using engaging analogies.",
        "evaluation_criteria": ["clarity", "analogy quality", "simplicity"]
    },
    "Professional Email": {
        "description": "Draft a formal email for a specific professional scenario",
        "example_input": "Draft an email to a client named Sarah, apologizing for a 2-day delay in delivering the Q3 marketing report. Explain that the delay was due to unexpected data anomalies, and assure her it will be sent tomorrow morning.",
        "system_prompt": "You are a professional communications expert. Write polite, clear, and professional business correspondence.",
        "evaluation_criteria": ["professional tone", "clarity", "appropriateness"]
    },
    "Creative Writing": {
        "description": "Generate a creative story or scene",
        "example_input": "Write a short, dialogue-heavy scene between two astronauts who have just discovered that their ship's AI has been secretly altering their navigational coordinates for the past month.",
        "system_prompt": "You are an award-winning sci-fi author. Write compelling, atmospheric scenes with strong character voices.",
        "evaluation_criteria": ["creativity", "dialogue naturalness", "pacing"]
    }
}

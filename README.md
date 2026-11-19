# AI Mystery Quest

An interactive detective investigation and puzzle game built with **Python**, **Flask**, **HTML**, **CSS**, **JavaScript**, and the **Groq API**, complete with an automatic **Demo Mode** fallback when no API key is configured.

## Project Structure

```text
ai_mystery_quest/
├── .env                  # Stores your Groq API key
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── app.py                # Flask backend & Groq API integration
├── templates/
│   └── index.html        # Frontend UI
└── static/
    ├── style.css         # Dark detective theme & layout
    └── script.js         # Game state, API requests, & progress tracking
```

## Setup & Run (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open **`http://127.0.0.1:5000`** in your browser. Add your `GROQ_API_KEY` inside `.env` to enable live AI generation, or leave it as-is to play in **Demo Mode**.

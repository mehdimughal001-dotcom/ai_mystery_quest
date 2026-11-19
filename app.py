import os
import json
import random
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Initialize Groq client if API key is available
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
USE_DEMO_MODE = not bool(GROQ_API_KEY) or GROQ_API_KEY == "your_groq_api_key_here"

client = None
if not USE_DEMO_MODE:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Groq client ({e}). Switching to Demo Mode.")
        USE_DEMO_MODE = True

MODEL_NAME = "llama-3.3-70b-versatile"

# Fallback cases for Demo Mode
DEMO_CASES = [
    {
        "title": "The Midnight Museum Heist",
        "setting": "Grand City Museum, 11:45 PM during a thunderstorm.",
        "summary": "The priceless 'Star of Orient' diamond vanished from a locked glass case. The alarm never triggered, and only three staff members were inside the building.",
        "suspects": [
            {"name": "Julian Vance", "role": "Head Curator", "alibi": "Claims he was cataloging ancient coins in the basement vault."},
            {"name": "Elena Rostova", "role": "Security Chief", "alibi": "Says she was rebooting the CCTV servers in the control room."},
            {"name": "Marcus Thorne", "role": "Night Janitor", "alibi": "States he was mopping the East Wing hallway far from the exhibit."}
        ],
        "evidence": [
            "A damp microfiber cloth smelling of glass cleaner found behind the display pedestal.",
            "Security logs show the alarm system was bypassed using the Security Chief's master override code at 11:42 PM.",
            "Muddy footprints size 10 leading from the basement stairs—Julian wears size 8, Elena wears size 7."
        ],
        "puzzle": {
            "question": "A torn sticky note in the control room reads: 'Shift code to the reverse of the hour the diamond vanished (11:42 -> ??)'. What 4-digit code disabled the glass sensor?",
            "hint_1": "Look closely at the time the alarm was bypassed in the evidence log.",
            "hint_2": "Take the digits of 11:42 (1142) and reverse them completely."
        },
        "culprit": "Elena Rostova",
        "solution_keywords": ["elena", "rostova", "security", "2411"],
        "explanation": "Elena Rostova used her master override code at 11:42 PM and reversed the timestamp (2411) to disable the glass sensor, framing the janitor with spare boots."
    },
    {
        "title": "Poison at the Obsidian Gala",
        "setting": "Blackwood Manor, Annual Charity Dinner.",
        "summary": "Tech billionaire Victor Sterling collapsed after taking a sip from his champagne flute. Toxicology confirms a fast-acting toxin.",
        "suspects": [
            {"name": "Clara Sterling", "role": "Estranged Wife", "alibi": "Was speaking with the orchestra conductor on stage."},
            {"name": "Dr. Aris Thorne", "role": "Business Partner", "alibi": "Claims he was taking an urgent phone call on the balcony."},
            {"name": "Chef Laurent", "role": "Head Chef", "alibi": "Was plating desserts in the kitchen with four sous-chefs."}
        ],
        "evidence": [
            "Residue of bitter almond oil was found on the rim of Victor's glass, not inside the champagne bottle.",
            "A vial labeled 'Cyanide-B' was found tucked inside a discarded surgical glove in the balcony planter.",
            "Phone records show Dr. Aris Thorne made zero outgoing or incoming calls between 8:00 PM and 9:30 PM."
        ],
        "puzzle": {
            "question": "Dr. Thorne's encrypted notepad has a Caesar cipher clue (+1 shift): 'HM UIF HMBTT'. Decode the three words to confirm how the poison was delivered.",
            "hint_1": "Shift each letter backward by 1 in the alphabet (H -> G, M -> L).",
            "hint_2": "HM = IN, UIF = THE. Now decode HMBTT."
        },
        "culprit": "Dr. Aris Thorne",
        "solution_keywords": ["aris", "thorne", "partner", "in the glass"],
        "explanation": "Dr. Aris Thorne lied about his phone call, laced the rim of the glass ('IN THE GLASS'), and hid the vial in the balcony planter."
    }
]


def query_groq_json(prompt):
    """Helper function to query Groq and enforce valid JSON response."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a master mystery game designer. Always output valid JSON only, with no markdown formatting or extra commentary."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


@app.route("/")
def index():
    return render_template("index.html", demo_mode=USE_DEMO_MODE)


@app.route("/api/generate-case", methods=["POST"])
def generate_case():
    data = request.get_json() or {}
    difficulty = data.get("difficulty", "Medium")
    theme = data.get("theme", "Classic Noir")

    if USE_DEMO_MODE:
        case = random.choice(DEMO_CASES)
        return jsonify({"status": "success", "demo_mode": True, "case": case})

    prompt = f"""
    Create an original, solvable detective mystery case with difficulty '{difficulty}' and theme '{theme}'.
    Return ONLY a JSON object with this exact schema:
    {{
        "title": "Case Title",
        "setting": "Location and time of crime",
        "summary": "2-3 sentence overview of the crime",
        "suspects": [
            {{"name": "Name 1", "role": "Role", "alibi": "Alibi statement"}},
            {{"name": "Name 2", "role": "Role", "alibi": "Alibi statement"}},
            {{"name": "Name 3", "role": "Role", "alibi": "Alibi statement"}}
        ],
        "evidence": [
            "Clue 1 pointing to inconsistencies",
            "Clue 2 physical evidence",
            "Clue 3 timeline or digital clue"
        ],
        "puzzle": {{
            "question": "A logic riddle, cipher, or numeric puzzle tied directly to the evidence",
            "hint_1": "Subtle nudge toward solving the puzzle",
            "hint_2": "Stronger clue without giving the exact final word"
        }},
        "culprit": "Exact full name of the guilty suspect",
        "solution_keywords": ["lowercase_lastname", "lowercase_puzzle_answer"],
        "explanation": "Clear explanation of who did it, how they did it, and how the evidence proves it."
    }}
    """
    try:
        case_data = query_groq_json(prompt)
        return jsonify({"status": "success", "demo_mode": False, "case": case_data})
    except Exception as e:
        print(f"Groq API Error during case generation: {e}")
        fallback = random.choice(DEMO_CASES)
        return jsonify({"status": "success", "demo_mode": True, "case": fallback, "warning": "API error; loaded Demo Case."})


@app.route("/api/hint", methods=["POST"])
def get_hint():
    data = request.get_json() or {}
    case = data.get("case", {})
    hint_level = data.get("hint_level", 1)

    if USE_DEMO_MODE:
        puzzle = case.get("puzzle", {})
        hint_text = puzzle.get("hint_1") if hint_level == 1 else puzzle.get("hint_2", "Compare every suspect's alibi directly against the physical evidence.")
        return jsonify({"status": "success", "hint": hint_text})

    prompt = f"""
    You are a seasoned detective partner. The player needs Hint #{hint_level} for this case:
    Title: {case.get('title')}
    Evidence: {case.get('evidence')}
    Puzzle: {case.get('puzzle', {}).get('question')}
    Culprit (DO NOT REVEAL DIRECTLY): {case.get('culprit')}

    Provide a clever, atmospheric hint (max 2 sentences) that guides the player without spoiling the culprit's name.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=120
        )
        return jsonify({"status": "success", "hint": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def detective_chat():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    case = data.get("case", {})

    if not question:
        return jsonify({"status": "error", "message": "Please ask a valid question."}), 400

    if USE_DEMO_MODE:
        q_lower = question.lower()
        if "alibi" in q_lower or "suspect" in q_lower:
            reply = "Detective AI (Demo): Cross-check each suspect's claimed location against the physical items left at the scene. Someone is lying about where they were."
        elif "puzzle" in q_lower or "code" in q_lower or "cipher" in q_lower:
            reply = "Detective AI (Demo): Look closely at the numbers or letters in the puzzle. Try reversing them or shifting letters by one position."
        elif "evidence" in q_lower:
            reply = "Detective AI (Demo): Every piece of evidence eliminates an innocent person or exposes a contradiction in one suspect's alibi."
        else:
            reply = f"Detective AI (Demo): Interesting angle regarding '{question}'. Focus on who had both opportunity and access to the crime scene."
        return jsonify({"status": "success", "reply": reply})

    system_prompt = f"""
    You are Detective AI, a sharp noir partner assisting a player investigating a case.
    Case Details: {json.dumps(case)}
    Rules:
    1. Answer the player's question in character (concise, analytical, 2-3 sentences max).
    2. Never directly name the culprit unless the player has already solved the case.
    3. Help them analyze alibis, evidence, or puzzle mechanics.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.6,
            max_tokens=180
        )
        return jsonify({"status": "success", "reply": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/submit", methods=["POST"])
def submit_answer():
    data = request.get_json() or {}
    suspect_guess = data.get("suspect", "").strip().lower()
    puzzle_answer = data.get("puzzle_answer", "").strip().lower()
    case = data.get("case", {})

    actual_culprit = case.get("culprit", "").strip().lower()
    keywords = [k.lower() for k in case.get("solution_keywords", [])]

    culprit_correct = (suspect_guess == actual_culprit) or (suspect_guess in actual_culprit and len(suspect_guess) > 3)
    puzzle_correct = any(k in puzzle_answer for k in keywords) or (len(puzzle_answer) > 2 and puzzle_answer in str(case.get("explanation", "")).lower())

    if culprit_correct and puzzle_correct:
        return jsonify({
            "status": "success",
            "solved": True,
            "score_earned": 100,
            "message": "Case Closed! You identified the culprit and cracked the puzzle.",
            "explanation": case.get("explanation", "")
        })
    elif culprit_correct and not puzzle_correct:
        return jsonify({
            "status": "success",
            "solved": False,
            "score_earned": 0,
            "message": "You have the right suspect, but your puzzle solution is off. Double-check the clues!"
        })
    elif not culprit_correct and puzzle_correct:
        return jsonify({
            "status": "success",
            "solved": False,
            "score_earned": 0,
            "message": "Your puzzle solution is right, but you accused the wrong suspect! Re-examine their alibis."
        })
    else:
        return jsonify({
            "status": "success",
            "solved": False,
            "score_earned": 0,
            "message": "Both the suspect and puzzle answer are incorrect. Keep investigating!"
        })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

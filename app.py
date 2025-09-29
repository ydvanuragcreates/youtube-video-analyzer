import os

# This line stabilizes the multi-threading libraries and prevents server crashes.
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
# Import all necessary functions from your youtube_analyzer module
from youtube_analyzer import analyze_video, generate_quiz_from_text, answer_question_from_text
from dotenv import load_dotenv
import secrets

# Load environment variables from the .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
# A secret key is required for session management to work
app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    """Renders the main analysis page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handles the video analysis request from the main page."""
    try:
        data = request.get_json()
        if not data or 'youtube_url' not in data:
            return jsonify({'error': 'YouTube URL is required.'}), 400

        url = data['youtube_url']
        # Call the main analysis function from the other module
        analysis_results = analyze_video(url)

        # Store the full transcript in the user's session to be used by the quiz and chat features
        session['transcript'] = analysis_results['transcript']
        
        return jsonify(analysis_results)

    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/quiz')
def quiz():
    """Renders the quiz page, checking if a transcript exists first."""
    if 'transcript' not in session or not session['transcript']:
        # If no transcript, render the quiz page with an error message
        return render_template('quiz.html', error="Please analyze a video first to generate a quiz.")
    return render_template('quiz.html')

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    """Generates quiz questions and sends them to the quiz page."""
    try:
        if 'transcript' not in session:
            return jsonify({'error': 'No transcript found in session.'}), 400

        transcript = session['transcript']
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found. Please create a .env file with your API key.")

        # Call the quiz generation function
        questions = generate_quiz_from_text(transcript, api_key)
        
        return jsonify(questions)

    except Exception as e:
        print(f"Error in /generate_questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    """Handles a question from the chat interface."""
    try:
        data = request.get_json()
        if 'transcript' not in session:
            return jsonify({'error': 'No transcript found in session.'}), 400
        if not data or 'question' not in data or not data['question'].strip():
            return jsonify({'error': 'A question is required.'}), 400
        
        transcript = session['transcript']
        question = data['question']
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found.")

        # Call the new question-answering function
        answer = answer_question_from_text(transcript, question, api_key)
        return jsonify({'answer': answer})

    except Exception as e:
        print(f"Error in /ask: {e}")
        return jsonify({'error': str(e)}), 500

# This block ensures the server runs only when the script is executed directly
if __name__ == '__main__':
    app.run(debug=True)
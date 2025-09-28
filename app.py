from flask import Flask, render_template, request, jsonify, session
import youtube_analyzer
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
# A secret key is required to use sessions in Flask
app.secret_key = os.urandom(24) 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        try:
            # The analysis function now returns a simpler dictionary
            results = youtube_analyzer.analyze_video(youtube_url)
            # We store the full transcript in the user's session
            # This allows the quiz page to access it later
            session['transcript'] = results.get('transcript')
            return render_template('index.html', results=results)
        except Exception as e:
            # Return a clear error message to the user on the webpage
            return render_template('index.html', error=str(e))
    return render_template('index.html')

@app.route('/quiz')
def quiz():
    # This route just renders the quiz page.
    # The actual questions are fetched by JavaScript on that page.
    if 'transcript' not in session or not session['transcript']:
        # If the user tries to access the quiz page directly without analyzing a video
        return render_template('quiz.html', error="You must analyze a video first to create a quiz!")
    return render_template('quiz.html')

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    """
    This is an API endpoint that the quiz page calls.
    It takes the transcript from the session and uses the Gemini API to create questions.
    """
    transcript = session.get('transcript')
    if not transcript:
        return jsonify({'error': 'No transcript available in session.'}), 400

    try:
        # Get the API key from the environment variables (.env file)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return jsonify({'error': 'GEMINI_API_KEY is not set on the server.'}), 500

        questions = youtube_analyzer.generate_quiz_from_text(transcript, api_key)
        return jsonify(questions)

    except Exception as e:
        print(f"Error in /generate_questions: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


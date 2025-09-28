from flask import Flask, render_template, request, jsonify
import youtube_analyzer
import os

# Create a Flask web application
app = Flask(__name__)

# Define the main route for the web page
@app.route('/', methods=['GET', 'POST'])
def index():
    # If the request is a POST, it means the user submitted the form
    if request.method == 'POST':
        # Get the URL from the form data
        youtube_url = request.form['youtube_url']

        if not youtube_url:
            return render_template('index.html', error="Please enter a YouTube URL.")

        try:
            # Call the analysis function from our other script
            # This will take a long time to run
            results = youtube_analyzer.analyze_video(youtube_url)
            # Render the page again, but this time with the results
            return render_template('index.html', results=results)
        except Exception as e:
            # If any error occurs, show it on the page
            print(f"An error occurred: {e}")
            return render_template('index.html', error=f"An error occurred: {e}")

    # If the request is a GET, just show the initial page
    return render_template('index.html', results=None)

# This allows you to run the app by executing "python app.py"
if __name__ == '__main__':
    # Set debug=True for development, which provides helpful error messages
    app.run(debug=True)

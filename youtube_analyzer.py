import os
import subprocess
import whisper
import spacy
from gensim import corpora
from gensim.models import LdaModel
import re
import uuid
import requests
import json
import torch

# Load the spaCy model once when the module is imported
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading 'en_core_web_sm' model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def download_audio(youtube_url):
    unique_id = uuid.uuid4()
    output_path = f"audio_{unique_id}.mp3"
    print(f"Downloading audio from {youtube_url}...")
    try:
        command = ['yt-dlp', '-x', '--audio-format', 'mp3', '-o', output_path, youtube_url]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print("Download completed.")
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to download audio. yt-dlp error: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed or not in your PATH.")

def transcribe_audio(audio_path):
    print("Transcribing audio...")
    model = whisper.load_model("base")
    
    # ---- THIS IS THE FINAL CORRECTION ----
    # The 'device' argument is not needed here. 
    # Whisper automatically uses the GPU if torch.cuda.is_available() is true.
    result = model.transcribe(audio_path) 
    # ---- END OF CORRECTION ----

    print("Transcription completed.")
    return result['text']

def generate_summary(text, num_sentences=5):
    doc = nlp(text)
    if len(list(doc.sents)) < num_sentences: return "Content is too short for a meaningful summary."
    sentences = list(doc.sents)
    word_frequencies = {word.text.lower(): 0 for word in doc if not word.is_stop and not word.is_punct}
    for word in doc:
        if word.text.lower() in word_frequencies: word_frequencies[word.text.lower()] += 1
    if not word_frequencies: return "Could not generate summary."
    max_freq = max(word_frequencies.values(), default=0)
    for word in word_frequencies.keys(): word_frequencies[word] = (word_frequencies[word]/max_freq)
    sentence_scores = {sent: sum(word_frequencies.get(word.text.lower(), 0) for word in sent) for sent in sentences}
    summarized_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    summarized_sentences.sort(key=lambda s: s.start)
    return " ".join([sent.text for sent in summarized_sentences])

def topic_modeling(text):
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and len(token.text) > 3]
    if len(tokens) < 20: return "Not enough content to determine a topic."
    id2word = corpora.Dictionary([tokens])
    corpus = [id2word.doc2bow(tokens)]
    lda_model = LdaModel(corpus=corpus, id2word=id2word, num_topics=1, random_state=100, passes=10)
    topic = lda_model.print_topics(num_topics=1, num_words=7)[0][1]
    words = re.findall(r'"(.*?)"', topic)
    return ", ".join(words).capitalize()

def analyze_video(youtube_url):
    audio_file = None
    try:
        audio_file = download_audio(youtube_url)
        transcript = transcribe_audio(audio_file)
        if not transcript.strip():
            raise RuntimeError("Transcription resulted in empty text. The video may not contain speech.")
        
        print("Analyzing transcript...")
        summary = generate_summary(transcript)
        main_topic = topic_modeling(transcript)
        print("Analysis complete.")

        return {
            "summary": summary,
            "topic": main_topic,
            "transcript": transcript
        }
    finally:
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"Cleaned up temporary file: {audio_file}")

def generate_quiz_from_text(transcript, api_key):
    print("Generating quiz questions with Gemini API...")
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    
    truncated_transcript = transcript[:8000] # Truncate to avoid exceeding API limits

    prompt = f"""
    Based on the following transcript, generate a 5-question multiple-choice quiz. The quiz should test understanding of the main concepts.
    Provide the output as a JSON array. Each object in the array should have "question" (a string), "options" (an array of 4 strings), and "answer" (the correct string from the options).
    Provide ONLY the raw JSON array output, nothing else.

    Transcript:
    ---
    {truncated_transcript}
    ---
    """

    payload = {
      "contents": [{"parts": [{"text": prompt}]}],
      "generationConfig": {"responseMimeType": "application/json"}
    }
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
    response.raise_for_status()
    
    response_data = response.json()
    json_string = response_data['candidates'][0]['content']['parts'][0]['text']
    
    try:
        # The model should return a JSON array directly
        questions = json.loads(json_string)
        # Basic validation of the received structure
        if not isinstance(questions, list) or not all('question' in q and 'options' in q and 'answer' in q for q in questions):
            raise ValueError("The received data is not in the expected quiz format.")
        return questions
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing JSON from API response: {e}")
        print(f"Received text: {json_string}")
        raise RuntimeError("Failed to parse the quiz questions from the AI. The format was incorrect.")


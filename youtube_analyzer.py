import os
import subprocess
import whisper
import spacy
from gensim import corpora
from gensim.models import LdaModel
from collections import Counter
import re
import uuid

# Load the spaCy model
# Make sure you've run: python -m spacy download en_core_web_sm
nlp = spacy.load("en_core_web_sm")

def download_audio(youtube_url):
    """
    Downloads audio from a YouTube URL to a unique temporary file.
    """
    try:
        # Generate a unique filename to avoid conflicts if multiple users access the app
        unique_id = uuid.uuid4()
        output_path = f"audio_{unique_id}.mp3"
        print(f"Downloading audio from {youtube_url}...")
        command = [
            'yt-dlp', '-x', '--audio-format', 'mp3',
            '-o', output_path, youtube_url
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print("Download completed.")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error downloading audio: {e.stderr}")
        # Raise a clear error that the web app can catch
        raise RuntimeError(f"Failed to download audio. yt-dlp error: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed or not in your PATH.")


def transcribe_audio(audio_path):
    """
    Transcribes an audio file using Whisper.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at {audio_path}")
    try:
        print("Transcribing audio...")
        # Use the "base" model for a good balance of speed and accuracy
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, fp16=False) # Set fp16=False for CPU
        print("Transcription completed.")
        return result['text']
    except Exception as e:
        raise RuntimeError(f"An error occurred during transcription: {e}")

def extract_keywords(text, num_keywords=10):
    doc = nlp(text.lower())
    keywords = [
        token.text for token in doc
        if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'ADJ']
    ]
    return [word for word, freq in Counter(keywords).most_common(num_keywords)]

def topic_modeling(text, num_topics=3, num_words=5):
    doc = nlp(text.lower())
    tokens = [
        token.lemma_ for token in doc
        if not token.is_stop and not token.is_punct and len(token.text) > 3
    ]
    if not tokens: return ["Not enough content for topic modeling."]
    id2word = corpora.Dictionary([tokens])
    corpus = [id2word.doc2bow(tokens)]
    if not corpus: return ["Could not create a corpus for topic modeling."]
    lda_model = LdaModel(corpus=corpus, id2word=id2word, num_topics=num_topics, random_state=100, passes=10)
    topics = []
    for idx, topic in lda_model.print_topics(-1, num_words=num_words):
        words = re.findall(r'"(.*?)"', topic)
        topics.append(f"Topic {idx+1}: " + ", ".join(words))
    return topics

def generate_summary(text, num_sentences=5):
    doc = nlp(text)
    if not doc or len(list(doc.sents)) < num_sentences: return "Not enough content to generate a summary."
    sentences = list(doc.sents)
    word_frequencies = Counter()
    for word in nlp(text.lower()):
        if not word.is_stop and not word.is_punct: word_frequencies[word.text] += 1
    if not word_frequencies: return "Could not determine word frequencies for summary."
    max_freq = max(word_frequencies.values(), default=0)
    for word in word_frequencies.keys(): word_frequencies[word] = (word_frequencies[word]/max_freq)
    sentence_scores = {}
    for sent in sentences:
        for word in sent:
            if word.text.lower() in word_frequencies:
                if sent in sentence_scores: sentence_scores[sent] += word_frequencies[word.text.lower()]
                else: sentence_scores[sent] = word_frequencies[word.text.lower()]
    summarized_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    summarized_sentences = sorted(summarized_sentences, key=lambda s: s.start)
    return " ".join([sent.text for sent in summarized_sentences])

def named_entity_recognition(text):
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities: entities[ent.label_] = []
        if ent.text not in entities[ent.label_]: entities[ent.label_].append(ent.text)
    return entities


# This is the function the web app (app.py) will call
def analyze_video(youtube_url):
    """
    This single function runs the entire pipeline:
    1. Downloads audio
    2. Transcribes audio
    3. Analyzes the transcript
    4. Cleans up the audio file
    5. Returns all results in a dictionary for the web app.
    """
    audio_file = None
    try:
        # Step 1: Download Audio
        audio_file = download_audio(youtube_url)

        # Step 2: Transcribe Audio
        transcript = transcribe_audio(audio_file)
        if not transcript:
            raise RuntimeError("Transcription failed. The video may have no speech.")

        # Step 3: Analyze the Transcript
        print("Analyzing transcript...")
        summary = generate_summary(transcript)
        topics = topic_modeling(transcript)
        keywords = extract_keywords(transcript)
        named_entities = named_entity_recognition(transcript)
        print("Analysis complete.")

        # Step 4: Return all results in a structured dictionary
        return {
            "summary": summary,
            "topics": topics,
            "keywords": keywords,
            "named_entities": named_entities,
            "transcript": transcript
        }
    finally:
        # Step 5: Clean up the temporary audio file
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"Cleaned up temporary file: {audio_file}")


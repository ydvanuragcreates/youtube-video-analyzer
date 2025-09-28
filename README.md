YouTube Video Transcription and Key Information Extraction
This project provides a Python script to download audio from a YouTube video, transcribe it, and extract key information such as topics, keywords, a summary, and named entities.

Core Components
YouTube Audio Extraction: Uses yt-dlp to download the audio stream from a YouTube video.

Audio Transcription: Employs OpenAI's Whisper model to convert the audio into a text transcript.

Key Information Extraction: Leverages spaCy and gensim for NLP tasks:

Keyword Extraction: Identifies the most frequent and important terms.

Topic Modeling: Discovers abstract topics using Latent Dirichlet Allocation (LDA).

Summarization: Creates a concise extractive summary.

Named Entity Recognition (NER): Finds mentions of people, places, organizations, etc.

Setup and Installation
Clone or download the project files.

Install yt-dlp: Follow the official installation instructions at https://github.com/yt-dlp/yt-dlp. On most systems with Python, you can use pip:

pip install yt-dlp

Install ffmpeg: Whisper requires ffmpeg to be installed on your system. You can download it from https://ffmpeg.org/download.html.

Install Python libraries: Install the required Python packages using the requirements.txt file.

pip install -r requirements.txt

Download spaCy model: After installing the libraries, you need to download the English language model for spaCy.

python -m spacy download en_core_web_sm

How to Run the Script
Open your terminal or command prompt.

Navigate to the directory where you saved the files.

Run the main script:

python youtube_analyzer.py

You will be prompted to enter a YouTube video URL. Paste the URL and press Enter.

The script will then download, transcribe, and analyze the video. The results will be printed to the console, and a full transcript will be saved in a file named transcript.txt.

Output Structure
The output is presented in the console and includes the following sections:

Summary: A brief, auto-generated summary of the video's content.

Key Topics: A list of the main topics discussed, with associated keywords.

Keywords: A comma-separated list of the most important keywords.

Named Entities: A categorized list of entities mentioned, such as:

PERSON: People's names.

ORG: Organizations, companies, etc.

GPE: Geopolitical entities (countries, cities).

DATE: Specific dates mentioned.

And other entity types as identified by spaCy.

Full Transcript: The complete transcript is saved to transcript.txt.

Example Console Output:
--- Summary ---
This is an example summary of the video content, highlighting the main points in a few sentences.

--- Key Topics ---
- Topic 1: technology, ai, future, data
- Topic 2: development, python, code, learning

--- Keywords ---
python, ai, machine learning, development, future, data, code, project, technology, tutorial

--- Named Entities ---
PERSON: Guido van Rossum
ORG: OpenAI, Google
GPE: California

Full transcript saved to transcript.txt

This structured output makes it easy to quickly understand the video's content and access the full text for deeper analysis.
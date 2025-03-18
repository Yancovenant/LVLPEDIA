# Import required libraries
import asyncio
import os
import re
import fitz
import time
import subprocess
import threading
import json

from flask import Flask, request, jsonify, send_file
from IPython.display import display, HTML, clear_output
from pyngrok import ngrok

import edge_tts


#!cloudflared tunnel run colab-tunnel

# Initialize Flask app
app = Flask(__name__)
port = 5000

# Progress Tracking
progress_status = {"progress": 0, "status": "Idle"}

def start_cloudflare_tunnel():
    """Starts Cloudflare Tunnel in the background."""
    print('Running Cloudflare Tunnel.....')
    subprocess.Popen(["cloudflared", "tunnel", "run", "colab3"])

def update_progress(status, percentage):
    """Updates the progress bar and logs in Google Colab."""
    progress_status["progress"] = percentage
    progress_status["status"] = status

    print(f"[{percentage}%] {status}")

@app.route("/", methods=["GET"])
def home():
    return "LVLPEDIA API is running!", 200

# Text-to-Speech Configuration
MAX_PARAGRAPH_LENGTH = 2500  # Define a maximum safe paragraph length
EN_US_MALE_VOICES = [
    #"en-US-GuyNeural",
    "en-US-SteffanNeural",
    "en-US-EricNeural",
    #"en-US-RogerNeural",
    'en-US-ChristopherNeural',
]
voice = "en-US-AndrewMultilingualNeural"

AUDIO_DIR = "episode_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)
SUBS_DIR = "episode_subtitle"
os.makedirs(SUBS_DIR, exist_ok=True)

# Store ongoing TTS tasks and status
tts_tasks = {}
tts_tasks_subs = {}

def run_async_in_thread(coroutine):
    """Runs an asyncio coroutine inside a thread-safe event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coroutine)

async def generate_subtitles(text, subtitle_path, episode_id):
    """Generates subtitles in the background."""
    try:
        update_progress(f"Starting... {subtitle_path} ...", 0)
        tts_tasks_subs[episode_id] = "Processing"

        communicate = edge_tts.Communicate(text, voice=voice)

        update_progress(f"Generating TTS Substitle {subtitle_path} ...", 10)
        submaker = edge_tts.SubMaker()

        for chunk in communicate.stream_sync():
            if chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

        with open(subtitle_path, "w", encoding="utf-8") as f:
            #print(submaker.get_srt())
            f.write(submaker.get_srt())

        """
        sub_result = []
        async for sub in communicate.stream():
            sub_result.append(sub)

        update_progress(f"Extracting Word Timing... Subtitle {subtitle_path} ...", 40)
        subtitle_data = []
        for sub in sub_result:
            if "text" in sub and "duration" in sub:
                words = sub["text"].split()
                start_time = sub["offset"] / 10000 # Convert ms → seconds no
                duration = sub["duration"] / 10000 # Convert ms → seconds no
                word_duration = duration / max(len(words), 1)

                for index, word in enumerate(words):
                    word_start = start_time + (index * word_duration)
                    word_end = word_start + word_duration
                    subtitle_data.append({
                        "word": word,
                        "start": round(word_start, 3) / 1000,
                        "end": round(word_end, 3) / 1000,
                    })

        update_progress(f"Saving TTS Subtitle as JSON {subtitle_path} ...", 70)
        with open(subtitle_path, "w", encoding="utf-8") as f:
            json.dump(subtitle_data, f, indent=2)
        """
        update_progress(f"Subtitle Generation Complete {subtitle_path} ...", 100)
        tts_tasks_subs[episode_id] = "Completed"

    except Exception as e:
        tts_tasks_subs[episode_id] = f"Failed: {str(e)}"
        print(f"❌ Error generating Subtitle: {str(e)}")
    return None

async def generate_tts_audio(text, output_path, subtitle_path, episode_id):
    """Runs TTS generation in the background and updates task status."""
    try:
        update_progress(f"Generating TTS Audio {output_path} ...", 50)
        update_progress(f"Starting... {subtitle_path} ...", 0)
        tts_tasks[episode_id] = "Processing"  # Set status to processing
        tts_tasks_subs[episode_id] = "Processing"

        communicate = edge_tts.Communicate(text, voice=voice)

        update_progress(f"Generating TTS Substitle {subtitle_path} ...", 10)
        submaker = edge_tts.SubMaker()
        with open(output_path, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        with open(subtitle_path, "w", encoding="utf-8") as file:
            file.write(submaker.get_srt())

        update_progress(f"TTS Generation Completed! {output_path}", 100)
        update_progress(f"Subtitle Generation Complete {subtitle_path} ...", 100)
        tts_tasks[episode_id] = "Completed"  # Set status to completed
        tts_tasks_subs[episode_id] = "Completed"

    except Exception as e:
        tts_tasks[episode_id] = f"Failed: {str(e)}"  # Store error message
        print(f"❌ Error generating TTS: {str(e)}")
    return None


@app.route('/tts/audio', methods=['POST'])
def generate_audio_from_text():
    """Receives text and generates TTS audio using Edge-TTS."""
    print(f"Received request with method: {request.method}")  # Debug log

    data = request.json
    text = data.get("text", "").replace("\n", " ").strip()
    episode_id = data.get("episode_id", "default")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    output_filename = f"{episode_id}.mp3"
    output_path = os.path.join(AUDIO_DIR, output_filename)
    subtitle_filename = f"{episode_id}.srt"
    subtitle_path = os.path.join(SUBS_DIR, subtitle_filename)

    print(tts_tasks.get(episode_id))
    if os.path.exists(output_path) and tts_tasks.get(episode_id) == "Completed":
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # Convert to MB
        if file_size >= 0.1:
            print(f"sending Existing {output_path} ({file_size:.2f}MB)")
            return send_file(output_path, mimetype="audio/mp3")
        print(f"⚠️ Existing file is too small ({file_size:.2f}MB). Restarting TTS.")
        os.remove(output_path)
        tts_tasks[episode_id] = "Not Found"

    if tts_tasks.get(episode_id) == "Processing":
        return jsonify({"message": "Audio is still processing", "status": "Processing"}), 202

    if tts_tasks.get(episode_id) in ["Processing", "Completed"]:
        return jsonify({"message": "Audio already being processed", "status": tts_tasks[episode_id]}), 202

    thread = threading.Thread(target=run_async_in_thread, args=(generate_tts_audio(text, output_path, subtitle_path, episode_id),))
    thread.start()

    return jsonify({"message": "Processing started", "episode_id": episode_id, "status": "Processing"}), 202

@app.route('/test_tts', methods=['GET', 'POST'])
def test_tts():
    """Simple HTML form to test TTS API"""
    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            return "No text provided.", 400

        episode_id = "test_audio"
        output_path = os.path.join(AUDIO_DIR, f"{episode_id}.mp3")

        # Run TTS synchronously (without background thread)
        asyncio.run(generate_tts_audio(text, output_path, episode_id))

        return f"""
            <p>Audio generated successfully!</p>
            <audio controls>
                <source src="/tts/audio?episode_id=test_audio" type="audio/mpeg">
                Your browser does not support the audio tag.
            </audio>
        """

    return """
        <form method="post">
            <input type="text" name="text" placeholder="Enter text" required>
            <button type="submit">Generate Audio</button>
        </form>
    """

### Generating TTS Subtitle ###
@app.route('/tts/subtitle', methods=['POST'])
def generate_substitle_from_tts():
    data = request.json
    text = data.get("text", "").replace("\n", " ").strip()
    episode_id = data.get("episode_id", "default")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    subtitle_filename = f"{episode_id}.srt"
    subtitle_path = os.path.join(SUBS_DIR, subtitle_filename)

    print(tts_tasks_subs.get(episode_id))
    if os.path.exists(subtitle_path) and tts_tasks_subs.get(episode_id) == 'Completed':
        print(f"sending Existing {subtitle_path}")
        return send_file(subtitle_path, mimetype='text/plain')

    if tts_tasks_subs.get(episode_id) == "Processing":
        return jsonify({"message": "Subtitle is still processing", "status": "Processing"}), 202

    if tts_tasks_subs.get(episode_id) in ["Processing", "Completed"]:
        return jsonify({"message": "Audio already being processed", "status": tts_tasks_subs[episode_id]}), 202

    #thread = threading.Thread(target=run_async_in_thread, args=(generate_subtitles(text, subtitle_path, episode_id),))
    #thread.start()

    return jsonify({"message": "Subtitle Processing started", "episode_id": episode_id, "status": "Processing"}), 202

@app.route('/tts/clear', methods=['POST'])
def clear_and_regenerate():
  data = request.json
  id = data.get('id', '')
  text = data.get('text', '').replace("\n", " ").strip()

  if not text:
    return jsonify({"error": "No text provided"}), 400
  if not id:
    return jsonify({'error': 'No id Provided'}), 400

  audio_name = f"{id}.mp3"
  subtitle_name = f"{id}.json"
  audio_path = os.path.join(AUDIO_DIR, audio_name)
  subtitle_path = os.path.join(SUBS_DIR, subtitle_name)

  if os.path.exists(audio_path):
    tts_tasks[id] = "Not Found"
    os.remove(audio_path)
  if os.path.exists(subtitle_path):
    tts_tasks_subs[id] = "Not Found"
    os.remove(subtitle_path)

  return jsonify({'message': "Successfully cleared, awaiting to thread process"}), 202

@app.route('/upload_pdf', methods=['POST'])
def generate_Text_from_pdf():
    update_progress("Uploading PDF...", 10)

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    pdf_path = "uploaded.pdf"
    file.save(pdf_path)

    update_progress("Extracting Text from PDF...", 30)
    text = extract_text_from_pdf(pdf_path)

    update_progress("Splitting Text into Chunks...", 60)
    text_chunks = split_text(text)

    update_progress("PDF Processing Completed!", 100)
    return jsonify({"message": "PDF processed successfully", "chunks": text_chunks})

    #we need to send the chunk data and then sending it back to the request and process it directly there the text...

def clean_text(text):
    """Fix merged words, misplaced words, and remove unnecessary line breaks."""
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Split words merged without space
    text = re.sub(r'\s+', ' ', text).strip()  # Remove excessive whitespace
    return text

def extract_text_from_pdf(pdf_path):
    """Extracts and cleans text from a PDF."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return clean_text(text)

def split_text(text, max_length=28000):
    """Splits text into chunks without cutting words."""
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 <= max_length:
            current_chunk += " " + word
        else:
            chunks.append(current_chunk.strip())
            current_chunk = word
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

if __name__ == '__main__':
    start_cloudflare_tunnel()
    app.run(host="0.0.0.0", port=port)

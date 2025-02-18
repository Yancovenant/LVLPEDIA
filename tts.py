import numpy as np
import scipy.io.wavfile as wav
from bark import generate_audio, preload_models
from flask import Flask, request, jsonify, send_file
from pyngrok import ngrok
import os

app = Flask(__name__)

ngrok_token = '2FqBCf2864FAaseGvHk0vWObQfy_4Tfvpe69KspQ9jxTzhe5w'
port = 5000
ngrok.set_auth_token(ngrok_token)

# Load Bark TTS Model
preload_models()

# Output file location
output_path = "output.wav"

@app.route('/tts', methods=['POST'])
def generate_audio_bark():
    """Receives text from Odoo, converts it to speech, and returns the audio file"""
    data = request.json
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        print(f"🎤 Generating audio for text: {text[:50]}...")  # Log only the first 50 chars

        # Generate audio using Bark
        audio_array = generate_audio(text, history_prompt="v2/en_speaker_6")

        # Ensure audio format is int16 for WAV
        audio_array = (audio_array * 32767).astype(np.int16)

        # Save to WAV
        wav.write(output_path, rate=24000, data=audio_array)

        print("✅ Audio generated successfully!")
        return send_file(output_path, mimetype="audio/wav")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Start Flask with Ngrok (Fixes the `host` issue)
if __name__ == '__main__':
    try:
      public_url = ngrok.connect(port).public_url
      print(public_url)
      app.run(port=port)
    finally:
      ngrok.disconnect(public_url=public_url)

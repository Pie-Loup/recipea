from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template
import tempfile
from whisper_cache import WhisperCacheManager
from google import genai
from prompt import get_recipe_transcription_prompt

load_dotenv()

# get model_name from args
model_name = os.getenv("WHISPER_MODEL_NAME", "base")
if not model_name:
    raise RuntimeError("WHISPER_MODEL_NAME is not set in environment variables.")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")

app = Flask(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialiser le modèle au démarrage
print(f"Initialisation du modèle Whisper '{model_name}'...")
wcm = WhisperCacheManager()
whisper_model = wcm.get_whisper_model(model_name)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        file.save(temp_audio)
        temp_path = temp_audio.name
    
    return jsonify({'message': 'File uploaded', 'temp_path': temp_path}), 200

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Sauvegarder le fichier temporairement
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        file.save(temp_audio)
        temp_path = temp_audio.name
    
    # Transcrire avec Whisper
    try:
        result = whisper_model.transcribe(temp_path, language='fr')
        text = result['text']
        
        # Nettoyer le fichier temporaire
        try:
            os.unlink(temp_path)
        except:
            pass
            
        return jsonify({'text': text})
    except Exception as e:
        # Nettoyer le fichier temporaire en cas d'erreur
        try:
            os.unlink(temp_path)
        except:
            pass
        return jsonify({'error': f'Erreur Whisper: {e}'}), 500

@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    try:
        data = request.json
        if not data or 'transcription' not in data:
            return jsonify({'error': 'No transcription provided'}), 400

        transcription = data['transcription']
        prompt = get_recipe_transcription_prompt(transcription)

        # Generate recipe using Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20"
            , contents=prompt
        )

        if response.text:
            return jsonify({'recipe': response.text})
        else:
            return jsonify({'error': 'Failed to generate recipe'}), 500

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
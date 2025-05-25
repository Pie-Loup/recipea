from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template
import tempfile
from google import genai
from prompt import get_recipe_transcription_prompt
import io
from pydub import AudioSegment

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")

app = Flask(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    try:
        # Get all audio files from the request
        audio_files = request.files.getlist('audio')
        if not audio_files:
            return jsonify({'error': 'No audio files provided'}), 400

        # Create a temporary file for the combined audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            # Initialize combined audio segment
            combined = None
            
            # Process each audio file
            for audio_file in audio_files:
                if audio_file.filename == '':
                    continue
                    
                # Read the audio file into memory
                audio_data = io.BytesIO(audio_file.read())
                try:
                    # Load the audio segment
                    segment = AudioSegment.from_file(audio_data)
                    
                    # Add to combined segment
                    if combined is None:
                        combined = segment
                    else:
                        combined += segment
                except Exception as e:
                    return jsonify({'error': f'Error processing audio file {audio_file.filename}: {str(e)}'}), 500
            
            if combined:
                # Export the combined audio to the temporary file
                combined.export(temp_audio.name, format='wav')
                
                # Upload the combined file to Gemini
                try:
                    audio_file = client.files.upload(file=temp_audio.name)

                    # Get the prompt template
                    prompt_template = get_recipe_transcription_prompt("")

                    # Generate recipe using Gemini API with file and prompt
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-preview-05-20",
                        config={"response_mime_type": "application/json"},
                        contents=[audio_file, prompt_template]
                    )

                    if response.text:
                        try:
                            # Convert Gemini's response text to a dictionary and return it directly
                            recipe_json = eval(response.text)
                            if not all(key in recipe_json for key in ['ingredients', 'steps', 'questions']):
                                return jsonify({'error': 'Invalid recipe format'}), 500
                            return jsonify(recipe_json)
                        except Exception as e:
                            return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 500
                    else:
                        return jsonify({'error': 'No response from Gemini API'}), 500

                finally:
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_audio.name)
                    except:
                        pass

    except Exception as e:
        return jsonify({'error': f'Error generating recipe: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
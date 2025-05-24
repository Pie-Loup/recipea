async function generate() {
  const prompt = document.getElementById('prompt').value;
  const res = await fetch('/generate', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({prompt})
  });
  const data = await res.json();
  document.getElementById('response').innerText = data.response;
}

async function transcribe() {
  const fileInput = document.getElementById('audioFile');
  const form = new FormData();
  form.append('audio', fileInput.files[0]);
  const res = await fetch('/transcribe', {method:'POST', body: form});
  const data = await res.json();
  const transcription = data.text;
  transcriptDiv.innerText = transcription;
  recipeBtn.disabled = false;  // Enable recipe button after transcription
}

async function generateRecipe() {
  const transcription = transcriptDiv.innerText;
  if (!transcription) return;
  
  recipeBtn.disabled = true;
  recipeDiv.innerText = "Génération de la recette en cours...";
  recipeDiv.classList.add('visible');
  
  try {
    const res = await fetch('/generate_recipe', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ transcription })
    });
    const data = await res.json();
    if (data.error) {
      throw new Error(data.error);
    }
    recipeDiv.innerText = data.recipe;
  } catch (err) {
    recipeDiv.innerText = 'Erreur lors de la génération de la recette : ' + err.message;
  } finally {
    recipeBtn.disabled = false;
  }
}

let mediaRecorder;
let audioChunks = [];
let audioBlobs = [];

const recordBtn = document.getElementById('recordBtn');
const recLabel = document.getElementById('recLabel');
const transcribeBtn = document.getElementById('transcribeBtn');
const recipeBtn = document.getElementById('recipeBtn');
const audioPlayback = document.getElementById('audioPlayback');
const transcriptDiv = document.getElementById('transcript');
const recipeDiv = document.getElementById('recipe');

let audioContext, analyser, micStream, dataArray, animationId;

function startVAD() {
  if (!micStream) return;
  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const source = audioContext.createMediaStreamSource(micStream);
  analyser = audioContext.createAnalyser();
  analyser.fftSize = 256;
  dataArray = new Uint8Array(analyser.frequencyBinCount);
  source.connect(analyser);
  function detect() {
    analyser.getByteTimeDomainData(dataArray);
    let max = 0;
    for (let i = 0; i < dataArray.length; i++) {
      max = Math.max(max, Math.abs(dataArray[i] - 128));
    }
    if (max > 15) {
      recordBtn.classList.add('recording');
    } else {
      recordBtn.classList.remove('recording');
    }
    animationId = requestAnimationFrame(detect);
  }
  detect();
}

function stopVAD() {
  if (animationId) cancelAnimationFrame(animationId);
  if (audioContext) audioContext.close();
  recordBtn.classList.remove('recording');
}

recordBtn.addEventListener('click', async () => {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    stopVAD();
    recLabel.textContent = 'Enregistrer';
  } else {
    audioChunks = [];
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(micStream);
      mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
      mediaRecorder.onstop = () => {
        const newBlob = new Blob(audioChunks, { type: 'audio/wav' });
        audioBlobs.push(newBlob);
        // Crée une playlist simple
        if (audioBlobs.length === 1) {
          audioPlayback.src = URL.createObjectURL(newBlob);
        } else {
          // Fusionne les blobs pour la lecture (optionnel, sinon playlist)
          // Ici, on affiche la liste
          let list = '';
          audioBlobs.forEach((b, i) => {
            const url = URL.createObjectURL(b);
            list += `<audio controls src="${url}" style="width:100%;margin-bottom:8px;"></audio>`;
          });
          audioPlayback.classList.add('hidden');
          transcriptDiv.innerHTML = list;
        }
        transcribeBtn.disabled = false;
      };
      mediaRecorder.start();
      recLabel.textContent = 'Arrêter';
      transcribeBtn.disabled = true;
      audioPlayback.classList.add('hidden');
      transcriptDiv.textContent = '';
      startVAD();
    } catch (err) {
      alert('Erreur lors de l\'accès au micro : ' + err.message);
    }
  }
});

transcribeBtn.addEventListener('click', async () => {
  if (!audioBlobs.length) return;
  transcribeBtn.disabled = true;
  transcriptDiv.textContent = 'Transcription en cours...';
  // Fusionne tous les blobs en un seul fichier audio
  const mergedBlob = new Blob(audioBlobs, { type: 'audio/wav' });
  const form = new FormData();
  form.append('file', mergedBlob, 'audio.wav');
  const res = await fetch('/transcribe', { method: 'POST', body: form });
  const data = await res.json();
  if (data.text) {
    transcriptDiv.textContent = data.text;
    recipeBtn.disabled = false;  // Enable recipe button when we have text
  } else if (data.temp_path) {
    transcriptDiv.textContent = 'Fichier audio reçu. (Transcription à implémenter côté serveur)';
  } else {
    transcriptDiv.textContent = data.error || 'Erreur lors de la transcription.';
  }
  transcribeBtn.disabled = false;
});

recipeBtn.addEventListener('click', generateRecipe);

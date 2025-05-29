let mediaRecorder;
let audioChunks = [];
let audioBlobs = [];

const recordBtn = document.getElementById('recordBtn');
const recLabel = document.getElementById('recLabel');
const recipeBtn = document.getElementById('recipeBtn');
const audioPlayback = document.getElementById('audioPlayback');
const audioList = document.getElementById('audioList');
const recipeDiv = document.getElementById('recipe');

let audioContext, analyser, micStream, dataArray, animationId;

function startVAD() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    dataArray = new Uint8Array(analyser.frequencyBinCount);
  }

  const source = audioContext.createMediaStreamSource(micStream);
  source.connect(analyser);
  
  function draw() {
    analyser.getByteTimeDomainData(dataArray);
    let sum = 0;
    for(let i = 0; i < dataArray.length; i++) {
      sum += Math.abs(dataArray[i] - 128);
    }
    let average = sum / dataArray.length;
    
    recordBtn.style.transform = `scale(${1 + average/1000})`;
    animationId = requestAnimationFrame(draw);
  }
  draw();
}

function stopVAD() {
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  recordBtn.style.transform = 'scale(1)';
}

recordBtn.addEventListener('click', async () => {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    stopVAD();
    recLabel.textContent = 'Enregistrer';
    recordBtn.classList.remove('recording');
  } else {
    audioChunks = [];
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordBtn.classList.add('recording');
      
      mediaRecorder = new MediaRecorder(micStream);
      mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
      mediaRecorder.onstop = () => {
        const newBlob = new Blob(audioChunks, { type: 'audio/wav' });
        audioBlobs.push(newBlob);
        
        // Create a playlist of recorded audio segments
        let list = '';
        audioBlobs.forEach((blob, i) => {
          const url = URL.createObjectURL(blob);
          list += `<audio controls src="${url}" style="width:100%;margin-bottom:8px;"></audio>`;
        });
        audioList.innerHTML = list;
        recipeBtn.disabled = false;
        recipeBtn.classList.add('ready');
      };
      
      mediaRecorder.start();
      recLabel.textContent = 'Arrêter';
      startVAD();
    } catch (err) {
      alert('Erreur lors de l\'accès au micro : ' + err.message);
    }
  }
});

async function generateRecipe() {
  if (!audioBlobs.length) return;
  
  recipeBtn.disabled = true;
  recipeBtn.classList.remove('ready');
  recipeDiv.innerHTML = "<p>Génération de la recette en cours...</p>";
  recipeDiv.classList.add('visible');
  
  try {
    const formData = new FormData();
    audioBlobs.forEach((blob, i) => {
      formData.append('audio', blob, `audio${i+1}.wav`);
    });
    
    const res = await fetch('/generate_recipe_from_voice', {
      method: 'POST',
      body: formData
    });
    
    const data = await res.json();
    if (data.error) {
      throw new Error(data.error);
    }
    
    if (!data.is_recipe) {
      recipeDiv.innerHTML = `
        <div class="recipe-section" style="text-align: center; color: #666;">
          <p>Désolé, je ne peux pas créer une recette à partir de cet enregistrement. Pourriez-vous réessayer en décrivant la recette plus en détail ?</p>
        </div>
      `;
      
      // Reset audio recordings
      audioBlobs = [];
      audioList.innerHTML = '';
      recipeBtn.disabled = true;
      return;
    }

    // Format the recipe data
    let html = '';
    
    // Title section
    html += `
      <div class="recipe-section">
        <h2 style="color: #1976d2; margin-bottom: 24px; text-align: center;">${data.title || 'Recette'}</h2>
      </div>
    `;
    
    // Ingredients section
    if (data.ingredients && data.ingredients.length > 0) {
      html += `
        <div class="recipe-section">
          <h3>Ingrédients</h3>
          <ul class="recipe-list">
            ${data.ingredients.map(ingredient => `<li>${ingredient}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    
    // Steps section
    if (data.steps && data.steps.length > 0) {
      html += `
        <div class="recipe-section">
          <h3>Étapes de préparation</h3>
          <ul class="recipe-list">
            ${data.steps.map(step => `<li>${step}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    
    // Questions section
    if (data.questions && data.questions.length > 0) {
      html += `
        <div class="recipe-section">
          <h3>Questions</h3>
          <ul class="questions-list">
            ${data.questions.map(question => `<li>${question}</li>`).join('')}
          </ul>
        </div>
      `;
    }
    
    recipeDiv.innerHTML = html;
  } catch (err) {
    recipeDiv.innerHTML = `<p class="error">Erreur lors de la génération de la recette : ${err.message}</p>`;
  } finally {
    recipeBtn.disabled = false;
  }
}

recipeBtn.addEventListener('click', generateRecipe);

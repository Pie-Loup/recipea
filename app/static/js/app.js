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
  
  // Initialize async recipe generator
  const generator = new AsyncRecipeGenerator();
  
  try {
    // Convert blobs to files for the async generator
    const audioFiles = audioBlobs.map((blob, i) => 
      new File([blob], `audio${i+1}.wav`, { type: 'audio/wav' })
    );
    
    // Generate recipe with progress updates
    const data = await generator.generateFromVoice(audioFiles, (status) => {
      recipeDiv.innerHTML = `<p>${status}</p>`;
    });
    
    // Use RecipeManager to handle the recipe display and setup
    if (window.recipeManager) {
      window.recipeManager.handleRecipeGeneration(data);
    } else {
      console.warn('RecipeManager not available, falling back to basic display');
      recipeDiv.innerHTML = `<p class="error">RecipeManager non disponible</p>`;
    }
    
    // Reset audio recordings if no valid recipe
    if (!data.is_recipe) {
      audioBlobs = [];
      audioList.innerHTML = '';
      recipeBtn.disabled = true;
    }
    
  } catch (err) {
    recipeDiv.innerHTML = `<p class="error">Erreur lors de la génération de la recette : ${err.message}</p>`;
  } finally {
    recipeBtn.disabled = false;
  }
}

recipeBtn.addEventListener('click', generateRecipe);

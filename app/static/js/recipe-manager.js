/**
 * Recipe Manager
 * Handles common recipe functionality across different generation methods
 */

class RecipeManager {
    constructor() {
        this.currentRecipe = null;
        this.asyncRecipeGenerator = new AsyncRecipeGenerator();
    }

    /**
     * Display recipe content in a consistent format
     */
    displayRecipe(data, containerId = 'recipe') {
        const recipeDiv = document.getElementById(containerId);
        
        if (!data.is_recipe) {
            this.displayNonRecipeMessage(recipeDiv, data.origin || 'unknown');
            return false;
        }

        // Store current recipe
        this.currentRecipe = data;

        // Build recipe HTML
        let html = this.buildRecipeHTML(data);
        
        recipeDiv.innerHTML = html;
        recipeDiv.classList.add('visible');
        
        return true;
    }

    /**
     * Display message when content is not a recipe
     */
    displayNonRecipeMessage(container, origin) {
        let message = '';
        switch (origin) {
            case 'text':
                message = 'Désolé, je ne peux pas créer une recette à partir de ce texte. Pourriez-vous me donner plus de détails sur la recette que vous souhaitez ?';
                break;
            case 'photo':
                message = 'Désolé, je ne peux pas identifier de recette dans cette photo. Pourriez-vous essayer avec une autre photo ?';
                break;
            case 'voice':
                message = 'Désolé, je ne peux pas créer une recette à partir de cet enregistrement. Pourriez-vous réessayer en décrivant la recette plus en détail ?';
                break;
            default:
                message = 'Désolé, je ne peux pas créer une recette à partir de ce contenu.';
        }

        container.innerHTML = `
            <div class="recipe-section error-message">
                <p>${message}</p>
            </div>
        `;
        container.classList.add('visible');
    }

    /**
     * Build recipe HTML content
     */
    buildRecipeHTML(data) {
        let html = '';
        
        // Title section
        html += `
            <div class="recipe-section">
                <h2 style="color: #1976d2; margin-bottom: 24px; text-align: center;">${data.title || 'Recette'}</h2>
            </div>
        `;
        
        // Recipe info section (new structured fields)
        let recipeInfoItems = [];
        if (data.preparation_time) {
            recipeInfoItems.push(`<span class="recipe-info-item">⏰ Préparation: ${data.preparation_time}</span>`);
        }
        if (data.cooking_time) {
            recipeInfoItems.push(`<span class="recipe-info-item">🔥 Cuisson: ${data.cooking_time}</span>`);
        }
        if (data.quantity) {
            recipeInfoItems.push(`<span class="recipe-info-item">👥 Quantité: ${data.quantity}</span>`);
        }
        if (data.difficulty) {
            const difficultyStars = '⭐'.repeat(data.difficulty);
            recipeInfoItems.push(`<span class="recipe-info-item">📊 Difficulté: ${difficultyStars} (${data.difficulty}/4)</span>`);
        }
        
        if (recipeInfoItems.length > 0) {
            html += `
                <div class="recipe-section recipe-info">
                    <div class="recipe-info-grid">
                        ${recipeInfoItems.join('')}
                    </div>
                </div>
            `;
        }
        
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
        
        // Other elements section
        if (data.other_elements && data.other_elements.length > 0) {
            html += `
                <div class="recipe-section">
                    <h3>Autres éléments</h3>
                    <ul class="other-elements-list">
                        ${data.other_elements.map(element => `<li>${element}</li>`).join('')}
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
        
        return html;
    }

    /**
     * Setup update functionality
     */
    setupUpdateFunctionality(updatePromptId = 'update-prompt', updateBtnId = 'updateBtn') {
        const updatePrompt = document.getElementById(updatePromptId);
        const updateBtn = document.getElementById(updateBtnId);

        if (!updatePrompt || !updateBtn) return;

        // Enable/disable update button based on input
        updatePrompt.addEventListener('input', () => {
            updateBtn.disabled = !updatePrompt.value.trim();
        });

        // Update recipe functionality
        updateBtn.addEventListener('click', async () => {
            const text = updatePrompt.value.trim();
            if (!text || !this.currentRecipe) return;

            updateBtn.disabled = true;
            updateBtn.textContent = 'Modification en cours...';

            try {
                const data = await this.asyncRecipeGenerator.updateRecipe(this.currentRecipe, text, (progress) => {
                    updateBtn.textContent = 'Modification en cours...';
                });

                this.currentRecipe = data;
                this.displayRecipe(data);
                updatePrompt.value = '';
                this.showSaveButton();

            } catch (error) {
                alert('Erreur: ' + error.message);
            } finally {
                updateBtn.disabled = false;
                updateBtn.textContent = 'Modifier la recette';
            }
        });
    }

    /**
     * Setup save functionality
     */
    setupSaveFunctionality(saveBtnId = 'saveBtn', origin = 'text_ia') {
        const saveBtn = document.getElementById(saveBtnId);
        
        if (!saveBtn) return;

        saveBtn.addEventListener('click', async () => {
            if (!this.currentRecipe) return;

            saveBtn.disabled = true;
            saveBtn.textContent = 'Sauvegarde en cours...';

            try {
                const recipeToSave = {
                    title: this.currentRecipe.title,
                    ingredients: this.currentRecipe.ingredients,
                    steps: this.currentRecipe.steps,
                    other_elements: this.currentRecipe.other_elements || [],
                    preparation_time: this.currentRecipe.preparation_time,
                    cooking_time: this.currentRecipe.cooking_time,
                    quantity: this.currentRecipe.quantity,
                    difficulty: this.currentRecipe.difficulty,
                    origin: origin
                };

                const response = await fetch('/save_recipe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(recipeToSave)
                });

                const data = await response.json();
                if (data.error) {
                    throw new Error(data.error);
                }

                alert('Votre recette a été sauvegardée avec succès !');
                window.location.href = '/feed';

            } catch (error) {
                alert('Erreur lors de la sauvegarde : ' + error.message);
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Poster ma sauce';
            }
        });
    }

    /**
     * Show save button
     */
    showSaveButton(saveBtnId = 'saveBtn') {
        const saveBtn = document.getElementById(saveBtnId);
        if (saveBtn) {
            saveBtn.classList.remove('hidden');
        }
    }

    /**
     * Show update input section and save button
     */
    showUpdateSection(initialInputId = 'initial-input', updateInputId = 'update-input') {
        const initialInput = document.getElementById(initialInputId);
        const updateInput = document.getElementById(updateInputId);

        if (initialInput) {
            initialInput.classList.add('hidden');
        }
        if (updateInput) {
            updateInput.classList.remove('hidden');
        }
        this.showSaveButton();
    }

    /**
     * Hide update section and show initial input
     */
    hideUpdateSection(initialInputId = 'initial-input', updateInputId = 'update-input') {
        const initialInput = document.getElementById(initialInputId);
        const updateInput = document.getElementById(updateInputId);

        if (initialInput) {
            initialInput.classList.remove('hidden');
        }
        if (updateInput) {
            updateInput.classList.add('hidden');
        }
    }

    /**
     * Complete setup for recipe generation page
     */
    setupRecipeGenerator(origin = 'text_ia') {
        // Setup update functionality
        this.setupUpdateFunctionality();
        
        // Setup save functionality
        this.setupSaveFunctionality('saveBtn', origin);
    }

    /**
     * Handle successful recipe generation
     */
    handleRecipeGeneration(data, origin = 'text_ia') {
        const isRecipe = this.displayRecipe(data);
        
        if (isRecipe) {
            this.showUpdateSection();
            // Clear any existing update prompt
            const updatePrompt = document.getElementById('update-prompt');
            if (updatePrompt) {
                updatePrompt.value = '';
            }
        } else {
            this.hideUpdateSection();
        }
        
        return isRecipe;
    }
}

// Export for use in other scripts
window.RecipeManager = RecipeManager;

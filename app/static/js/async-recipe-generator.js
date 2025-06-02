/**
 * Async Recipe Generator
 * Handles asynchronous recipe generation with polling
 */

class AsyncRecipeGenerator {
    constructor() {
        this.pollingInterval = 2000; // Poll every 2 seconds
        this.maxPollingTime = 120000; // Max 2 minutes of polling
    }

    /**
     * Poll task status until completion or failure
     */
    async pollTaskStatus(taskId) {
        const startTime = Date.now();
        
        return new Promise((resolve, reject) => {
            const interval = setInterval(async () => {
                try {
                    // Check if we've exceeded max polling time
                    if (Date.now() - startTime > this.maxPollingTime) {
                        clearInterval(interval);
                        reject(new Error('Timeout: La génération prend trop de temps'));
                        return;
                    }

                    const response = await fetch(`/api/task/${taskId}`);
                    if (!response.ok) {
                        throw new Error('Erreur lors de la vérification du statut');
                    }

                    const task = await response.json();
                    
                    if (task.status === 'completed') {
                        clearInterval(interval);
                        resolve(task.result);
                    } else if (task.status === 'failed') {
                        clearInterval(interval);
                        reject(new Error(task.error || 'Erreur lors de la génération'));
                    }
                    // If status is 'pending', continue polling
                    
                } catch (error) {
                    clearInterval(interval);
                    reject(error);
                }
            }, this.pollingInterval);
        });
    }

    /**
     * Generate recipe from voice with async handling
     */
    async generateFromVoice(audioFiles, onProgress = null) {
        try {
            if (onProgress) onProgress('Envoi de l\'audio...');

            const formData = new FormData();
            for (const audioFile of audioFiles) {
                formData.append('audio', audioFile);
            }

            const response = await fetch('/generate_recipe_from_voice', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Erreur lors de l\'envoi');
            }

            const { task_id } = await response.json();
            
            if (onProgress) onProgress('Génération en cours...');
            
            return await this.pollTaskStatus(task_id);
            
        } catch (error) {
            throw new Error(`Erreur: ${error.message}`);
        }
    }

    /**
     * Generate recipe from photo with async handling
     */
    async generateFromPhoto(photoFile, onProgress = null) {
        try {
            if (onProgress) onProgress('Envoi de la photo...');

            const formData = new FormData();
            formData.append('photo', photoFile);

            const response = await fetch('/generate_recipe_from_photo', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Erreur lors de l\'envoi');
            }

            const { task_id } = await response.json();
            
            if (onProgress) onProgress('Génération en cours...');
            
            return await this.pollTaskStatus(task_id);
            
        } catch (error) {
            throw new Error(`Erreur: ${error.message}`);
        }
    }

    /**
     * Generate recipe from text with async handling
     */
    async generateFromText(text, onProgress = null) {
        try {
            if (onProgress) onProgress('Envoi du texte...');

            const response = await fetch('/generate_recipe_from_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Erreur lors de l\'envoi');
            }

            const { task_id } = await response.json();
            
            if (onProgress) onProgress('Génération en cours...');
            
            return await this.pollTaskStatus(task_id);
            
        } catch (error) {
            throw new Error(`Erreur: ${error.message}`);
        }
    }

    /**
     * Update recipe with async handling
     */
    async updateRecipe(recipe, userComments, onProgress = null) {
        try {
            if (onProgress) onProgress('Envoi des modifications...');

            const response = await fetch('/update_recipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    recipe: recipe,
                    user_comments: userComments 
                })
            });

            if (!response.ok) {
                throw new Error('Erreur lors de l\'envoi');
            }

            const { task_id } = await response.json();
            
            if (onProgress) onProgress('Modification en cours...');
            
            return await this.pollTaskStatus(task_id);
            
        } catch (error) {
            throw new Error(`Erreur: ${error.message}`);
        }
    }
}

// Export for use in other scripts
window.AsyncRecipeGenerator = AsyncRecipeGenerator;

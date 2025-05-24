import os
import whisper

# Utiliser un répertoire de cache persistant dans le conteneur Docker

class WhisperCacheManager(Exception):

    WHISPER_CACHE_DIR = os.environ.get("WHISPER_CACHE_DIR", "/app/whisper_cache")


    def ensure_cache_directory(self):
        """Créer le répertoire de cache s'il n'existe pas"""
        if not os.path.exists(self.WHISPER_CACHE_DIR):
            os.makedirs(self.WHISPER_CACHE_DIR, exist_ok=True)
            print(f"Répertoire de cache créé : {self.WHISPER_CACHE_DIR}")


    def is_model_cached(self, model_name):
        """Vérifier si le modèle est déjà en cache de manière plus robuste"""
        try:
            # Méthode 1: Vérifier les fichiers du modèle directement
            model_file_patterns = [
                f"{model_name}.pt",
                f"whisper-{model_name}.pt"
            ]
            
            for pattern in model_file_patterns:
                model_path = os.path.join(self.WHISPER_CACHE_DIR, pattern)
                if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
                    print(f"Modèle {model_name} trouvé en cache : {model_path}")
                    return True
            
            # Méthode 2: Vérifier la structure de cache Hugging Face si applicable
            hf_cache_path = os.path.join(self.WHISPER_CACHE_DIR, f'models--openai--whisper-{model_name}')
            if os.path.exists(hf_cache_path):
                snapshots_dir = os.path.join(hf_cache_path, 'snapshots')
                if os.path.exists(snapshots_dir):
                    for snapshot_dir in os.listdir(snapshots_dir):
                        snapshot_path = os.path.join(snapshots_dir, snapshot_dir)
                        if os.path.isdir(snapshot_path):
                            # Vérifier la présence de fichiers modèle
                            model_files = [f for f in os.listdir(snapshot_path) 
                                        if f.endswith(('.bin', '.pt', '.pth', '.safetensors'))]
                            if model_files:
                                print(f"Modèle {model_name} trouvé en cache HF : {snapshot_path}")
                                return True
            
            return False
        except Exception as e:
            print(f"Erreur lors de la vérification du cache : {e}")
            return False


    def get_whisper_model(self, model_name='base'):  
        """Charger le modèle Whisper avec gestion optimisée du cache"""
        
        self.ensure_cache_directory()
        
        if self.is_model_cached(model_name):
            print(f'Modèle Whisper {model_name} déjà en cache, chargement...')
        else:
            print(f'Modèle Whisper {model_name} non trouvé en cache, téléchargement...')
        
        try:
            # Charger le modèle avec le répertoire de cache spécifié
            model = whisper.load_model(model_name, download_root=self.WHISPER_CACHE_DIR)
            print(f'Modèle Whisper {model_name} chargé avec succès')
            return model
        except Exception as e:
            print(f'Erreur lors du chargement du modèle : {e}')
            raise
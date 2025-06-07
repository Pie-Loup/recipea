// theme-color.js - Applique automatiquement la theme-color sauce sur toutes les pages

(function() {
    // Fonction pour appliquer la theme-color
    function applyThemeColor() {
        // Chercher s'il existe déjà une meta theme-color
        let themeColorMeta = document.querySelector('meta[name="theme-color"]');
        
        if (themeColorMeta) {
            // Si elle existe, mettre à jour sa valeur
            themeColorMeta.setAttribute('content', '#ffffff');
        } else {
            // Si elle n'existe pas, la créer
            themeColorMeta = document.createElement('meta');
            themeColorMeta.setAttribute('name', 'theme-color');
            themeColorMeta.setAttribute('content', '#ffffff');
            document.head.appendChild(themeColorMeta);
        }
    }
    
    // Appliquer immédiatement
    applyThemeColor();
    
    // Appliquer aussi quand le DOM est chargé (sécurité)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyThemeColor);
    }
})();

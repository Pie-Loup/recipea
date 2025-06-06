// Gestion du splash screen pour PWA
(function() {
    'use strict';
    
    // Créer et afficher le splash screen pour iOS
    function createSplashScreen() {
        // Vérifier si on est sur iOS et en mode standalone (PWA installée)
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        const isStandalone = window.navigator.standalone === true;
        
        if (isIOS && isStandalone) {
            const splash = document.createElement('div');
            splash.className = 'ios-splash';
            splash.style.backgroundColor = '#E0322C';
            splash.innerHTML = `
                <div style="text-align: center;">
                    <img src="/static/logo-splash.svg" alt="sauce" style="width: 120px; height: 120px; margin-bottom: 20px;">
                    <div style="color: #ffffff; font-family: 'Fredoka', Arial, sans-serif; font-size: 2.5rem; font-weight: 600;">sauce</div>
                </div>
            `;
            
            document.body.appendChild(splash);
            
            // Masquer le splash screen après le chargement
            window.addEventListener('load', function() {
                setTimeout(function() {
                    splash.classList.add('fade-out');
                    setTimeout(function() {
                        if (splash.parentNode) {
                            splash.parentNode.removeChild(splash);
                        }
                    }, 500);
                }, 1000);
            });
        }
    }
    
    // Mettre à jour la couleur de thème dynamiquement
    function updateThemeColor() {
        const themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (themeColorMeta) {
            themeColorMeta.content = '#E0322C';
        } else {
            const meta = document.createElement('meta');
            meta.name = 'theme-color';
            meta.content = '#E0322C';
            document.head.appendChild(meta);
        }
        
        // Également pour Windows
        const msThemeColorMeta = document.querySelector('meta[name="msapplication-TileColor"]');
        if (msThemeColorMeta) {
            msThemeColorMeta.content = '#E0322C';
        }
    }
    
    // Exécuter au chargement du DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            createSplashScreen();
            updateThemeColor();
        });
    } else {
        createSplashScreen();
        updateThemeColor();
    }
})();

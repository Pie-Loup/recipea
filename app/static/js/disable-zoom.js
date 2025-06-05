// Désactive le zoom/pinch-to-zoom sur les appareils mobiles
(function() {
    'use strict';
    
    // Désactiver le zoom via gestionnaire d'événements
    document.addEventListener('gesturestart', function(e) {
        e.preventDefault();
    });
    
    document.addEventListener('gesturechange', function(e) {
        e.preventDefault();
    });
    
    document.addEventListener('gestureend', function(e) {
        e.preventDefault();
    });
    
    // Empêcher le zoom avec les événements tactiles
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
    
    // Empêcher le zoom avec la molette de la souris
    document.addEventListener('wheel', function(e) {
        if (e.ctrlKey) {
            e.preventDefault();
        }
    }, { passive: false });
    
    // Empêcher le zoom via les raccourcis clavier
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '-' || e.key === '0')) {
            e.preventDefault();
        }
    });
    
    // Pour iOS Safari - empêcher le zoom via touch
    let isScaling = false;
    document.addEventListener('touchstart', function(e) {
        if (e.touches.length > 1) {
            isScaling = true;
        }
    });
    
    document.addEventListener('touchmove', function(e) {
        if (isScaling || e.touches.length > 1) {
            e.preventDefault();
        }
    }, { passive: false });
    
    document.addEventListener('touchend', function(e) {
        isScaling = false;
    });
    
    // Empêcher le double-tap zoom sur iOS
    let lastTouchTime = 0;
    document.addEventListener('touchstart', function(e) {
        const currentTime = new Date().getTime();
        const tapLength = currentTime - lastTouchTime;
        if (tapLength < 500 && tapLength > 0) {
            e.preventDefault();
        }
        lastTouchTime = currentTime;
    });
})();

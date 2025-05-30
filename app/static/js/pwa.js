// PWA Installation and Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            // Register service worker only (without push notifications)
            await registerServiceWorker();
            console.log('Service Worker initialized');
        } catch (err) {
            console.error('Service Worker initialization failed: ', err);
        }
    });
}

// PWA Installation
let deferredPrompt;
const pwaPrompt = document.getElementById('pwaPrompt');

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Check if user has already dismissed or installed
    const pwaInstalled = localStorage.getItem('pwaInstalled');
    if (!pwaInstalled) {
        pwaPrompt.style.display = 'block';
    }
});

// Installation must be triggered by user gesture
async function installPWA() {
    if (deferredPrompt) {
        // Show the install prompt
        deferredPrompt.prompt();
        
        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            console.log('User accepted the PWA installation');
            localStorage.setItem('pwaInstalled', 'true');
        }
        
        // Clear the deferredPrompt variable
        deferredPrompt = null;
    }
    // Hide the prompt regardless of outcome
    pwaPrompt.style.display = 'none';
}

// Handle successful installation
window.addEventListener('appinstalled', (evt) => {
    localStorage.setItem('pwaInstalled', 'true');
    pwaPrompt.style.display = 'none';
});

// Check if app is launched in standalone mode (already installed)
if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
    localStorage.setItem('pwaInstalled', 'true');
    pwaPrompt.style.display = 'none';
}

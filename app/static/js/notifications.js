// Function to urlBase64ToUint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// Check if push notifications are supported
async function checkPushNotificationSupport() {
    // Détecter iOS
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
        throw new Error('iOS_DEVICE');
    }
    
    if (!('serviceWorker' in navigator)) {
        throw new Error('Service Workers are not supported');
    }
    
    if (!('PushManager' in window)) {
        throw new Error('Push notifications are not supported');
    }
    
    if (!('Notification' in window)) {
        throw new Error('Notifications are not supported');
    }
}

// Request notification permission
async function requestNotificationPermission() {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
        throw new Error('Notification permission denied');
    }
    return permission;
}

// Subscribe to push notifications
async function subscribeToPushNotifications() {
    try {
        await checkPushNotificationSupport();
        await requestNotificationPermission();

        // Get service worker registration
        const registration = await navigator.serviceWorker.ready;

        // Use VAPID key from the window object (passed from Flask)
        const publicKey = window.VAPID_PUBLIC_KEY;

        // Convert VAPID key to Uint8Array
        const convertedVapidKey = urlBase64ToUint8Array(publicKey);

        // Get push subscription
        let subscription = await registration.pushManager.getSubscription();

        // If no subscription exists, create one
        if (!subscription) {
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
        }

        // Send subscription to server
        await fetch('/push/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subscription: subscription
            })
        });

        return subscription;
    } catch (error) {
        console.error('Error subscribing to push notifications:', error);
        throw error;
    }
}

// Initialize push notifications when user is logged in
async function initializePushNotifications() {
    try {
        const subscription = await subscribeToPushNotifications();
        console.log('Successfully subscribed to push notifications');
    } catch (error) {
        console.error('Failed to initialize push notifications:', error);
        
        // Si c'est un appareil iOS, suggérer l'installation de la PWA
        if (error.message === 'iOS_DEVICE') {
            // Vérifier si l'app n'est pas déjà installée
            if (!window.matchMedia('(display-mode: standalone)').matches) {
                const pwaPrompt = document.getElementById('pwaPrompt');
                if (pwaPrompt) {
                    pwaPrompt.innerHTML = `
                        📱 Pour une meilleure expérience, installez sauce sur votre iPhone !
                        <button onclick="showIOSInstallInstructions()">Comment faire ?</button>
                        <button onclick="document.getElementById('pwaPrompt').style.display = 'none'">Plus tard</button>
                    `;
                    pwaPrompt.style.display = 'block';
                }
            }
        }
    }
}

// Fonction pour montrer les instructions d'installation sur iOS
function showIOSInstallInstructions() {
    const modal = document.createElement('div');
    modal.className = 'ios-install-modal';
    modal.innerHTML = `
        <div class="ios-install-content">
            <h3>Installation sur iPhone/iPad</h3>
            <ol>
                <li>Appuyez sur le bouton de partage <span class="ios-icon">⎙</span></li>
                <li>Faites défiler et appuyez sur "Sur l'écran d'accueil"</li>
                <li>Appuyez sur "Ajouter"</li>
            </ol>
            <button onclick="this.parentElement.parentElement.remove()">Fermer</button>
        </div>
    `;
    document.body.appendChild(modal);
}

// Vérifie si le navigateur supporte les notifications push
async function checkNotificationSupport() {
    console.log('Checking Service Worker support...', 'serviceWorker' in navigator);
    if (!('serviceWorker' in navigator)) {
        throw new Error('Service Workers are not supported');
    }
    console.log('Checking PushManager support...', 'PushManager' in window);
    if (!('PushManager' in window)) {
        throw new Error('Push notifications are not supported');
    }
    console.log('Current notification permission:', Notification.permission);
    if (Notification.permission === 'denied') {
        throw new Error('Push notifications are blocked');
    }
}

// Convertit une clé VAPID base64url en Uint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// Enregistre le service worker
async function registerServiceWorker() {
    console.log('=== Registering service worker ===');
    try {
        const registration = await navigator.serviceWorker.register('/static/sw.js');
        console.log('Service Worker registration successful with scope:', registration.scope);
        
        // Attendre que le service worker soit activé
        if (registration.active) {
            console.log('Service Worker already active');
        } else {
            console.log('Waiting for Service Worker to activate...');
            await new Promise((resolve) => {
                registration.addEventListener('activate', (event) => {
                    console.log('Service Worker activated!');
                    resolve();
                });
            });
        }
        
        return registration;
    } catch (error) {
        console.error('Service Worker registration failed:', error);
        throw error;
    }
}

// S'abonne aux notifications push
// Fonction d'initialisation appelée au chargement de la page
async function initializePushNotifications() {
    console.log('=== Initializing push notifications ===');
    try {
        if (!window.VAPID_PUBLIC_KEY) {
            throw new Error('VAPID public key not found in window object');
        }
        console.log('VAPID key present:', window.VAPID_PUBLIC_KEY);
        
        const result = await subscribeToPushNotifications();
        console.log('Push notifications initialized:', result);
        return result;
    } catch (error) {
        console.error('Failed to initialize push notifications:', error);
        throw error;
    }
}

async function subscribeToPushNotifications() {
    try {
        console.log('=== Starting subscription process ===');
        console.log('Checking notification support...');
        await checkNotificationSupport();
        console.log('Notification support OK');
        
        // Demander la permission pour les notifications si ce n'est pas déjà fait
        console.log('Requesting notification permission...');
        const permission = await Notification.requestPermission();
        console.log('Permission status:', permission);
        if (permission !== 'granted') {
            throw new Error('Notification permission not granted');
        }

        // Enregistrer d'abord le service worker
        console.log('Registering service worker...');
        let registration = await registerServiceWorker();
        
        // Essayer d'utiliser une registration existante si disponible
        const existingRegistration = await navigator.serviceWorker.getRegistration('/static/sw.js');
        if (existingRegistration && existingRegistration.active) {
            console.log('Using existing service worker registration');
            registration = existingRegistration;
        }
        
        console.log('Waiting for service worker to be ready...');
        
        // S'assurer que le service worker est ready
        if (!registration.active) {
            console.log('Service worker not active, waiting...');
            await new Promise(resolve => {
                if (registration.installing) {
                    registration.installing.addEventListener('statechange', function() {
                        if (this.state === 'activated') {
                            console.log('Service worker is now activated');
                            resolve();
                        }
                    });
                } else if (registration.waiting) {
                    registration.waiting.addEventListener('statechange', function() {
                        if (this.state === 'activated') {
                            console.log('Service worker is now activated');
                            resolve();
                        }
                    });
                } else {
                    // Fallback si aucun service worker en attente
                    setTimeout(resolve, 1000);
                }
            });
        }
        
        // Attendre encore un peu pour s'assurer que tout est prêt
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Vérifier si une souscription existe déjà
        console.log('Checking for existing subscription...');
        const existingSubscription = await registration.pushManager.getSubscription();
        if (existingSubscription) {
            console.log('Found existing push subscription, unsubscribing first...');
            try {
                await existingSubscription.unsubscribe();
                console.log('Successfully unsubscribed from existing subscription');
            } catch (unsubError) {
                console.warn('Failed to unsubscribe from existing subscription:', unsubError);
            }
        } else {
            console.log('No existing subscription found');
        }

        // Si pas de souscription existante, en créer une nouvelle
        console.log('Getting VAPID public key from window...');
        const publicKey = window.VAPID_PUBLIC_KEY;
        if (!publicKey) {
            throw new Error('VAPID public key not found');
        }
        console.log('Got VAPID public key:', publicKey);
        console.log('Service worker registered');
        
        // Convertir la clé VAPID en format approprié
        console.log('Original VAPID key length:', publicKey.length);
        console.log('Original VAPID key first 20 chars:', publicKey.substring(0, 20));
        
        const applicationServerKey = urlBase64ToUint8Array(publicKey);
        console.log('Converted VAPID key to Uint8Array, length:', applicationServerKey.length);
        console.log('Expected length should be 65 bytes for P-256 key');
        console.log('First few bytes:', Array.from(applicationServerKey.slice(0, 10)));
        console.log('Last few bytes:', Array.from(applicationServerKey.slice(-10)));
        
        // Vérifier que la clé a la bonne longueur
        if (applicationServerKey.length !== 65) {
            console.error('VAPID key has wrong length:', applicationServerKey.length, 'expected 65');
            throw new Error(`VAPID key has wrong length: ${applicationServerKey.length}, expected 65`);
        }
        
        // Créer la souscription
        const subscribeOptions = {
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
        };
        
        console.log('Subscribing to push notifications with options:', {
            userVisibleOnly: subscribeOptions.userVisibleOnly,
            applicationServerKeyLength: subscribeOptions.applicationServerKey.length
        });
        console.log('Registration pushManager available:', !!registration.pushManager);
        
        let subscription;
        try {
            console.log('Calling registration.pushManager.subscribe...');
            
            // Vérifier une dernière fois que le service worker est actif
            if (!registration.active) {
                console.error('Service worker still not active before subscription');
                throw new Error('Service worker not ready for push subscription');
            }
            
            // Détection du navigateur pour debug
            const userAgent = navigator.userAgent;
            const isIOSPWA = window.navigator.standalone === true;
            
            console.log('Detected browser - iOS PWA:', isIOSPWA);
            
            if (isIOSPWA) {
                console.log('iOS PWA detected - applying special handling...');
                
                // Pour iOS PWA, vérifier les permissions différemment
                if (Notification.permission === 'default') {
                    console.log('iOS PWA: Requesting notification permission...');
                    const permission = await Notification.requestPermission();
                    if (permission !== 'granted') {
                        throw new Error('iOS PWA: Notification permission not granted');
                    }
                }
                
                // Attendre plus longtemps pour iOS PWA
                console.log('Using extended delay for iOS PWA');
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Vérifier que le service worker est prêt pour iOS PWA
                if (!registration.active) {
                    console.error('iOS PWA: Service worker not active');
                    throw new Error('iOS PWA: Service worker not ready');
                }
                
                console.log('iOS PWA: Ready for subscription');
            } else {
                // Délai standard pour les autres navigateurs
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            subscription = await registration.pushManager.subscribe(subscribeOptions);
            console.log('Subscription successful!');
        } catch (subscribeError) {
            console.error('Subscription error:', subscribeError);
            throw subscribeError;
        }
        console.log('Push subscription created:', subscription);
        
        // Envoyer la souscription au serveur
        console.log('Sending subscription to server:', subscription);
        const subscribeResponse = await fetch('/api/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',  // Pour envoyer les cookies
            body: JSON.stringify(subscription)
        });
        
        if (!subscribeResponse.ok) {
            const errorText = await subscribeResponse.text();
            console.error('Failed to subscribe:', errorText);
            throw new Error('Failed to subscribe to push notifications');
        }
        
        console.log('Successfully subscribed to push notifications');
        return true;
    } catch (error) {
        console.error('Error subscribing to push notifications:', error);
        return false;
    }
}

// Envoie la souscription au serveur
async function sendSubscriptionToServer(subscription) {
    const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify(subscription)
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to send subscription to server:', errorText);
        throw new Error('Failed to send subscription to server');
    }
    
    return true;
}



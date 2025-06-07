// Notification header management functions
// This file handles the notification icon state in the header across different pages

function updateNotificationHeaderIcon() {
    const headerIcon = document.getElementById('notification-header-icon');
    if (!headerIcon) return;
    
    // Check notification permission and subscription status
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
        headerIcon.src = headerIcon.src.replace('img/header/notification_full.png', 'img/header/notification.png');
        return;
    }
    
    // Check if notifications are granted and we have an active subscription
    if (Notification.permission === 'granted') {
        navigator.serviceWorker.getRegistration('/static/sw.js').then(registration => {
            if (registration) {
                registration.pushManager.getSubscription().then(subscription => {
                    if (subscription) {
                        // Notifications are enabled
                        headerIcon.src = headerIcon.src.includes('img/header/notification_full.png') ? 
                            headerIcon.src : 
                            headerIcon.src.replace('img/header/notification.png', 'img/header/notification_full.png');
                    } else {
                        // No subscription
                        headerIcon.src = headerIcon.src.replace('img/header/notification_full.png', 'img/header/notification.png');
                    }
                });
            } else {
                // No service worker
                headerIcon.src = headerIcon.src.replace('img/header/notification_full.png', 'img/header/notification.png');
            }
        });
    } else {
        // Permission not granted
        headerIcon.src = headerIcon.src.replace('img/header/notification_full.png', 'img/header/notification.png');
    }
}

// Common notification management functions
async function enableNotifications() {
    try {
        console.log('Enabling notifications...');
        
        // Specific handling for iOS PWA
        const isIOSPWA = window.navigator.standalone === true;
        
        console.log('Browser detection:', {
            isIOSPWA,
            userAgent: navigator.userAgent,
            standalone: window.navigator.standalone
        });
        
        if (isIOSPWA) {
            console.log('Detected iOS PWA - applying special handling');
            // For iOS PWA, wait a bit longer before requesting permission
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        const result = await initializePushNotifications();
        
        if (result) {
            console.log('Notifications enabled successfully');
            // Update header icon
            setTimeout(updateNotificationHeaderIcon, 100);
            alert('✅ Notifications activées avec succès !');
        } else {
            console.log('Failed to enable notifications');
            alert('❌ Impossible d\'activer les notifications');
        }
    } catch (error) {
        console.error('Error enabling notifications:', error);
        alert(`❌ Erreur lors de l'activation: ${error.message}`);
    }
}

async function disableNotifications() {
    try {
        // Confirm with user
        if (!confirm('Êtes-vous sûr de vouloir désactiver les notifications push ?')) {
            return;
        }
        
        console.log('Disabling notifications...');
        
        // Get current subscription
        const registration = await navigator.serviceWorker.getRegistration('/static/sw.js');
        if (registration) {
            const subscription = await registration.pushManager.getSubscription();
            if (subscription) {
                // Unsubscribe from the service worker
                await subscription.unsubscribe();
                
                // Remove from backend database
                const response = await fetch('/api/unsubscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        endpoint: subscription.endpoint
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    console.log('Notifications disabled successfully');
                    // Update header icon
                    setTimeout(updateNotificationHeaderIcon, 100);
                    alert('✅ Notifications désactivées avec succès !');
                } else {
                    throw new Error(result.error || 'Failed to unsubscribe from backend');
                }
            } else {
                throw new Error('No active subscription found');
            }
        } else {
            throw new Error('Service worker not registered');
        }
    } catch (error) {
        console.error('Error disabling notifications:', error);
        alert(`❌ Erreur lors de la désactivation: ${error.message}`);
    }
}

// Test notification function
async function testNotification() {
    try {
        const testBtn = document.getElementById('testNotificationBtn');
        if (!testBtn) {
            console.error('Test notification button not found');
            return;
        }
        
        const originalText = testBtn.textContent;
        testBtn.textContent = '⏳ Envoi...';
        testBtn.disabled = true;
        
        // Données de notification de test
        const testNotificationData = {
            "title": "🧪 Test Notification",
            "body": "Ceci est un test de notification push. Si vous voyez ceci, ça fonctionne !",
            "icon": "/static/img/icon.png",
            "badge": "/static/img/badge.png",
            "data": {
                "type": "test",
                "url": window.location.pathname
            }
        };
        
        const response = await fetch('/api/send-notification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                notification_data: testNotificationData
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            testBtn.textContent = '✓ Envoyé';
            testBtn.style.backgroundColor = '#4CAF50';
            alert(`✅ ${result.message}`);
            
            // Reset button after 3 seconds
            setTimeout(() => {
                testBtn.textContent = originalText;
                testBtn.style.backgroundColor = '#2196F3';
                testBtn.disabled = false;
            }, 3000);
        } else {
            throw new Error(result.error || 'Failed to send test notification');
        }
    } catch (error) {
        console.error('Error sending test notification:', error);
        const testBtn = document.getElementById('testNotificationBtn');
        if (testBtn) {
            testBtn.textContent = '❌ Erreur';
            testBtn.style.backgroundColor = '#f44336';
            alert(`❌ Erreur: ${error.message}`);
            
            // Reset button after 3 seconds
            setTimeout(() => {
                testBtn.textContent = '🧪 Tester les notifications';
                testBtn.style.backgroundColor = '#2196F3';
                testBtn.disabled = false;
            }, 3000);
        }
    }
}

// Common toggle function that can be overridden by individual pages
function toggleNotificationState() {
    console.log('Toggle notification state called');
    
    // Check current state and toggle
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
        alert('❌ Les notifications ne sont pas supportées sur cet appareil');
        return;
    }
    
    if (Notification.permission === 'granted') {
        navigator.serviceWorker.getRegistration('/static/sw.js').then(registration => {
            if (registration) {
                registration.pushManager.getSubscription().then(subscription => {
                    if (subscription) {
                        // Notifications are enabled, disable them
                        disableNotifications();
                    } else {
                        // No subscription, enable them
                        enableNotifications();
                    }
                }).catch(error => {
                    console.error('Error checking subscription:', error);
                    enableNotifications();
                });
            } else {
                // No service worker, enable them
                enableNotifications();
            }
        }).catch(error => {
            console.error('Error getting service worker registration:', error);
            enableNotifications();
        });
    } else {
        // Permission not granted, enable them
        enableNotifications();
    }
}

// Initialize header notification icon on page load
function initNotificationHeader() {
    // Wait a bit for the page to load completely
    setTimeout(updateNotificationHeaderIcon, 500);
    
    // Also update periodically to catch any changes
    setInterval(updateNotificationHeaderIcon, 5000);
}

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNotificationHeader);
} else {
    initNotificationHeader();
}

# Utilisation des notifications de suivi

## Nouvelles routes ajoutées

### 1. Route complète : `/api/send-follow-notification`

Cette route crée la relation de suivi ET envoie la notification.

**URL:** `POST /api/send-follow-notification`
**Authentification:** Requise (token Supabase dans les cookies)

**Corps de la requête:**
```json
{
  "followed_username": "username_b"
}
```

**Exemple d'utilisation:**
```javascript
// L'utilisateur connecté (username_a) suit username_b
fetch('/api/send-follow-notification', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    followed_username: "username_b"
  })
});
```

### 2. Route notification uniquement : `/api/notify-follow`

Cette route envoie uniquement la notification (sans créer la relation de suivi).

**URL:** `POST /api/notify-follow`
**Authentification:** Requise (token Supabase dans les cookies)

**Corps de la requête:**
```json
{
  "follower_username": "username_a",
  "followed_user_id": "uuid-de-l-utilisateur-suivi"
}
```

## Notification envoyée

Quand un utilisateur A (username_a) suit un utilisateur B (username_b), B reçoit cette notification:

```json
{
  "notification_data": {
    "title": "Un chef vous suit",
    "body": "@username_a vous suit sur sauce! Cliquez pour voir son profil et ses recettes 😋",
    "icon": "/static/img/icon.png",
    "badge": "/static/img/badge.png",
    "data": {
      "type": "custom",
      "url": "/feed"
    }
  }
}
```

## Intégration dans votre application

### Côté frontend (JavaScript)

```javascript
async function followUser(username) {
  try {
    const response = await fetch('/api/send-follow-notification', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        followed_username: username
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('Utilisateur suivi avec succès:', result.message);
      // Mettre à jour l'interface utilisateur
    } else {
      console.error('Erreur lors du suivi:', result.error);
    }
  } catch (error) {
    console.error('Erreur réseau:', error);
  }
}

// Utilisation
followUser('username_b');
```

### Côté backend (déclenchement automatique)

Si vous avez déjà un système de suivi et voulez juste ajouter les notifications, vous pouvez utiliser la route `/api/notify-follow` :

```python
import requests

def trigger_follow_notification(follower_username, followed_user_id):
    """Déclencher une notification de suivi"""
    url = "http://localhost:5001/api/notify-follow"
    data = {
        "follower_username": follower_username,
        "followed_user_id": followed_user_id
    }
    
    # Vous devez inclure le token d'authentification approprié
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {your_service_token}"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

## Prérequis

1. **Table follows**: Assurez-vous que la table `follows` existe dans Supabase avec les colonnes :
   - `id` (primary key)
   - `follower_id` (UUID, foreign key vers profiles.id)
   - `following_id` (UUID, foreign key vers profiles.id)
   - `created_at` (timestamp)

2. **Table profiles**: Doit avoir les colonnes :
   - `id` (UUID, primary key)
   - `username` (string, unique)

3. **Notifications push**: L'utilisateur suivi doit avoir activé les notifications push.

## Gestion des erreurs

- **400**: Données manquantes ou invalides
- **401**: Non authentifié
- **404**: Utilisateur non trouvé
- **500**: Erreur serveur

Les notifications qui échouent n'empêchent pas la création de la relation de suivi.

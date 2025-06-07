# Guide de Test Manuel - Notifications de Suivi

## 🎯 Objectif
Tester le système complet de notifications push lors du suivi d'utilisateurs.

## 📋 Prérequis
1. Application sauce running sur http://localhost:5001
2. Deux comptes utilisateurs (A et B)
3. Navigateur supportant les notifications push
4. Notifications autorisées dans le navigateur

## 🧪 Procédure de Test

### Étape 1 : Préparation
1. Ouvrir deux onglets/fenêtres de navigateur
2. Aller sur http://localhost:5001 dans les deux
3. Se connecter avec l'utilisateur A dans le premier onglet
4. Se connecter avec l'utilisateur B dans le second onglet

### Étape 2 : Activation des Notifications
Dans chaque onglet :
1. Accepter les notifications push si demandé
2. Vérifier que les notifications sont activées dans les paramètres du navigateur
3. La console devrait afficher des logs de souscription

### Étape 3 : Test du Suivi
1. Dans l'onglet utilisateur A : aller sur `/profile`
2. Rechercher l'utilisateur B dans la barre de recherche
3. Cliquer sur "Suivre" à côté du nom de l'utilisateur B
4. Observer :
   - Message de succès affiché : "Vous suivez maintenant @username_b ! 🎉"
   - Console : logs de la requête POST vers `/api/send-follow-notification`

### Étape 4 : Vérification de la Notification
Dans l'onglet utilisateur B :
1. Une notification push devrait apparaître avec :
   - **Titre** : "Un chef vous suit"
   - **Corps** : "@username_a vous suit sur sauce! Cliquez pour voir son profil et ses recettes 😋"
   - **Icône** : icône de l'app
2. Cliquer sur la notification devrait rediriger vers `/feed`

### Étape 5 : Vérification Base de Données
1. Vérifier que la relation de suivi a été créée dans la table `follows`
2. Vérifier les logs serveur pour confirmer l'envoi de la notification

## 🔍 Points de Vérification

### Frontend
- [ ] Interface de recherche d'utilisateurs fonctionne
- [ ] Bouton "Suivre" change d'état après clic
- [ ] Message de succès s'affiche
- [ ] Aucune erreur JavaScript dans la console

### Backend  
- [ ] Route `/api/send-follow-notification` accessible avec auth
- [ ] Création de la relation de suivi en base
- [ ] Logs de notification dans la console serveur
- [ ] Gestion des erreurs (utilisateur non trouvé, etc.)

### Notifications
- [ ] Notification reçue avec le bon titre et corps
- [ ] Icône et badge corrects
- [ ] Clic sur notification redirige vers `/feed`
- [ ] Pas de notification si utilisateur n'a pas d'abonnement push

## 🚨 Dépannage

### Aucune notification reçue
1. Vérifier que les notifications sont autorisées dans le navigateur
2. Vérifier la console pour les erreurs de service worker
3. Vérifier les logs serveur pour les erreurs de push
4. Tester avec un autre navigateur

### Erreur lors du suivi
1. Vérifier l'authentification (token valide)
2. Vérifier que l'utilisateur cible existe
3. Consulter la console serveur pour les détails de l'erreur

### Service Worker
1. Aller dans DevTools > Application > Service Workers
2. Vérifier que le SW est enregistré et actif
3. Tester les notifications depuis l'onglet Service Worker

## 📊 Structure de Notification Attendue
```json
{
  "title": "Un chef vous suit",
  "body": "@username_a vous suit sur sauce! Cliquez pour voir son profil et ses recettes 😋",
  "icon": "/static/img/icon.png",
  "badge": "/static/img/badge.png",
  "data": {
    "type": "custom",
    "url": "/feed"
  }
}
```

## 🎉 Critères de Succès
- ✅ L'utilisateur A peut suivre l'utilisateur B sans erreur
- ✅ L'utilisateur B reçoit une notification push avec le bon contenu
- ✅ La notification redirige vers `/feed` quand cliquée
- ✅ La relation de suivi est correctement enregistrée en base
- ✅ Pas d'erreurs dans les logs serveur ou client

# Notifications Module

This module handles all push notification functionality for the Sauce application.

## API Endpoints

All notification endpoints are prefixed with `/api`:

### GET `/api/vapid-public-key`
Returns the VAPID public key needed for push notification subscriptions.

**Response:**
```json
{
  "publicKey": "BJ4h..."
}
```

### POST `/api/subscribe`
Subscribe a user to push notifications.

**Headers:**
- `Authorization: Bearer <token>` or Cookie with `sb-access-token`

**Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "BCv...",
    "auth": "4w..."
  }
}
```

**Response:**
```json
{
  "message": "Successfully subscribed to push notifications"
}
```

### POST `/api/send-notification`
Send a custom notification to the authenticated user.

**Headers:**
- `Authorization: Bearer <token>` or Cookie with `sb-access-token`

**Body:**
```json
{
  "notification_data": {
    "title": "Notification Title",
    "body": "Notification message",
    "icon": "/static/img/icon.png",
    "badge": "/static/img/badge.png",
    "data": {
      "type": "custom",
      "url": "/target-page"
    }
  }
}
```

**Response:**
```json
{
  "message": "Test notification sent successfully to 1 device(s)",
  "subscriptions_found": 1,
  "notifications_sent": 1
}
```

### POST `/api/unsubscribe`
Unsubscribe from push notifications.

**Headers:**
- `Authorization: Bearer <token>` or Cookie with `sb-access-token`

**Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

**Response:**
```json
{
  "message": "Successfully unsubscribed from push notifications",
  "deleted_count": 1
}
```

### GET `/api/sw.js`
Serves the service worker file for push notifications.

## Dependencies

This module requires:
- `pywebpush` - For sending push notifications
- `supabase` - For database operations
- `jwt` - For token verification

## Environment Variables

Required environment variables:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - JWT secret for token verification
- `VAPID_PUBLIC_KEY` - VAPID public key for push notifications
- `VAPID_PRIVATE_KEY` - VAPID private key for push notifications
- `CONTACT_EMAIL` - Contact email for VAPID claims

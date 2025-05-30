-- Set the push notification webhook URL as a database setting
ALTER DATABASE postgres SET "app.push_notification_webhook_url" = 'https://helping-pumped-gobbler.ngrok-free.app/api/notifications/push';

-- Note: You'll need to update this URL for each environment (dev, staging, prod)
-- Example for production:
-- ALTER DATABASE postgres SET "app.push_notification_webhook_url" = 'https://your-production-domain.com/api/notifications/push';

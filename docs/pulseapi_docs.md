# PulseAPI Documentation

PulseAPI is a REST API for sending transactional notifications (email, SMS, and push) from your application.

## Authentication

All requests require an API key sent in the `Authorization` header:
```
Authorization: Bearer YOUR_API_KEY
```
API keys are generated in the Dashboard under Settings > API Keys. Keys are scoped to either Test mode or Live mode — test keys start with `pk_test_`, live keys start with `pk_live_`.

## Sending a Notification

**Endpoint:** `POST https://api.pulseapi.dev/v1/notifications`

**Request body:**
```json
{
  "channel": "email" | "sms" | "push",
  "to": "recipient address or phone number or device token",
  "template_id": "optional template identifier",
  "data": { "any": "template variables" }
}
```

Responses return a `notification_id` you can use to check delivery status.

## Rate Limits

- Free tier: 100 requests/minute
- Pro tier: 1,000 requests/minute
- Enterprise tier: custom limits, contact sales

Exceeding your limit returns a `429 Too Many Requests` response with a `Retry-After` header.

## Webhooks

You can register a webhook URL (Dashboard > Settings > Webhooks) to receive delivery status updates. PulseAPI will POST events like `delivered`, `failed`, and `bounced` to your endpoint as they happen.

## Error Codes

| Code | Meaning |
|---|---|
| 400 | Invalid request body or missing required field |
| 401 | Invalid or missing API key |
| 404 | Template ID not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error — safe to retry with backoff |

## SDKs

Official SDKs are available for Python (`pip install pulseapi`), Node.js (`npm install pulseapi`), and Ruby (`gem install pulseapi`). Community-maintained SDKs exist for Go and PHP but are not officially supported.

## Support

For issues not covered here, contact support@pulseapi.dev or open a ticket in the Dashboard.

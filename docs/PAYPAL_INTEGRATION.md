# PayPal Sandbox

Set `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com`, and `FRONTEND_URL`. The server obtains a token, creates Orders API v2 CAPTURE orders and returns the approval URL. Capture is restricted to the signed-in user's order and checks completed status, amount, and currency. Duplicate local captures return the existing completed state.

The frontend redirects to PayPal approval. A return-route capture UI has not yet been implemented; call `POST /api/payments/capture` with the returned `token` as `orderId` and the user's bearer token. No successful payment is simulated. Webhook signature verification is not implemented. Sandbox credentials and network connectivity are needed for end-to-end verification.

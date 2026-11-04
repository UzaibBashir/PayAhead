# API reference

These Flask routes document the server-side handlers used by the Streamlit app. Streamlit invokes them in-process; no separate API server is needed for the app. To develop against the optional HTTP API directly, start `python backend/app.py` and use `http://localhost:5000/api`. JSON is used except for CSV uploads.

- `GET /health`: API and PayPal credential readiness.
- `POST /auth/register`, `POST /auth/login`: receive JWT bearer tokens.
- `GET /dashboard?profile=student`: profile metrics, recent activity, and available demo profiles.
- `PUT /finances/profile`: save a signed-in user's financial profile.
- `POST /transactions/import`: import a UTF-8 CSV with `date` and `amount`; optional `description`, `name`, or `merchant`.
- `GET /products?q=`: search the curated/demo catalogue.
- `POST /products`: add a signed-in user's product with a user-confirmed price and optional validated URL.
- `POST /products/extract`: preview public Open Graph/Schema.org metadata with DNS pinning, private-address blocking, 1 MB limit, and redirects disabled. User confirmation is required before save; retailer values remain unverified.
- `POST /analyze`: `{product,price}` returns rule-based affordability, scenarios, five specialist findings, and a provider-generated text explanation. The server checks product price and currency.
- `GET /forecast`: profile baseline for guests; monthly net history average for signed-in accounts with enough imported history.
- `GET /anomalies`: Isolation Forest flags for signed-in accounts with at least 30 imported expenses.
- `GET /products/<id>/price-history` or `GET /price-history?product=`: generated synthetic monthly price series and trend demo.
- `POST /schedule`, `GET /schedule`: save and list purchase watches.
- `POST /schedule/evaluate`, `GET /alerts`: evaluate watches against local catalogue/profile values and list in-app alerts.
- `GET /agents/activity`: signed-in user's saved specialist findings.
- `GET/PUT/DELETE /preferences`: read, save, or clear user-approved preferences.
- `GET /payments/status`, `POST /payments/order`, `POST /payments/capture`: PayPal Sandbox readiness, order creation, and verified capture.

Use `Authorization: Bearer <token>` for private endpoints. Registration requires an email-like value and a password of at least eight characters. Scenario values are estimates, not guaranteed cash balances.

# Security

Passwords use Werkzeug password hashing. JWTs protect profile updates, CSV imports, schedules and payments. Profile data is keyed to user ID. CSV is limited to 2 MB, decoded as UTF-8 and treated as plain text; file contents are never executed. PayPal credentials stay server-side. Payments require explicit user approval and server capture.

Use unique secrets, HTTPS, short-lived tokens, rate limiting, webhook signature verification, audit retention and a privacy review before production use. Demo profile, activity and forecast chart are fictional. Financial guidance is educational only. Do not upload sensitive statements to a public deployment.

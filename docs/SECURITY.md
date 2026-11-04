# Security

Passwords use Werkzeug password hashing. JWTs protect profile updates, CSV imports, schedules and payments. Profile data is keyed to user ID. CSV is limited to 2 MB, decoded as UTF-8 and treated as plain text; file contents are never executed. PayPal credentials stay server-side. Payments require explicit user approval and server capture.

Use unique secrets, HTTPS, short-lived tokens, rate limiting, webhook signature verification, audit retention and a privacy review before production use. Hosted Streamlit should use Supabase Postgres; Community Cloud does not guarantee persistence for local files. Keep database and payment credentials in Streamlit Secrets. Demo profile, activity and forecast chart are fictional. Financial guidance is educational only. Do not upload sensitive statements to a public deployment.

Product metadata preview resolves and pins a public DNS address, blocks local/private addresses and nonstandard ports, refuses redirects, enforces TLS and a 1 MB response cap, and parses only HTML metadata. It does not execute page scripts. User must confirm extracted details; prices are not independently verified.

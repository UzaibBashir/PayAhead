# Architecture

Streamlit is the user interface. It calls the Flask REST API over HTTP; Flask uses SQLAlchemy and SQLite. Deterministic finance calculations return affordability scenarios. Five specialist roles summarize relevant evidence. No agent authorizes a payment.

```mermaid
flowchart LR
 UI[Streamlit UI] --> API[Flask REST API]
 API --> DB[(SQLite / SQLAlchemy)]
 API --> CALC[Financial calculations]
 CALC --> TEAM[Five advisory roles]
 API --> PP[PayPal Sandbox Orders v2]
```

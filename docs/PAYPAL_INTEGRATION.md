# PayPal Sandbox

Set `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com`, `PAYPAL_RETURN_URL=http://localhost:8501`, and `PAYPAL_CANCEL_URL=http://localhost:8501`. Flask obtains a token and creates Orders API v2 CAPTURE orders. Streamlit returns from payer approval with the PayPal order token and invokes the signed-in user's capture route. The server checks completed status, amount, and currency. Duplicate application captures return the already completed state.

Payment order/capture behavior has mocked tests. A real Sandbox payment has not been completed in this environment because it requires credentials and payer approval. Webhook signature verification is not implemented. This is a Sandbox demonstration only, not a production integration.

# AI and models

The live MVP uses deterministic finance calculations and a structured five-role advisory workflow. It does not call an LLM and never invents price trends. Product price endpoints use explicitly labeled generated demo series; their trend estimate is educational only and does not describe retailer prices.

An optional scikit-learn expense classifier can be trained with `python backend/scripts/train_models.py`. It generates synthetic merchant descriptions, uses a stratified held-out 20% split and prints precision/recall/F1. Metrics apply only to synthetic data and do not predict performance on real bank statements. When its saved model exists, CSV import uses the classifier; a conservative keyword fallback is used otherwise. A user-level Isolation Forest flags unusual expense amounts once at least 30 imported expenses exist; flags are review prompts, not fraud findings. No deep learning model is included.

| Task | MVP method | Limitation |
|---|---|---|
| Expense category | TF-IDF + logistic regression training script | Synthetic data only |
| Cash flow | Deterministic monthly surplus/scenario arithmetic | No learned balance series |
| Affordability | Income, obligations, savings-buffer rules | Advisory only |
| Anomaly flags | Isolation Forest on imported expense amounts (30+ required) | Unusual values need manual review |
| Price trend | Linear regression against 12 synthetic monthly points, last 3 held out | Synthetic demo only; never a live quote |


## Price model evaluation

Run `python backend/scripts/evaluate_price_model.py` to reproduce the 3 point time holdout across the 20 synthetic product series (60 forecasts). Current sample MAE: last observed value baseline 20.31, linear regression 18.18 currency units. These values describe the generated data only and are not evidence of market forecasting quality.

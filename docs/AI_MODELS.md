# AI and models

The live MVP uses deterministic finance calculations and a structured five-role advisory workflow. It does not call an LLM and never invents price trends. Historical product price series are absent, so price prediction is deliberately unavailable.

An optional scikit-learn expense classifier can be trained with `python backend/scripts/train_models.py`. It generates synthetic merchant descriptions, uses a stratified held-out 20% split and prints precision/recall/F1. Metrics apply only to synthetic data and do not predict performance on real bank statements. The script is not wired into CSV import. No deep learning or anomaly classifier is included.

| Task | MVP method | Limitation |
|---|---|---|
| Expense category | TF-IDF + logistic regression training script | Synthetic data only |
| Cash flow | Deterministic monthly surplus/scenario arithmetic | No learned balance series |
| Affordability | Income, obligations, savings-buffer rules | Advisory only |
| Price forecast | Disabled without price history | No fabricated estimates |

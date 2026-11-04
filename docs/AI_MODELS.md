# AI and models

The live MVP uses deterministic finance calculations and a structured five-role advisory workflow. It does not call an LLM and never invents price trends. Product price endpoints use explicitly labeled generated demo series; their trend estimate is educational only and does not describe retailer prices. Expense categorization supports both a classic model and an optional PyTorch MLP; the latter is a demonstration trained only on generated descriptions.

An optional scikit-learn expense classifier can be trained with `python backend/scripts/train_models.py`. The optional PyTorch MLP can be trained/benchmarked with `python backend/scripts/benchmark_expense_dl.py`, then selected by setting `EXPENSE_MODEL=pytorch`. Install its optional dependency with `pip install -r backend/requirements-deep-learning.txt`; the model artifact is generated locally and ignored by Git. The comparison uses the same synthetic descriptions and stratified held-out 20% split, reporting accuracy and macro precision/recall/F1. Both models scored 1.0000 on this simple synthetic holdout; that easy generated corpus makes the result unsuitable as evidence of performance on real bank statements. Scikit-learn remains the default. If PyTorch or its artifact is unavailable, categorization falls back to the standard classifier/keyword path. A user-level Isolation Forest flags unusual expense amounts once at least 30 imported expenses exist; flags are review prompts, not fraud findings.

| Task | MVP method | Limitation |
|---|---|---|
| Expense category | TF-IDF + logistic regression (default); optional PyTorch MLP | Synthetic data only; benchmark is not real-world validation |
| Cash flow | Deterministic monthly surplus/scenario arithmetic | No learned balance series |
| Affordability | Income, obligations, savings-buffer rules | Advisory only |
| Anomaly flags | Isolation Forest on imported expense amounts (30+ required) | Unusual values need manual review |
| Price trend | Linear regression against 12 synthetic monthly points, last 3 held out | Synthetic demo only; never a live quote |


## Price model evaluation

Run `python backend/scripts/evaluate_price_model.py` to reproduce the 3 point time holdout across the 20 synthetic product series (60 forecasts). Current sample MAE: last observed value baseline 20.31, linear regression 18.18 currency units. These values describe the generated data only and are not evidence of market forecasting quality.

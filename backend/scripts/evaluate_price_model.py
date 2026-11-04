"""Evaluate holdout error for synthetic product series; this is not market accuracy."""
import csv,collections
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression
rows=collections.defaultdict(list)
with open(Path(__file__).parents[2]/'data'/'sample_price_history.csv',encoding='utf-8-sig') as f:
 for r in csv.DictReader(f):rows[r['product']].append(float(r['price']))
errors={'last-value':[],'linear-regression':[]}
for values in rows.values():
 values=np.array(values); cut=len(values)-3; x=np.arange(len(values)).reshape(-1,1)
 if cut<5:continue
 pred_mean=np.repeat(values[cut-1],3); pred_lin=LinearRegression().fit(x[:cut],values[:cut]).predict(x[cut:])
 errors['last-value'].extend(abs(pred_mean-values[cut:]));errors['linear-regression'].extend(abs(pred_lin-values[cut:]))
for model,err in errors.items():print(f"{model}: n={len(err)} MAE={np.mean(err):.2f} synthetic currency units")

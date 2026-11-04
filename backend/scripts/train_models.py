"""Train a reproducible synthetic expense classifier with held-out metrics."""
import numpy as np,joblib,pathlib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
rng=np.random.default_rng(17); examples={'Food':['grocery store','market produce','restaurant','coffee shop','meal delivery'],'Housing':['monthly rent','home insurance','property manager'],'Transport':['metro transit','gas station','rideshare','parking garage'],'Bills':['electric utility','internet service','mobile phone'],'Shopping':['online marketplace','clothing store','electronics shop']}; texts=[];labels=[]
for label,terms in examples.items():
 for i in range(240):texts.append(terms[i%len(terms)]+' '+str(rng.integers(1,100)));labels.append(label)
xtr,xte,ytr,yte=train_test_split(texts,labels,test_size=.2,random_state=42,stratify=labels);model=make_pipeline(TfidfVectorizer(ngram_range=(1,2)),LogisticRegression(max_iter=500));model.fit(xtr,ytr);out=pathlib.Path(__file__).parents[1]/'app'/'ml'/'expense_classifier.joblib';out.parent.mkdir(parents=True,exist_ok=True);joblib.dump(model,out);print('Holdout report on synthetic transactions:');print(classification_report(yte,model.predict(xte)))

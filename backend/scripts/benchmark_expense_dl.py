"""Compare a PyTorch MLP with TF-IDF/logistic regression on the same synthetic holdout."""
from pathlib import Path
import numpy as np,torch
from torch import nn
from torch.utils.data import TensorDataset,DataLoader
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,precision_recall_fscore_support

def make_data():
 rng=np.random.default_rng(17); examples={'Food':['grocery store','market produce','restaurant','coffee shop','meal delivery'],'Housing':['monthly rent','home insurance','property manager'],'Transport':['metro transit','gas station','rideshare','parking garage'],'Bills':['electric utility','internet service','mobile phone'],'Shopping':['online marketplace','clothing store','electronics shop']};texts=[];labels=[]
 for label,terms in examples.items():
  for i in range(240):texts.append(terms[i%len(terms)]+' '+str(rng.integers(1,100)));labels.append(label)
 return texts,np.asarray(labels)
def score(name,y,pred):
 precision,recall,f1,_=precision_recall_fscore_support(y,pred,average='macro',zero_division=0)
 print(f'{name}: accuracy={accuracy_score(y,pred):.4f} macro_precision={precision:.4f} macro_recall={recall:.4f} macro_f1={f1:.4f} n_test={len(y)}')
def main():
 torch.manual_seed(17);torch.set_num_threads(1);texts,labels=make_data();xtr,xte,ytr,yte=train_test_split(texts,labels,test_size=.2,random_state=42,stratify=labels)
 baseline=make_pipeline(TfidfVectorizer(ngram_range=(1,2)),LogisticRegression(max_iter=500));baseline.fit(xtr,ytr);score('TF-IDF + logistic regression',yte,baseline.predict(xte))
 vocab=TfidfVectorizer(ngram_range=(1,2));a=vocab.fit_transform(xtr).toarray().astype('float32');b=vocab.transform(xte).toarray().astype('float32');classes=sorted(set(ytr));lookup={v:i for i,v in enumerate(classes)};yt=np.array([lookup[v] for v in ytr],dtype='int64');yv=np.array([lookup[v] for v in yte],dtype='int64')
 model=nn.Sequential(nn.Linear(a.shape[1],64),nn.ReLU(),nn.Dropout(.15),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,len(classes)));opt=torch.optim.Adam(model.parameters(),lr=.01);loss_fn=nn.CrossEntropyLoss();loader=DataLoader(TensorDataset(torch.from_numpy(a),torch.from_numpy(yt)),batch_size=64,shuffle=True,generator=torch.Generator().manual_seed(17))
 for _ in range(50):
  model.train()
  for xb,yb in loader:opt.zero_grad();loss=loss_fn(model(xb),yb);loss.backward();opt.step()
 model.eval()
 with torch.no_grad():pred=model(torch.from_numpy(b)).argmax(1).numpy()
 score('PyTorch MLP',yte,np.array(classes)[pred]);out=Path(__file__).parents[1]/'app'/'ml'/'expense_mlp.pt';out.parent.mkdir(parents=True,exist_ok=True);torch.save({'state_dict':model.state_dict(),'vocab':{str(k):int(v) for k,v in vocab.vocabulary_.items()},'classes':[str(label) for label in classes]},out);print('Saved experimental weights to',out)
if __name__=='__main__':main()

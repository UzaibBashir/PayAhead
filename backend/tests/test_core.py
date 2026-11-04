import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from app import app,metrics
def test_metrics():
 m=metrics({'income':5000,'fixed':2000,'variable':1000,'debt':500,'savings':6000,'currency':'USD'}); assert m['disposableIncome']==1500 and m['totalExpenses']==3500 and m['savingsRate']==30
def test_health_demo():
 c=app.test_client(); assert c.get('/api/health').json['status']=='ok'; d=c.get('/api/dashboard').json; assert d['simulated'] and d['metrics']['disposableIncome']==1550
def test_search(): assert len(app.test_client().get('/api/products?q=headphones').json['products'])==1

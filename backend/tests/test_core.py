import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from app import app,metrics,Product
def test_metrics():
 m=metrics({'income':5000,'fixed':2000,'variable':1000,'debt':500,'savings':6000,'currency':'USD'}); assert m['disposableIncome']==1500 and m['totalExpenses']==3500 and m['savingsRate']==30
def test_health_demo():
 c=app.test_client(); assert c.get('/api/health').json['status']=='ok'; d=c.get('/api/dashboard').json; assert d['simulated'] and d['metrics']['disposableIncome']==1550
def test_search(): assert len(app.test_client().get('/api/products?q=headphones').json['products'])==1


def test_demo_profiles_catalogue_and_specialists():
 c=app.test_client(); assert len(c.get('/api/dashboard').json['demoProfiles'])==5; assert len(c.get('/api/products').json['products'])>=20
 result=c.post('/api/analyze',json={'product':'Studio Pro Laptop','price':1499}).json
 assert len(result['agents'])==5 and result['agents'][2]['name']=='Price Intelligence'
 assert result['agents'][2]['finding'].startswith('No verified price history')

def test_forecast_is_explicit_about_demo_method():
 r=app.test_client().get('/api/forecast').json; assert r['simulated'] is True and 'not a learned' in r['note']


def test_synthetic_price_model_has_holdout_metrics():
 c=app.test_client(); product=c.get('/api/products?q=laptop').json['products'][0]
 with app.app_context(): pid=Product.query.filter_by(name=product['name']).first().id
 response=c.get(f'/api/products/{pid}/price-history').json
 assert response['source']=='synthetic_demo' and response['forecast']['holdoutPoints']==3
 assert response['forecast']['holdoutMAE']>=0 and 'not a retailer quote' in response['note']




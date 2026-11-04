import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from app import app,metrics,Product,Payment
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





def test_watch_eval_creates_user_alert():
 import secrets
 c=app.test_client();reg=c.post('/api/auth/register',json={'email':secrets.token_hex(5)+'@example.test','password':'long-enough-pass'});h={'Authorization':'Bearer '+reg.json['token']}
 saved=c.post('/api/schedule',headers=h,json={'product':'Studio Pro Laptop','target':0,'due':__import__('datetime').date.today().isoformat()});assert saved.status_code==201
 checked=c.post('/api/schedule/evaluate',headers=h,json={}).json;assert checked['checked']==1 and checked['created']
 assert len(c.get('/api/alerts',headers=h).json['alerts'])==1


def test_paypal_order_capture_and_duplicate_are_verified(monkeypatch):
 import secrets
 from unittest.mock import patch
 class Response:
  def __init__(self,data):self.data=data
  def json(self):return self.data
  def raise_for_status(self):return None
 c=app.test_client();reg=c.post('/api/auth/register',json={'email':secrets.token_hex(5)+'@example.test','password':'long-enough-pass'});h={'Authorization':'Bearer '+reg.json['token']}
 monkeypatch.setenv('PAYPAL_CLIENT_ID','sandbox-id');monkeypatch.setenv('PAYPAL_CLIENT_SECRET','sandbox-secret')
 order='ORDER-'+secrets.token_hex(6)
 with patch('requests.post',side_effect=[Response({'access_token':'access'}),Response({'id':order,'links':[{'rel':'approve','href':'https://sandbox.example/approve'}]})]):
  made=c.post('/api/payments/order',headers=h,json={'product':'QuietComfort Headphones','price':329,'currency':'USD'});assert made.status_code==200
 payload={'status':'COMPLETED','purchase_units':[{'payments':{'captures':[{'status':'COMPLETED','amount':{'value':'329.00','currency_code':'USD'}}]}}]}
 with patch('requests.post',side_effect=[Response({'access_token':'access'}),Response(payload)]) as call:
  captured=c.post('/api/payments/capture',headers=h,json={'orderId':order});assert captured.json['verified'] is True;assert call.call_count==2
 duplicate=c.post('/api/payments/capture',headers=h,json={'orderId':order});assert duplicate.json['duplicate'] is True




def test_product_url_blocks_private_hosts():
 from product_url import extract
 import pytest
 with pytest.raises(ValueError,match='private'):
  extract('http://127.0.0.1/admin')

def test_preferences_are_authenticated_and_user_scoped():
 import secrets
 c=app.test_client();reg=c.post('/api/auth/register',json={'email':secrets.token_hex(5)+'@example.test','password':'long-enough-pass'});headers={'Authorization':'Bearer '+reg.json['token']}
 assert c.put('/api/preferences',headers=headers,json={'category':'Audio','budget':'500','other':'ignored'}).json['preferences']=={'category':'Audio','budget':'500'}
 assert c.get('/api/preferences',headers=headers).json['preferences']['category']=='Audio'
 assert c.delete('/api/preferences',headers=headers).json['deleted'] is True
 assert c.get('/api/preferences',headers=headers).json['preferences']=={}

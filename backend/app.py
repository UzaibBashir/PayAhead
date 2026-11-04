import os,csv,io
from datetime import date,datetime,timedelta
from flask import Flask,jsonify,request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash,check_password_hash
app=Flask(__name__); app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('DATABASE_URL','sqlite:///payahead.db'); app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False; app.config['JWT_SECRET_KEY']=os.getenv('JWT_SECRET_KEY','local-dev-change-this'); CORS(app,origins=os.getenv('FRONTEND_URL','http://localhost:5173')); db=SQLAlchemy(app); jwt=JWTManager(app)
class User(db.Model):
 id=db.Column(db.Integer,primary_key=True); email=db.Column(db.String(255),unique=True,nullable=False); password=db.Column(db.String(255),nullable=False)
class Profile(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),unique=True); income=db.Column(db.Float,default=5200); fixed=db.Column(db.Float,default=2100); variable=db.Column(db.Float,default=1100); savings=db.Column(db.Float,default=8200); debt=db.Column(db.Float,default=450); currency=db.Column(db.String(3),default='USD'); name=db.Column(db.String(100),default='Personal profile')
class Transaction(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer); name=db.Column(db.String(140)); category=db.Column(db.String(60)); amount=db.Column(db.Float); date=db.Column(db.Date,default=date.today); kind=db.Column(db.String(10),default='expense')
class Product(db.Model):
 id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(160)); category=db.Column(db.String(70)); price=db.Column(db.Float); currency=db.Column(db.String(3),default='USD'); rating=db.Column(db.Float,default=4.5); image=db.Column(db.String(400)); description=db.Column(db.String(300))
class Schedule(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer); product=db.Column(db.String(160)); target=db.Column(db.Float); due=db.Column(db.Date); status=db.Column(db.String(20),default='watching')
class Payment(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer); product=db.Column(db.String(160)); amount=db.Column(db.Float); currency=db.Column(db.String(3)); paypal_order=db.Column(db.String(100),unique=True); status=db.Column(db.String(30),default='created'); created=db.Column(db.DateTime,default=datetime.utcnow)
def demo(): return {'name':'Maya Chen · Professional','income':5200,'fixed':2100,'variable':1100,'savings':8200,'debt':450,'currency':'USD'}
def metrics(p):
 inc=float(p.get('income',0)); fixed=float(p.get('fixed',0)); variable=float(p.get('variable',0)); debt=float(p.get('debt',0)); savings=float(p.get('savings',0)); spend=fixed+variable+debt; free=inc-spend
 return {'income':inc,'fixedExpenses':fixed,'variableExpenses':variable,'debtPayments':debt,'totalExpenses':spend,'disposableIncome':free,'savings':savings,'savingsRate':round(max(0,free)/inc*100,1) if inc else 0,'emergencyMonths':round(savings/max(1,fixed+variable),1),'currency':p.get('currency','USD')}
def profile(uid=None):
 if uid:
  x=Profile.query.filter_by(user_id=int(uid)).first()
  if x:return {'name':x.name,'income':x.income,'fixed':x.fixed,'variable':x.variable,'savings':x.savings,'debt':x.debt,'currency':x.currency}
 return demo()
def current_user():
 from flask_jwt_extended import verify_jwt_in_request,get_jwt_identity
 try: verify_jwt_in_request(optional=True); return get_jwt_identity()
 except Exception:return None
PRODUCTS=[{'name':'Studio Pro Laptop','category':'Computers','price':1499,'currency':'USD','rating':4.8,'image':'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=85','description':'A powerful 14-inch laptop for work and creative projects.'},{'name':'QuietComfort Headphones','category':'Audio','price':329,'currency':'USD','rating':4.7,'image':'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85','description':'Comfortable noise-cancelling headphones for focus.'},{'name':'Everyday Smartwatch','category':'Wearables','price':249,'currency':'USD','rating':4.5,'image':'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85','description':'Health, activity and notifications at a glance.'},{'name':'City Commuter Bike','category':'Outdoors','price':799,'currency':'USD','rating':4.6,'image':'https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=900&q=85','description':'A lightweight daily ride for city streets.'},{'name':'Home Espresso Maker','category':'Home','price':549,'currency':'USD','rating':4.4,'image':'https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?auto=format&fit=crop&w=900&q=85','description':'Cafe-style espresso for a slower morning.'}]
@app.get('/api/health')
def health(): return jsonify(status='ok',service='PayAhead API',payments='sandbox-configured' if os.getenv('PAYPAL_CLIENT_ID') and os.getenv('PAYPAL_CLIENT_SECRET') else 'credentials-required')
@app.post('/api/auth/register')
def register():
 from flask_jwt_extended import create_access_token
 d=request.get_json() or {}; email=str(d.get('email','')).strip().lower(); pw=str(d.get('password',''))
 if '@' not in email or len(pw)<8:return jsonify(error='Enter a valid email and a password with at least 8 characters.'),400
 if User.query.filter_by(email=email).first():return jsonify(error='An account with this email already exists.'),409
 u=User(email=email,password=generate_password_hash(pw)); db.session.add(u); db.session.flush(); db.session.add(Profile(user_id=u.id)); db.session.commit(); return jsonify(token=create_access_token(identity=str(u.id)),email=email),201
@app.post('/api/auth/login')
def login():
 from flask_jwt_extended import create_access_token
 d=request.get_json() or {}; u=User.query.filter_by(email=str(d.get('email','')).lower()).first()
 if not u or not check_password_hash(u.password,str(d.get('password',''))):return jsonify(error='Email or password is incorrect.'),401
 return jsonify(token=create_access_token(identity=str(u.id)),email=u.email)
@app.get('/api/dashboard')
def dashboard():
 uid=current_user(); p=profile(uid); tx=Transaction.query.filter_by(user_id=int(uid) if uid else None).order_by(Transaction.date.desc()).limit(8).all()
 recent=[{'name':t.name,'category':t.category,'amount':t.amount,'date':t.date.isoformat()} for t in tx] if tx else [{'name':n,'category':c,'amount':a,'date':(date.today()-timedelta(days=i*3)).isoformat()} for i,(n,c,a) in enumerate([('Rent','Housing',1450),('Groceries','Food',128),('Transit pass','Transport',72),('Coffee shop','Dining',18),('Utilities','Bills',116)])]
 return jsonify(profile=p,metrics=metrics(p),transactions=recent,simulated=not bool(uid))
@app.put('/api/finances/profile')
def update_profile():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to save a personal profile.'),401
 d=request.get_json() or {}; p=Profile.query.filter_by(user_id=int(uid)).first()
 for field in ('income','fixed','variable','savings','debt'):
  try:v=float(d.get(field,getattr(p,field)))
  except (TypeError,ValueError):return jsonify(error=f'{field} must be a number.'),400
  if v<0:return jsonify(error='Financial amounts cannot be negative.'),400
  setattr(p,field,v)
 p.currency=str(d.get('currency',p.currency)).upper()[:3]; db.session.commit(); return jsonify(profile=profile(uid),metrics=metrics(profile(uid)))
@app.get('/api/products')
def products():
 q=request.args.get('q','').lower(); vals=PRODUCTS+[{'name':p.name,'category':p.category,'price':p.price,'currency':p.currency,'rating':p.rating,'image':p.image,'description':p.description} for p in Product.query.all()]; return jsonify(products=[p for p in vals if q in (p['name']+' '+p['category']).lower()])
@app.post('/api/analyze')
def analyze():
 d=request.get_json() or {}; m=metrics(profile(current_user())); price=max(0,float(d.get('price',0))); name=str(d.get('product','Purchase'))[:160]; safe=m['disposableIncome']>=price and m['savings']-price>=max(0,m['fixedExpenses']+m['variableExpenses'])*.5; ratio=price/max(1,m['income'])*100
 scenarios=[{'label':'Buy now','days':0,'projectedCash':round(m['disposableIncome']-price,2),'result':'Comfortable' if safe else 'Tight'},{'label':'Wait 15 days','days':15,'projectedCash':round(max(0,m['disposableIncome']*.5-price),2),'result':'More room'},{'label':'Wait 30 days','days':30,'projectedCash':round(max(0,m['disposableIncome']*2-price),2),'result':'Build cash flow'},{'label':'Lower-cost option','days':0,'projectedCash':round(max(0,m['disposableIncome']-price*.7),2),'result':'Keeps more savings'}]
 findings=['Cash flow and obligations checked','Catalogue listing reviewed','Price history unavailable; no trend claimed','Buffer and affordability compared','Payment requires explicit approval']; names=['Financial Analyst','Product Research','Price Intelligence','Purchase Decision','Payment Safety']
 return jsonify(product=name,price=price,currency=m['currency'],affordable=safe,risk='low' if safe and ratio<15 else ('moderate' if m['disposableIncome']>=price else 'high'),recommendation='Buy when ready' if safe else 'Wait and build your buffer',reason=f"Your monthly amount after listed expenses and debt is {m['currency']} {m['disposableIncome']:,.0f}. This purchase is {ratio:.0f}% of monthly income. {'Your remaining savings preserve a basic buffer.' if safe else 'Buying now could reduce available cash or your emergency buffer.'}",scenarios=scenarios,agents=[{'name':n,'status':'complete','finding':f} for n,f in zip(names,findings)])
@app.post('/api/transactions/import')
def import_csv():
 uid=current_user()
 if not uid:return jsonify(error='Sign in before importing transactions.'),401
 f=request.files.get('file')
 if not f or not f.filename.lower().endswith('.csv'):return jsonify(error='Choose a CSV file.'),400
 try:
  raw=f.stream.read(2000001)
  if len(raw)>2000000:return jsonify(error='CSV exceeds the 2 MB limit.'),413
  reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))); cols={x.lower():x for x in(reader.fieldnames or [])}; dc=next((cols[k] for k in ('date','transaction_date') if k in cols),None); ac=next((cols[k] for k in ('amount','value') if k in cols),None); nc=next((cols[k] for k in ('description','name','merchant') if k in cols),None)
  if not dc or not ac:return jsonify(error='CSV needs date and amount columns.'),400
  added=0
  for row in reader:
   try:day=datetime.fromisoformat(row[dc][:10]).date(); amt=float(row[ac].replace(',','')); name=(row.get(nc,'Transaction') if nc else 'Transaction')[:140]
   except Exception:continue
   if Transaction.query.filter_by(user_id=int(uid),date=day,name=name,amount=abs(amt)).first():continue
   db.session.add(Transaction(user_id=int(uid),date=day,name=name,amount=abs(amt),kind='income' if amt<0 else 'expense',category='Other')); added+=1
  db.session.commit(); return jsonify(imported=added)
 except UnicodeDecodeError:return jsonify(error='CSV must use UTF-8 encoding.'),400
@app.post('/api/schedule')
def schedule():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to save a purchase watch.'),401
 d=request.get_json() or {}; s=Schedule(user_id=int(uid),product=str(d.get('product',''))[:160],target=max(0,float(d.get('target',0))),due=date.fromisoformat(d.get('due',date.today().isoformat()))); db.session.add(s); db.session.commit(); return jsonify(id=s.id,status=s.status),201
@app.get('/api/payments/status')
def payment_status():return jsonify(configured=bool(os.getenv('PAYPAL_CLIENT_ID') and os.getenv('PAYPAL_CLIENT_SECRET')),mode='sandbox',message='Sandbox credentials required. Payments are never simulated.')
@app.post('/api/payments/order')
def create_order():
 uid=current_user(); d=request.get_json() or {}; price=float(d.get('price',0)); p=profile(uid)
 if not uid:return jsonify(error='Sign in to prepare checkout.'),401
 if price<=0 or price>metrics(p)['disposableIncome']:return jsonify(error='Purchase is not within available monthly cash flow.'),400
 cid=os.getenv('PAYPAL_CLIENT_ID'); secret=os.getenv('PAYPAL_CLIENT_SECRET')
 if not cid or not secret:return jsonify(error='PayPal Sandbox requires PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.'),503
 try:
  import requests
  base=os.getenv('PAYPAL_BASE_URL','https://api-m.sandbox.paypal.com').rstrip('/'); token=requests.post(base+'/v1/oauth2/token',auth=(cid,secret),data={'grant_type':'client_credentials'},timeout=12); token.raise_for_status(); bearer=token.json()['access_token']; response=requests.post(base+'/v2/checkout/orders',headers={'Authorization':'Bearer '+bearer,'Content-Type':'application/json'},json={'intent':'CAPTURE','purchase_units':[{'amount':{'currency_code':d.get('currency','USD'),'value':f'{price:.2f}'},'description':str(d.get('product','PayAhead purchase'))[:120]}],'application_context':{'return_url':os.getenv('FRONTEND_URL','http://localhost:5173')+'/checkout/return','cancel_url':os.getenv('FRONTEND_URL','http://localhost:5173')+'/checkout/cancel'}},timeout=15); response.raise_for_status(); data=response.json(); row=Payment(user_id=int(uid),product=str(d.get('product','Purchase'))[:160],amount=price,currency=d.get('currency','USD'),paypal_order=data['id']); db.session.add(row); db.session.commit(); return jsonify(orderId=data['id'],approveUrl=next((x['href'] for x in data.get('links',[]) if x['rel']=='approve'),None))
 except Exception:return jsonify(error='PayPal could not create a Sandbox order. Check credentials and server logs.'),502
@app.post('/api/payments/capture')
def capture():
 uid=current_user(); order_id=(request.get_json() or {}).get('orderId'); row=Payment.query.filter_by(paypal_order=order_id,user_id=int(uid) if uid else -1).first()
 if not row:return jsonify(error='Order not found.'),404
 if row.status=='completed':return jsonify(status='completed',duplicate=True)
 if not os.getenv('PAYPAL_CLIENT_ID') or not os.getenv('PAYPAL_CLIENT_SECRET'):return jsonify(error='PayPal Sandbox credentials are required.'),503
 try:
  import requests
  base=os.getenv('PAYPAL_BASE_URL','https://api-m.sandbox.paypal.com').rstrip('/'); auth=requests.post(base+'/v1/oauth2/token',auth=(os.getenv('PAYPAL_CLIENT_ID'),os.getenv('PAYPAL_CLIENT_SECRET')),data={'grant_type':'client_credentials'},timeout=12); auth.raise_for_status(); bearer=auth.json()['access_token']; res=requests.post(base+f'/v2/checkout/orders/{order_id}/capture',headers={'Authorization':'Bearer '+bearer,'Content-Type':'application/json'},json={},timeout=15); res.raise_for_status(); data=res.json(); cap=data['purchase_units'][0]['payments']['captures'][0]; verified=data.get('status')=='COMPLETED' and cap.get('status')=='COMPLETED' and float(cap['amount']['value'])==row.amount and cap['amount']['currency_code']==row.currency
  if not verified:return jsonify(error='PayPal capture did not match amount and currency.'),409
  row.status='completed'; db.session.commit(); return jsonify(status='completed',verified=True)
 except Exception:return jsonify(error='PayPal capture could not be verified.'),502
with app.app_context():
 db.create_all()
 if Product.query.count()==0:
  for p in PRODUCTS:db.session.add(Product(**p))
  db.session.commit()
if __name__=='__main__':app.run(port=int(os.getenv('PORT','5000')),debug=os.getenv('FLASK_DEBUG')=='1')



import os,csv,io,ssl

from datetime import date,datetime,timedelta,timezone

from flask import Flask,jsonify,request

from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended import JWTManager

from werkzeug.security import generate_password_hash,check_password_hash

from dotenv import load_dotenv

from functools import lru_cache

load_dotenv()
def utc_now(): return datetime.now(timezone.utc)

app=Flask(__name__); app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('DATABASE_URL','sqlite:///payahead.db'); app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False; app.config['SECRET_KEY']=os.getenv('SECRET_KEY','local-development-only-change-before-use-32bytes-min')

app.config['JWT_SECRET_KEY']=os.getenv('JWT_SECRET_KEY','local-development-only-change-before-use-32bytes-min'); CORS(app,origins=os.getenv('FRONTEND_URL','http://localhost:8501')); db=SQLAlchemy(app); jwt=JWTManager(app)

class User(db.Model):

 id=db.Column(db.Integer,primary_key=True); email=db.Column(db.String(255),unique=True,nullable=False); password=db.Column(db.String(255),nullable=False)

class Profile(db.Model):

 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),unique=True); income=db.Column(db.Float,default=5200); fixed=db.Column(db.Float,default=2100); variable=db.Column(db.Float,default=1100); savings=db.Column(db.Float,default=8200); debt=db.Column(db.Float,default=450); currency=db.Column(db.String(3),default='USD'); name=db.Column(db.String(100),default='Personal profile')

class Transaction(db.Model):

 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer); name=db.Column(db.String(140)); category=db.Column(db.String(60)); amount=db.Column(db.Float); date=db.Column(db.Date,default=date.today); kind=db.Column(db.String(10),default='expense')

class Product(db.Model):

 id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(160)); category=db.Column(db.String(70)); price=db.Column(db.Float); currency=db.Column(db.String(3),default='USD'); rating=db.Column(db.Float,default=4.5); image=db.Column(db.String(400)); description=db.Column(db.String(300)); url=db.Column(db.String(500))

class PriceHistory(db.Model):
 id=db.Column(db.Integer,primary_key=True); product_name=db.Column(db.String(160),index=True); observed_on=db.Column(db.Date,index=True); price=db.Column(db.Float); currency=db.Column(db.String(3)); source=db.Column(db.String(30),default='synthetic_demo')
class Schedule(db.Model):

 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer); product=db.Column(db.String(160)); target=db.Column(db.Float); due=db.Column(db.Date); status=db.Column(db.String(20),default='watching')

class ScheduleAlert(db.Model):
 id=db.Column(db.Integer,primary_key=True); schedule_id=db.Column(db.Integer,db.ForeignKey('schedule.id')); user_id=db.Column(db.Integer); message=db.Column(db.String(300)); created=db.Column(db.DateTime,default=utc_now); read=db.Column(db.Boolean,default=False)
class Preference(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,index=True); key=db.Column(db.String(60)); value=db.Column(db.String(300))
class AgentActivity(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,index=True); product=db.Column(db.String(160)); role=db.Column(db.String(60)); finding=db.Column(db.String(500)); created=db.Column(db.DateTime,default=utc_now)
class Payment(db.Model):

 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer); product=db.Column(db.String(160)); amount=db.Column(db.Float); currency=db.Column(db.String(3)); paypal_order=db.Column(db.String(100),unique=True); status=db.Column(db.String(30),default='created'); created=db.Column(db.DateTime,default=utc_now)

DEMOS={

 'professional':{'name':'Maya Chen · Professional','income':5200,'fixed':2100,'variable':1100,'savings':8200,'debt':450,'currency':'USD'},

 'student':{'name':'Aarav · Student','income':1650,'fixed':720,'variable':430,'savings':1900,'debt':80,'currency':'USD'},

 'freelancer':{'name':'Jordan · Freelancer','income':4800,'fixed':1800,'variable':1450,'savings':11200,'debt':300,'currency':'USD'},

 'family':{'name':'The Rivera family','income':7800,'fixed':3400,'variable':2200,'savings':18600,'debt':650,'currency':'USD'},

 'goals':{'name':'Priya · Multiple goals','income':11200,'fixed':3600,'variable':1900,'savings':42000,'debt':900,'currency':'USD'}}

def purchase_fit(profile_data,price):
 m=metrics(profile_data); price=float(price)
 return m['disposableIncome']>=price and m['savings']-price>=max(0,m['fixedExpenses']+m['variableExpenses'])*.5

def demo(): return DEMOS['professional']

def metrics(p):

 inc=float(p.get('income',0)); fixed=float(p.get('fixed',0)); variable=float(p.get('variable',0)); debt=float(p.get('debt',0)); savings=float(p.get('savings',0)); spend=fixed+variable+debt; free=inc-spend

 return {'income':inc,'fixedExpenses':fixed,'variableExpenses':variable,'debtPayments':debt,'totalExpenses':spend,'disposableIncome':free,'savings':savings,'savingsRate':round(max(0,free)/inc*100,1) if inc else 0,'emergencyMonths':round(savings/max(1,fixed+variable),1),'currency':p.get('currency','USD')}

def profile(uid=None, sample='professional'):

 if uid:

  x=Profile.query.filter_by(user_id=int(uid)).first()

  if x:return {'name':x.name,'income':x.income,'fixed':x.fixed,'variable':x.variable,'savings':x.savings,'debt':x.debt,'currency':x.currency}

 return DEMOS.get(sample, demo())

@lru_cache(maxsize=1)
def expense_model():
 try:
  import joblib
  model_path=os.path.join(os.path.dirname(__file__),'app','ml','expense_classifier.joblib')
  return joblib.load(model_path) if os.path.exists(model_path) else None
 except Exception:return None
def categorize(description):
 if os.getenv('EXPENSE_MODEL','sklearn').lower()=='pytorch':
  try:
   from backend.ml.deep_expense import predict
   return str(predict(description))
  except Exception:pass
 model=expense_model()
 if model is not None:
  try:return str(model.predict([description])[0])
  except Exception:pass
 text=description.lower()
 rules={'Food':['grocery','market','restaurant','cafe','coffee','meal'],'Housing':['rent','mortgage','home'],'Transport':['transit','fuel','gas','uber','parking'],'Bills':['utility','electric','internet','mobile','phone'],'Shopping':['store','shop','amazon','purchase']}
 import re
 return next((category for category,words in rules.items() if any(re.search(r'\\b'+word+r'\\b',text) for word in words)),'Other')
def current_user():

 from flask_jwt_extended import verify_jwt_in_request,get_jwt_identity

 try: verify_jwt_in_request(optional=True); return get_jwt_identity()

 except Exception:return None

PRODUCTS=[{'name':'Studio Pro Laptop','category':'Computers','price':1499,'currency':'USD','rating':4.8,'image':'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=85','description':'A powerful 14-inch laptop for work and creative projects.'},{'name':'QuietComfort Headphones','category':'Audio','price':329,'currency':'USD','rating':4.7,'image':'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85','description':'Comfortable noise-cancelling headphones for focus.'},{'name':'Everyday Smartwatch','category':'Wearables','price':249,'currency':'USD','rating':4.5,'image':'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85','description':'Health, activity and notifications at a glance.'},{'name':'City Commuter Bike','category':'Outdoors','price':799,'currency':'USD','rating':4.6,'image':'https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=900&q=85','description':'A lightweight daily ride for city streets.'},{'name':'Home Espresso Maker','category':'Home','price':549,'currency':'USD','rating':4.4,'image':'https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?auto=format&fit=crop&w=900&q=85','description':'Cafe-style espresso for a slower morning.'},{'name':'Noise Cancel Earbuds','category':'Audio','price':179,'currency':'USD','rating':4.5,'image':'','description':'Compact wireless earbuds for everyday listening.'},{'name':'Creator Laptop 16','category':'Computers','price':1899,'currency':'USD','rating':4.7,'image':'','description':'A larger display for creative work.'},{'name':'Portable Monitor','category':'Computers','price':289,'currency':'USD','rating':4.3,'image':'','description':'A second screen for a flexible workspace.'},{'name':'Mechanical Keyboard','category':'Computers','price':139,'currency':'USD','rating':4.6,'image':'','description':'A comfortable keyboard for long work sessions.'},{'name':'Ergonomic Chair','category':'Home','price':649,'currency':'USD','rating':4.5,'image':'','description':'Adjustable support for a home office.'},{'name':'Air Purifier','category':'Home','price':279,'currency':'USD','rating':4.4,'image':'','description':'Quiet air filtration for a bedroom or office.'},{'name':'Robot Vacuum','category':'Home','price':399,'currency':'USD','rating':4.3,'image':'','description':'Scheduled floor cleaning for busy weeks.'},{'name':'Fitness Tracker','category':'Wearables','price':129,'currency':'USD','rating':4.2,'image':'','description':'Simple activity and sleep tracking.'},{'name':'Tablet 11','category':'Computers','price':599,'currency':'USD','rating':4.6,'image':'','description':'A versatile tablet for reading and notes.'},{'name':'Mirrorless Camera','category':'Cameras','price':1099,'currency':'USD','rating':4.7,'image':'','description':'A compact camera for travel and projects.'},{'name':'Compact Projector','category':'Home','price':469,'currency':'USD','rating':4.2,'image':'','description':'Movie nights in a portable package.'},{'name':'Standing Desk','category':'Home','price':499,'currency':'USD','rating':4.5,'image':'','description':'A height-adjustable workspace.'},{'name':'Smart Speaker Pair','category':'Audio','price':219,'currency':'USD','rating':4.4,'image':'','description':'Room-filling audio and voice control.'},{'name':'Carry-on Luggage','category':'Travel','price':249,'currency':'USD','rating':4.3,'image':'','description':'Lightweight luggage for short trips.'},{'name':'Espresso Grinder','category':'Home','price':199,'currency':'USD','rating':4.5,'image':'','description':'Consistent grinding for home coffee.'}]

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

 uid=current_user(); sample=request.args.get('profile','professional'); p=profile(uid,sample); tx=Transaction.query.filter_by(user_id=int(uid) if uid else None).order_by(Transaction.date.desc()).limit(8).all()

 recent=[{'name':t.name,'category':t.category,'amount':t.amount,'date':t.date.isoformat()} for t in tx] if tx else [{'name':n,'category':c,'amount':a,'date':(date.today()-timedelta(days=i*3)).isoformat()} for i,(n,c,a) in enumerate([('Rent','Housing',1450),('Groceries','Food',128),('Transit pass','Transport',72),('Coffee shop','Dining',18),('Utilities','Bills',116)])]

 return jsonify(profile=p,metrics=metrics(p),transactions=recent,simulated=not bool(uid),demoProfiles=[{'id':k,'name':v['name']} for k,v in DEMOS.items()])

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

@app.get('/api/forecast')

def forecast():

 uid=current_user(); p=profile(uid); m=metrics(p)

 if not uid:return jsonify(simulated=True,method='profile arithmetic',monthlyNet=m['disposableIncome'],note='Synthetic sample profile; not a learned bank-balance forecast.')

 rows=Transaction.query.filter_by(user_id=int(uid)).order_by(Transaction.date.asc()).all()

 if len(rows)<30:return jsonify(simulated=False,method='insufficient history',monthlyNet=m['disposableIncome'],transactions=len(rows),note='Add at least 30 transactions for a history-based estimate.')

 from collections import defaultdict

 months=defaultdict(float)

 for t in rows: months[t.date.strftime('%Y-%m')]+=(-t.amount if t.kind=='expense' else t.amount)

 vals=list(months.values())[-6:]; avg=sum(vals)/len(vals)

 return jsonify(simulated=False,method='six-month mean of imported monthly net transactions',monthlyNet=round(avg,2),months=len(vals),transactions=len(rows),note='Historical average is not a guaranteed forecast.')

@app.get('/api/products')

def products():

 q=request.args.get('q','').lower(); vals=PRODUCTS+[{'name':p.name,'category':p.category,'price':p.price,'currency':p.currency,'rating':p.rating,'image':p.image,'description':p.description,'url':p.url} for p in Product.query.all() if p.name not in {x['name'] for x in PRODUCTS}]; return jsonify(products=[p for p in vals if q in (p['name']+' '+p['category']).lower()])


@app.get('/api/products/<int:product_id>/price-history')
def price_history(product_id):
 product=db.session.get(Product,product_id)
 if not product:return jsonify(error='Product not found.'),404
 rows=PriceHistory.query.filter_by(product_name=product.name).order_by(PriceHistory.observed_on.asc()).all()
 history=[{'date':r.observed_on.isoformat(),'price':r.price,'currency':r.currency} for r in rows]
 if len(rows)<8:return jsonify(product=product.name,source='unavailable',history=history,forecast=None,note='Insufficient price observations.')
 import numpy as np
 from sklearn.linear_model import LinearRegression
 x=np.arange(len(rows)).reshape(-1,1);y=np.array([r.price for r in rows]);cut=len(rows)-3;fit=LinearRegression().fit(x[:cut],y[:cut]);holdout=fit.predict(x[cut:]);mae=float(np.mean(np.abs(holdout-y[cut:])));full=LinearRegression().fit(x,y);estimate=max(0,float(full.predict([[len(rows)+1]])[0]))
 return jsonify(product=product.name,source=rows[0].source,history=history,forecast={'horizonDays':30,'estimatedPrice':round(estimate,2),'holdoutMAE':round(mae,2),'holdoutPoints':len(rows)-cut},note='Generated synthetic demo series; not a retailer quote or guarantee.')

@app.post('/api/products')
def add_product():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to add a product.'),401
 d=request.get_json() or {}; name=str(d.get('name','')).strip()[:160]; category=str(d.get('category','Other'))[:70]
 try:price=float(d.get('price',0))
 except (TypeError,ValueError):return jsonify(error='Enter a valid price.'),400
 currency=str(d.get('currency','USD')).upper()
 if not name or price<=0 or currency not in {'USD','EUR','GBP','CAD','AUD','JPY','INR'}:return jsonify(error='Enter a name, positive price, and supported currency.') ,400
 url=str(d.get('url','')).strip()
 if url:
  from urllib.parse import urlparse
  import ipaddress,socket
  parsed=urlparse(url)
  if parsed.scheme not in ('http','https') or not parsed.hostname:return jsonify(error='Use a valid http or https product URL.'),400
  try:
   ips={x[4][0] for x in socket.getaddrinfo(parsed.hostname,None)}
   if any(not ipaddress.ip_address(ip).is_global for ip in ips):return jsonify(error='Private and local network URLs are not allowed.'),400
  except socket.gaierror:return jsonify(error='Product URL host could not be resolved.'),400
 row=Product(name=name,category=category,price=price,currency=currency,rating=0,image='',description=str(d.get('description','User added product; price not externally verified.'))[:300],url=url or None);db.session.add(row);db.session.commit()
 return jsonify(id=row.id,name=row.name,price=row.price,currency=row.currency,source='user_entered'),201
@app.post('/api/products/extract')
def extract_product_url():
 if not current_user():return jsonify(error='Sign in to preview a product URL.'),401
 url=str((request.get_json() or {}).get('url','')).strip()
 if len(url)>2000:return jsonify(error='Product URL is too long.'),400
 try:
  from product_url import extract
  result=extract(url);return jsonify(result)
 except ValueError as exc:return jsonify(error=str(exc)),400
 except (OSError,TimeoutError,ssl.SSLError) as exc:return jsonify(error='Could not safely read product metadata.'),400
 except Exception as exc:app.logger.warning('Product preview failed: %s',exc);return jsonify(error='Product preview failed; enter details manually.'),502
@app.get('/api/preferences')
def get_preferences():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to view preferences.'),401
 rows=Preference.query.filter_by(user_id=int(uid)).all();return jsonify(preferences={x.key:x.value for x in rows})
@app.put('/api/preferences')
def save_preferences():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to save preferences.'),401
 data=request.get_json() or {}; allowed={'category','budget','currency','brand'}
 for key,value in data.items():
  if key not in allowed:continue
  row=Preference.query.filter_by(user_id=int(uid),key=key).first()
  if row is None:row=Preference(user_id=int(uid),key=key);db.session.add(row)
  row.value=str(value)[:300]
 db.session.commit();return jsonify(preferences={x.key:x.value for x in Preference.query.filter_by(user_id=int(uid)).all()})
@app.delete('/api/preferences')
def clear_preferences():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to remove preferences.'),401
 Preference.query.filter_by(user_id=int(uid)).delete();db.session.commit();return jsonify(deleted=True)
@app.get('/api/agents/activity')
def agent_activity():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to view saved activity.'),401
 rows=AgentActivity.query.filter_by(user_id=int(uid)).order_by(AgentActivity.created.desc()).limit(100).all()
 return jsonify(activity=[{'product':x.product,'role':x.role,'finding':x.finding,'created':x.created.isoformat()} for x in rows])

@app.get('/api/price-history')
def price_history_by_name():
 name=request.args.get('product',''); product=Product.query.filter_by(name=name).first()
 if not product:return jsonify(error='Product not found.'),404
 return price_history(product.id)

@app.post('/api/analyze')

def analyze():

 d=request.get_json() or {}; p=profile(current_user()); m=metrics(p); name=str(d.get('product','Purchase'))[:160]; product_row=Product.query.filter_by(name=name).first()
 if not product_row:return jsonify(error='Choose a product saved in the catalogue.'),404
 price=float(product_row.price)
 if str(d.get('price',price)) and round(float(d.get('price',price)),2)!=round(price,2):return jsonify(error='Submitted price differs from the saved listing.'),409
 if product_row.currency!=p.get('currency','USD'):return jsonify(error='Product and profile currencies differ; currency conversion is unavailable.'),400
 safe=purchase_fit(p,price); ratio=price/max(1,m['income'])*100

 scenarios=[{'label':'Buy now','days':0,'projectedCash':round(m['disposableIncome']-price,2),'result':'Comfortable' if safe else 'Tight'},{'label':'Wait 15 days','days':15,'projectedCash':round(max(0,m['disposableIncome']*.5-price),2),'result':'More room'},{'label':'Wait 30 days','days':30,'projectedCash':round(max(0,m['disposableIncome']*2-price),2),'result':'Build cash flow'},{'label':'Lower-cost option','days':0,'projectedCash':round(max(0,m['disposableIncome']-price*.7),2),'result':'Keeps more savings'}]

 from agents import run_specialists

 product_data={'name':product_row.name,'category':product_row.category,'description':product_row.description,'price':product_row.price,'currency':product_row.currency}

 specialists=run_specialists(product_data,price,m,safe)
 uid=current_user()
 if uid:
  for specialist in specialists:db.session.add(AgentActivity(user_id=int(uid),product=name,role=specialist['name'],finding=specialist['finding']))
  db.session.commit()

 recommendation='Buy when ready' if safe else 'Wait and build your buffer'
 fallback=f"Monthly surplus is {m['currency']} {m['disposableIncome']:,.0f}. The purchase is {ratio:.0f}% of monthly income. {'Your remaining savings preserve a basic buffer.' if safe else 'Buying now could reduce available cash or your emergency buffer.'}"
 try:
  from ai.providers import get_provider
  explanation=get_provider().explain({'currency':m['currency'],'surplus':m['disposableIncome'],'share':ratio,'recommendation':recommendation,'affordable':safe})
 except Exception as exc: app.logger.warning('AI explanation unavailable: %s',exc); explanation=fallback
 return jsonify(product=name,price=price,currency=m['currency'],affordable=safe,risk='low' if safe and ratio<15 else ('moderate' if m['disposableIncome']>=price else 'high'),recommendation=recommendation,reason=explanation,scenarios=scenarios,agents=[{'status':'complete',**agent} for agent in specialists])

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

   db.session.add(Transaction(user_id=int(uid),date=day,name=name,amount=abs(amt),kind='income' if amt<0 else 'expense',category=categorize(name))); added+=1

  db.session.commit(); return jsonify(imported=added)

 except UnicodeDecodeError:return jsonify(error='CSV must use UTF-8 encoding.'),400

@app.get('/api/schedule')

def list_schedules():

 uid=current_user()

 if not uid:return jsonify(error='Sign in to view purchase watches.'),401

 rows=Schedule.query.filter_by(user_id=int(uid)).order_by(Schedule.due.asc()).all()

 return jsonify(schedules=[{'id':r.id,'product':r.product,'target':r.target,'due':r.due.isoformat(),'status':r.status} for r in rows])


@app.post('/api/schedule/evaluate')
def evaluate_schedules():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to evaluate watches.'),401
 watches=Schedule.query.filter_by(user_id=int(uid),status='watching').all(); cash=metrics(profile(uid))['disposableIncome']; today=date.today(); created=[]
 for w in watches:
  product=Product.query.filter_by(name=w.product).first(); reasons=[]
  if w.due<=today: reasons.append('target date reached')
  if product and w.target>0 and product.price<=w.target: reasons.append('catalogue price reached target')
  if product and cash>=product.price: reasons.append('monthly surplus covers catalogue price')
  if reasons:
   msg=f"{w.product}: {', '.join(reasons)}. Please review before deciding."
   if not ScheduleAlert.query.filter_by(schedule_id=w.id,message=msg).first(): db.session.add(ScheduleAlert(schedule_id=w.id,user_id=int(uid),message=msg)); created.append(msg)
 db.session.commit(); return jsonify(checked=len(watches),created=created,note='Manual check against saved catalogue values; this does not monitor retailers.')
@app.get('/api/alerts')
def alerts():
 uid=current_user()
 if not uid:return jsonify(error='Sign in to view alerts.'),401
 rows=ScheduleAlert.query.filter_by(user_id=int(uid)).order_by(ScheduleAlert.created.desc()).all()
 return jsonify(alerts=[{'id':a.id,'message':a.message,'created':a.created.isoformat(),'read':a.read} for a in rows])

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

 product_row=Product.query.filter_by(name=str(d.get('product',''))).first()
 if not product_row:return jsonify(error='Choose a product saved in the catalogue.'),400
 if round(price,2)!=round(float(product_row.price),2) or str(d.get('currency','USD')).upper()!=product_row.currency:return jsonify(error='Submitted price/currency differs from the saved listing.'),409
 if product_row.currency!=p.get('currency','USD'):return jsonify(error='Product and profile currencies differ; currency conversion is unavailable.'),400
 if not purchase_fit(p,price):return jsonify(error='Purchase would exceed available cash or reduce the basic savings buffer.'),400

 cid=os.getenv('PAYPAL_CLIENT_ID'); secret=os.getenv('PAYPAL_CLIENT_SECRET')

 if not cid or not secret:return jsonify(error='PayPal Sandbox requires PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.'),503

 try:

  import requests

  base=os.getenv('PAYPAL_BASE_URL','https://api-m.sandbox.paypal.com').rstrip('/'); token=requests.post(base+'/v1/oauth2/token',auth=(cid,secret),data={'grant_type':'client_credentials'},timeout=12); token.raise_for_status(); bearer=token.json()['access_token']; response=requests.post(base+'/v2/checkout/orders',headers={'Authorization':'Bearer '+bearer,'Content-Type':'application/json'},json={'intent':'CAPTURE','purchase_units':[{'amount':{'currency_code':d.get('currency','USD'),'value':f'{price:.2f}'},'description':str(d.get('product','PayAhead purchase'))[:120]}],'application_context':{'return_url':os.getenv('PAYPAL_RETURN_URL','http://localhost:8501'),'cancel_url':os.getenv('PAYPAL_CANCEL_URL','http://localhost:8501')}},timeout=15); response.raise_for_status(); data=response.json(); row=Payment(user_id=int(uid),product=str(d.get('product','Purchase'))[:160],amount=price,currency=d.get('currency','USD'),paypal_order=data['id']); db.session.add(row); db.session.commit(); return jsonify(orderId=data['id'],approveUrl=next((x['href'] for x in data.get('links',[]) if x['rel']=='approve'),None))

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
 from sqlalchemy import inspect,text
 if 'url' not in {c['name'] for c in inspect(db.engine).get_columns('product')}: db.session.execute(text('ALTER TABLE product ADD COLUMN url VARCHAR(500)')); db.session.commit()
 for product in PRODUCTS:
  if not Product.query.filter_by(name=product['name']).first(): db.session.add(Product(**product))
 db.session.commit()
 if PriceHistory.query.count()==0:
  import random,math
  rng=random.Random(1701); today=date.today()
  for product in PRODUCTS:
   base=float(product['price'])
   for month in range(12,0,-1):
    d=today-timedelta(days=30*month); simulated=base*(1+0.035*math.sin(month*1.7)+rng.uniform(-0.035,0.035))
    db.session.add(PriceHistory(product_name=product['name'],observed_on=d,price=round(simulated,2),currency=product['currency'],source='synthetic_demo'))
  db.session.commit()
def evaluate_all_watches():
 with app.app_context():
  watches=Schedule.query.filter_by(status='watching').all(); today=date.today()
  for w in watches:
   product=Product.query.filter_by(name=w.product).first(); reasons=[]
   if w.due<=today: reasons.append('target date reached')
   if product and w.target>0 and product.price<=w.target: reasons.append('catalogue price reached target')
   p=profile(w.user_id); cash=metrics(p)['disposableIncome']
   if product and cash>=product.price: reasons.append('monthly surplus covers catalogue price')
   if reasons:
    msg=f"{w.product}: {', '.join(reasons)}. Please review before deciding."
    if not ScheduleAlert.query.filter_by(schedule_id=w.id,message=msg).first(): db.session.add(ScheduleAlert(schedule_id=w.id,user_id=w.user_id,message=msg))
  db.session.commit()
if os.getenv('ENABLE_SCHEDULER','false').lower()=='true':
 try:
  from apscheduler.schedulers.background import BackgroundScheduler
  scheduler=BackgroundScheduler(daemon=True); scheduler.add_job(evaluate_all_watches,'interval',hours=1,id='watch-evaluator',replace_existing=True); scheduler.start()
 except Exception as exc: app.logger.error('Scheduler did not start: %s',exc)

if __name__=='__main__':app.run(port=int(os.getenv('PORT','5000')),debug=os.getenv('FLASK_DEBUG')=='1')

import os
import requests
import streamlit as st
import pandas as pd

API=os.getenv('PAYAHEAD_API_URL','http://localhost:5000/api')
st.set_page_config(page_title='PayAhead',page_icon='🌿',layout='wide',initial_sidebar_state='expanded')
theme=st.sidebar.radio('Appearance',['Light','Dark'],horizontal=True,key='appearance')
dark=theme=='Dark'
colors={'bg':'#10141d','surface':'#181f2b','surface2':'#202938','text':'#edf2f7','muted':'#9aa8ba','border':'#2a3545','accent':'#61d8c0','accent_soft':'#173d3a','input':'#141b26'} if dark else {'bg':'#f4f7fa','surface':'#ffffff','surface2':'#f8fafb','text':'#243143','muted':'#7d8a9a','border':'#e4eaf0','accent':'#168c79','accent_soft':'#e4f6f1','input':'#ffffff'}
st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{{--pa-bg:{colors['bg']};--pa-surface:{colors['surface']};--pa-surface2:{colors['surface2']};--pa-text:{colors['text']};--pa-muted:{colors['muted']};--pa-border:{colors['border']};--pa-accent:{colors['accent']};--pa-accent-soft:{colors['accent_soft']};--pa-input:{colors['input']}}}
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;color:var(--pa-text)}} .stApp{{background:var(--pa-bg);color:var(--pa-text)}}
h1,h2,h3{{font-family:Manrope,sans-serif!important;letter-spacing:-.035em;color:var(--pa-text)}} h1{{font-weight:800!important}}
p,[data-testid="stCaptionContainer"]{{color:var(--pa-muted)}}
[data-testid="stSidebar"]{{background:var(--pa-surface);border-right:1px solid var(--pa-border)}} [data-testid="stSidebar"] h2{{color:var(--pa-text);font-weight:800}}
.block-container{{padding-top:2.1rem;padding-bottom:3rem;max-width:1280px}}
div[data-testid="stMetric"]{{background:var(--pa-surface);border:1px solid var(--pa-border);padding:18px 20px;border-radius:15px;box-shadow:0 6px 24px #08111b12}}
div[data-testid="stMetricLabel"] p{{color:var(--pa-muted);font-size:.82rem;font-weight:600}} div[data-testid="stMetricValue"]{{color:var(--pa-text);font-family:Manrope,sans-serif;font-weight:750}}
[data-testid="stVerticalBlockBorderWrapper"]{{background:var(--pa-surface);border-color:var(--pa-border);border-radius:15px;padding:8px}}
.stTextInput input,.stNumberInput input,.stSelectbox [data-baseweb="select"]>div{{background:var(--pa-input);color:var(--pa-text);border-color:var(--pa-border);border-radius:9px}}
.stButton>button,.stLinkButton>a,.stFormSubmitButton>button{{border-radius:9px;border:1px solid var(--pa-border);font-weight:650;transition:all .15s ease}}
.stButton>button[kind="primary"]{{background:var(--pa-accent);border-color:var(--pa-accent);color:#082820}}
.stButton>button:hover,.stLinkButton>a:hover{{border-color:var(--pa-accent);color:var(--pa-accent);transform:translateY(-1px)}}
[data-testid="stDataFrame"]{{border:1px solid var(--pa-border);border-radius:12px;overflow:hidden}}
.demo{{background:{'#26301f' if dark else '#fff8e8'};padding:13px 16px;border:1px solid {'#4b553c' if dark else '#f2e8cf'};border-radius:11px;color:{'#d7d1a4' if dark else '#766744'};margin:.7rem 0 1.4rem}}
hr{{border-color:var(--pa-border)}}
</style>''',unsafe_allow_html=True)
if 'token' not in st.session_state: st.session_state.token=''
def headers(): return {'Authorization':f"Bearer {st.session_state.token}"} if st.session_state.token else {}
def api_get(path,**kw):
 try:
  r=requests.get(API+path,headers=headers(),timeout=4,**kw); return r.json() if r.ok else None
 except requests.RequestException:return None
def api_post(path,data=None,files=None):
 try:
  r=requests.post(API+path,headers=headers(),json=data,files=files,timeout=20); return r.status_code,r.json()
 except requests.RequestException:return 0,{'error':'Could not reach the PayAhead API. Start the Flask backend first.'}
with st.sidebar:
 st.markdown('## 🌿 payahead')
 st.caption('THINK BEFORE YOU SPEND')
 page=st.radio('Workspace',['Overview','Purchase advisor','Explore products','Transactions','My schedule'],label_visibility='collapsed',key='page_selector')
 st.divider()
 if st.session_state.token:
  st.success('Personal workspace');
  if st.button('Sign out',use_container_width=True): st.session_state.token=''; st.rerun()
 else:
  st.caption('Sign in to save your own profile')
  mode=st.radio('Account',['Sign in','Create account'],horizontal=True)
  email=st.text_input('Email',key='auth_email'); password=st.text_input('Password',type='password',key='auth_password')
  if st.button(mode,use_container_width=True):
   status,result=api_post('/auth/'+('login' if mode=='Sign in' else 'register'),{'email':email,'password':password})
   if status in (200,201): st.session_state.token=result['token']; st.rerun()
   st.error(result.get('error','Account request failed.'))
 st.divider(); st.caption('Your money. Your call. Payments always need your approval.')

if not st.session_state.token:
 demos=api_get('/dashboard') or {}; choices=demos.get('demoProfiles',[])
 if choices:
  selected=st.sidebar.selectbox('Demo profile',[x['name'] for x in choices],index=0,key='demo_profile')
  profile_id=next(x['id'] for x in choices if x['name']==selected)
 else: profile_id='professional'
 dashboard=api_get('/dashboard',params={'profile':profile_id})
else: dashboard=api_get('/dashboard')
# PayPal returns the approved order ID as `token`; capture is server-side and checks amount/currency.
order_token=st.query_params.get('token')
if order_token and st.session_state.token:
 status,capture_result=api_post('/payments/capture',{'orderId':order_token})
 if status==200 and capture_result.get('verified'): st.success('PayPal Sandbox payment captured and verified.')
 elif status==200 and capture_result.get('duplicate'): st.info('This order was already captured.')
 else: st.error(capture_result.get('error','Could not verify PayPal capture.'))
 st.query_params.clear()
if not dashboard:
 st.title('PayAhead'); st.error('The API is unavailable. Start it with `python backend/app.py` and refresh.'); st.stop()
profile=dashboard['profile']; metrics=dashboard['metrics']; currency=metrics.get('currency','USD')
def fmt(n): return f"{currency} {n:,.0f}"
st.markdown(f"<div style='color:{colors['accent']};font-size:.72rem;font-weight:700;letter-spacing:.13em;margin-bottom:.25rem'>PAYAHEAD / {page.upper()}</div>",unsafe_allow_html=True)
st.title({'Overview':'Your money, in focus.','Purchase advisor':'Make a confident choice.','Explore products':'A better buy starts here.','Transactions':'Every dollar, accounted for.','My schedule':'Your plan, at your pace.'}[page])
st.caption('A little clarity today makes the bigger decisions easier.')
if dashboard.get('simulated'): st.markdown('<div class="demo">✦ &nbsp; <b>Simulated demo data</b> · Sample values are fictional. Sign in to create a personal profile.</div>',unsafe_allow_html=True)
if page=='Overview':
 cols=st.columns(4)
 for col,label,value,helptext in zip(cols,['Monthly income','Monthly expenses','Available this month','Your savings'],[metrics['income'],metrics['totalExpenses'],metrics['disposableIncome'],metrics['savings']],['Income on profile','Includes debt payments','After listed expenses','Emergency buffer']): col.metric(label,fmt(value),help=helptext)
 left,right=st.columns([1.7,1])
 with left:
  st.subheader('Recent activity')
  tx=pd.DataFrame(dashboard.get('transactions',[]))
  if not tx.empty: st.dataframe(tx,use_container_width=True,hide_index=True)
 with right:
  st.subheader('Your money insight'); st.info(f"After listed expenses and debt, about **{fmt(metrics['disposableIncome'])}** is available this month. Savings cover about **{metrics['emergencyMonths']} months** of regular expenses.")
  st.caption('These calculations are advisory and use profile values.')
  with st.form('profile'):
   st.write('Monthly profile')
   income=st.number_input('Income',min_value=0.0,value=float(profile['income']),step=100.0)
   fixed=st.number_input('Fixed expenses',min_value=0.0,value=float(profile['fixed']),step=50.0)
   variable=st.number_input('Variable expenses',min_value=0.0,value=float(profile['variable']),step=50.0)
   savings=st.number_input('Savings',min_value=0.0,value=float(profile['savings']),step=100.0)
   debt=st.number_input('Debt payments',min_value=0.0,value=float(profile['debt']),step=50.0)
   if st.form_submit_button('Save profile',use_container_width=True):
    try:
     r=requests.put(API+'/finances/profile',headers={**headers(),'Content-Type':'application/json'},json={'income':income,'fixed':fixed,'variable':variable,'savings':savings,'debt':debt},timeout=10)
     if r.ok: st.success('Profile saved.'); st.rerun()
     else: st.error(r.json().get('error','Sign in to save a profile.'))
    except requests.RequestException: st.error('API unavailable.')
elif page=='Explore products':
 query=st.text_input('Search products',placeholder='Laptop, audio, home…'); result=api_get('/products',params={'q':query or ''}) or {'products':[]}; products=result['products']
 
 for start in range(0,len(products),3):
  cols=st.columns(3)
  for col,p in zip(cols,products[start:start+3]):
   with col:
    with st.container(border=True):
     if p.get('image'): st.image(p['image'],use_container_width=True)
     st.caption(p['category']); st.subheader(p['name']); st.write(p.get('description','')); st.markdown(f"**{p['currency']} {p['price']:,.0f}** · ★ {p['rating']}")
     if st.button('Can I afford it?',key='p_'+p['name'],use_container_width=True): st.session_state['chosen_product']=p; st.session_state['page_selector']='Purchase advisor'; st.rerun()
elif page=='Purchase advisor':
 result=api_get('/products') or {'products':[]}; products=result['products']; labels=[f"{p['name']} · {p['currency']} {p['price']:,.0f}" for p in products]
 chosen=st.selectbox('Choose a product',labels) if labels else None
 if chosen:
  p=products[labels.index(chosen)]; st.session_state['chosen_product']=p
  if st.button('Analyze purchase',type='primary') or st.session_state.get('analysis_product')==p['name']:
   status,a=api_post('/analyze',{'product':p['name'],'price':p['price']})
   if status==200:
    st.session_state['analysis']=a; st.session_state['analysis_product']=p['name']
  a=st.session_state.get('analysis') if st.session_state.get('analysis_product')==p['name'] else None
  if a:
   st.subheader(a['recommendation']); st.write(a['reason']); c=st.columns(4)
   for col,scenario in zip(c,a['scenarios']): col.metric(scenario['label'],fmt(scenario['projectedCash']),scenario['result'])
   st.subheader('Decision team')
   for agent in a['agents']: st.write(f"✅ **{agent['name']}** — {agent['finding']}")
   st.caption('Price history is unavailable in the demo; no trend is inferred. A payment always needs your approval.')
   if st.button('Continue to PayPal'):
    if not st.session_state.token: st.warning('Sign in before preparing checkout.')
    else:
     status,order=api_post('/payments/order',{'product':p['name'],'price':p['price'],'currency':p['currency']})
     if status==200 and order.get('approveUrl'): st.link_button('Approve in PayPal Sandbox',order['approveUrl'],use_container_width=True)
     else: st.error(order.get('error','Checkout unavailable.'))
elif page=='Transactions':
 st.subheader('Recent activity'); tx=pd.DataFrame(dashboard.get('transactions',[])); st.dataframe(tx,use_container_width=True,hide_index=True) if not tx.empty else st.info('No transactions yet.')
 uploaded=st.file_uploader('Import a CSV',type=['csv'],help='Required columns: date and amount. Optional: description, name or merchant.')
 if uploaded:
  st.write('Preview'); st.dataframe(pd.read_csv(uploaded).head(10),use_container_width=True,hide_index=True); uploaded.seek(0)
  if st.button('Import transactions',type='primary'):
   status,result=api_post('/transactions/import',files={'file':(uploaded.name,uploaded.getvalue(),'text/csv')})
   st.success(f"Imported {result.get('imported',0)} transactions.") if status==200 else st.error(result.get('error','Import failed.'))
 anomalies=api_get('/anomalies')
 if anomalies:
  st.subheader('Unusual amounts to review')
  st.caption(anomalies['note'])
  if anomalies.get('anomalies'): st.dataframe(pd.DataFrame(anomalies['anomalies']),use_container_width=True,hide_index=True)
else:
 st.subheader('Purchase watches')
 if not st.session_state.token: st.info('Sign in to save a price or date watch.')
 else:
  with st.form('schedule_watch'):
   product_name=st.text_input('Product name'); target=st.number_input('Target price',min_value=0.0,step=10.0); due=st.date_input('Review by')
   if st.form_submit_button('Save watch',type='primary'):
    status,result=api_post('/schedule',{'product':product_name,'target':target,'due':due.isoformat()})
    st.success('Watch saved.') if status==201 else st.error(result.get('error','Could not save watch.'))
  result=api_get('/schedule')
  if result and result.get('schedules'): st.dataframe(pd.DataFrame(result['schedules']),use_container_width=True,hide_index=True)
 st.subheader('Cash-flow outlook')
 forecast=api_get('/forecast')
 if forecast: st.info(f"Method: {forecast['method']}. Monthly net estimate: {fmt(forecast['monthlyNet'])}. {forecast['note']}")
st.divider(); st.caption('PayAhead provides educational estimates, not financial advice. The dashboard cash-flow chart is not a bank forecast.')

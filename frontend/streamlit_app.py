import os
import requests
import streamlit as st
import pandas as pd

API=os.getenv('PAYAHEAD_API_URL','http://localhost:5000/api')
st.set_page_config(page_title='PayAhead',page_icon='🌿',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif} h1,h2,h3{font-family:Manrope,sans-serif!important;letter-spacing:-.03em} .stApp{background:#f7f8fb} [data-testid="stSidebar"]{background:#fff;border-right:1px solid #edf0f4} .block-container{padding-top:2rem;max-width:1240px} div[data-testid="stMetric"]{background:white;border:1px solid #edf0f4;padding:18px;border-radius:14px} .demo{background:#fff8e8;padding:12px 16px;border:1px solid #f2e8cf;border-radius:10px;color:#766744}
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
 page=st.radio('Workspace',['Overview','Purchase advisor','Explore products','Transactions','My schedule'],label_visibility='collapsed')
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

dashboard=api_get('/dashboard')
if not dashboard:
 st.title('PayAhead'); st.error('The API is unavailable. Start it with `python backend/app.py` and refresh.'); st.stop()
profile=dashboard['profile']; metrics=dashboard['metrics']; currency=metrics.get('currency','USD')
def fmt(n): return f"{currency} {n:,.0f}"
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
 for row in st.columns(3): pass
 for start in range(0,len(products),3):
  cols=st.columns(3)
  for col,p in zip(cols,products[start:start+3]):
   with col:
    with st.container(border=True):
     if p.get('image'): st.image(p['image'],use_container_width=True)
     st.caption(p['category']); st.subheader(p['name']); st.write(p.get('description','')); st.markdown(f"**{p['currency']} {p['price']:,.0f}** · ★ {p['rating']}")
     if st.button('Can I afford it?',key='p_'+p['name'],use_container_width=True): st.session_state['chosen_product']=p; st.session_state['page']='Purchase advisor'; st.rerun()
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
     if status==200 and order.get('approveUrl'): st.link_button('Approve in PayPal Sandbox',order['approveUrl'])
     else: st.error(order.get('error','Checkout unavailable.'))
elif page=='Transactions':
 st.subheader('Recent activity'); tx=pd.DataFrame(dashboard.get('transactions',[])); st.dataframe(tx,use_container_width=True,hide_index=True) if not tx.empty else st.info('No transactions yet.')
 uploaded=st.file_uploader('Import a CSV',type=['csv'],help='Required columns: date and amount. Optional: description, name or merchant.')
 if uploaded:
  st.write('Preview'); st.dataframe(pd.read_csv(uploaded).head(10),use_container_width=True,hide_index=True); uploaded.seek(0)
  if st.button('Import transactions',type='primary'):
   status,result=api_post('/transactions/import',files={'file':(uploaded.name,uploaded.getvalue(),'text/csv')})
   st.success(f"Imported {result.get('imported',0)} transactions.") if status==200 else st.error(result.get('error','Import failed.'))
else:
 st.subheader('Purchase watches'); st.info('Saved purchase watches are available to signed-in accounts through the API. Scheduling and notifications are not yet shown in this Streamlit view.')
st.divider(); st.caption('PayAhead provides educational estimates, not financial advice. The dashboard cash-flow chart is not a bank forecast.')

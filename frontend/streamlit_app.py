import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

REPO_ROOT=str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path: sys.path.insert(0,REPO_ROOT)
from frontend.local_api import request as local_request

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
 r=local_request('GET',path,headers=headers(),**kw); return r.json() if r.ok else None
def api_put(path,data):
 r=local_request('PUT',path,headers=headers(),json=data);return r.status_code,r.json()
def api_delete(path):
 r=local_request('DELETE',path,headers=headers());return r.status_code,r.json()
def api_post(path,data=None,files=None):
 normalized_files={key:(value[0],value[1] if isinstance(value[1],bytes) else value[1].getvalue(),value[2]) for key,value in (files or {}).items()}
 r=local_request('POST',path,headers=headers(),json=data,files=normalized_files or None); return r.status_code,r.json()
with st.sidebar:
 st.markdown('## 🌿 payahead')
 st.caption('THINK BEFORE YOU SPEND')
 page=st.radio('Workspace',['Overview','Purchase advisor','Explore products','Transactions','My schedule','Preferences'],label_visibility='collapsed',key='page_selector')
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
 st.title('PayAhead'); st.error('Could not load your workspace. Check the app logs and database configuration, then refresh.'); st.stop()
profile=dashboard['profile']; metrics=dashboard['metrics']; currency=metrics.get('currency','USD')
def fmt(n): return f"{currency} {n:,.0f}"
st.markdown(f"<div style='color:{colors['accent']};font-size:.72rem;font-weight:700;letter-spacing:.13em;margin-bottom:.25rem'>PAYAHEAD / {page.upper()}</div>",unsafe_allow_html=True)
st.title({'Overview':'Your money, in focus.','Purchase advisor':'Make a confident choice.','Explore products':'A better buy starts here.','Transactions':'Every dollar, accounted for.','My schedule':'Your plan, at your pace.','Preferences':'Make it personal.'}[page])
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
   currency_choice=st.selectbox('Currency',['USD','EUR','GBP','CAD','AUD','JPY','INR'],index=['USD','EUR','GBP','CAD','AUD','JPY','INR'].index(profile.get('currency','USD')) if profile.get('currency','USD') in ['USD','EUR','GBP','CAD','AUD','JPY','INR'] else 0)
   if st.form_submit_button('Save profile',use_container_width=True):
    status,saved=api_put('/finances/profile',{'income':income,'fixed':fixed,'variable':variable,'savings':savings,'debt':debt,'currency':currency_choice})
    if status==200: st.success('Profile saved.'); st.rerun()
    else: st.error(saved.get('error','Sign in to save a profile.'))
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
     if st.button('Price history',key='h_'+p['name'],use_container_width=True): st.session_state['price_lookup']=p['name']
 with st.expander('Preview a product page'):
  page_url=st.text_input('Public product page URL',key='product_preview_url')
  if st.button('Read product details',key='preview_product'):
   status,preview=api_post('/products/extract',{'url':page_url})
   if status==200:
    st.session_state['product_preview']=preview; st.info(preview.get('source','Metadata preview; confirm every value.'))
   else: st.error(preview.get('error','Could not preview URL.'))
  preview=st.session_state.get('product_preview')
  if preview:
   st.write({'Name':preview['name'],'Suggested price':preview['price'],'Currency':preview['currency'],'Source':preview['source']})
   st.caption('Page metadata may be inaccurate. Confirm the product details and enter the price you verified before saving.')
   reviewed_price=st.number_input('Confirmed price',min_value=0.0,value=float(preview['price'] or 0),step=10.0,key='preview_confirmed_price')
   if st.button('Save reviewed product',key='save_preview'):
    if reviewed_price<=0: st.error('Enter a confirmed positive price before saving.')
    else:
     status,saved=api_post('/products',{'name':preview['name'],'category':'Other','price':reviewed_price,'currency':preview['currency'],'url':preview['url'],'description':'Page metadata reviewed by user; not independently verified.'})
     st.success('Saved. Verify the price before checkout.') if status==201 else st.error(saved.get('error','Could not save product.'))
 with st.expander('Add a product manually'):
  with st.form('add_product'):
   new_name=st.text_input('Product name'); new_category=st.text_input('Category','Other'); new_price=st.number_input('Listed price',min_value=0.0,step=10.0); new_currency=st.selectbox('Currency',['USD','EUR','GBP','CAD','AUD','JPY','INR']); new_url=st.text_input('Product page URL (saved for reference)'); new_description=st.text_area('Notes')
   if st.form_submit_button('Save product'):
    status,created=api_post('/products',{'name':new_name,'category':new_category,'price':new_price,'currency':new_currency,'url':new_url,'description':new_description})
    st.success('Product saved. Its price is user-entered and not verified.') if status==201 else st.error(created.get('error','Could not save product.'))
 if st.session_state.get('price_lookup'):
  history=api_get('/price-history',params={'product':st.session_state['price_lookup']})
  if history and history.get('history'):
   st.subheader(f"Price history · {history['product']}"); st.caption(history['note']); frame=pd.DataFrame(history['history']); frame['date']=pd.to_datetime(frame['date']); st.line_chart(frame.set_index('date')['price'])
   if history.get('forecast'): st.metric('Illustrative 30 day estimate',f"{history['forecast']['currency'] if 'currency' in history['forecast'] else ''}{history['forecast']['estimatedPrice']:,.2f}",help=f"Holdout MAE {history['forecast']['holdoutMAE']:.2f}; synthetic series only.")
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
   if st.session_state.token:
    activity=api_get('/agents/activity')
    if activity and activity.get('activity'):
     with st.expander('Saved decision activity'): st.dataframe(pd.DataFrame(activity['activity']),use_container_width=True,hide_index=True)
   st.caption('Demo price trends use generated series. They are not retailer quotes. A payment always needs your approval.')
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
elif page=='Preferences':
 st.subheader('Your saved preferences')
 if not st.session_state.token: st.info('Sign in to manage saved preferences.')
 else:
  prefs=api_get('/preferences') or {'preferences':{}}; existing=prefs.get('preferences',{})
  with st.form('preferences'):
   category=st.text_input('Preferred category',existing.get('category',''))
   budget=st.text_input('Purchase budget',existing.get('budget',''))
   preferred_currency=st.text_input('Preferred currency',existing.get('currency','USD'))
   brand=st.text_input('Brand preferences',existing.get('brand',''))
   if st.form_submit_button('Save preferences',type='primary'):
    status,saved=api_put('/preferences',{'category':category,'budget':budget,'currency':preferred_currency,'brand':brand})
    st.success('Preferences saved.') if status==200 else st.error(saved.get('error','Could not save preferences.'))
  if st.button('Delete saved preferences'):
   status,deleted=api_delete('/preferences'); st.success('Preferences deleted.') if status==200 else st.error(deleted.get('error','Could not delete preferences.'))
else:
 st.subheader('Purchase watches')
 if st.session_state.token and st.button('Check my watches now'):
  status,evaluated=api_post('/schedule/evaluate',{})
  st.success(f"Checked {evaluated.get('checked',0)} watches; {len(evaluated.get('created',[]))} new alerts.") if status==200 else st.error(evaluated.get('error','Watch check failed.'))
 if not st.session_state.token: st.info('Sign in to save a price or date watch.')
 else:
  with st.form('schedule_watch'):
   product_name=st.text_input('Product name'); target=st.number_input('Target price',min_value=0.0,step=10.0); due=st.date_input('Review by')
   if st.form_submit_button('Save watch',type='primary'):
    status,result=api_post('/schedule',{'product':product_name,'target':target,'due':due.isoformat()})
    st.success('Watch saved.') if status==201 else st.error(result.get('error','Could not save watch.'))
  result=api_get('/schedule')
  if result and result.get('schedules'): st.dataframe(pd.DataFrame(result['schedules']),use_container_width=True,hide_index=True)
  alert_data=api_get('/alerts')
  if alert_data and alert_data.get('alerts'):
   st.subheader('Alerts'); [st.warning(a['message']) for a in alert_data['alerts']]
 st.subheader('Cash-flow outlook')
 forecast=api_get('/forecast')
 if forecast: st.info(f"Method: {forecast['method']}. Monthly net estimate: {fmt(forecast['monthlyNet'])}. {forecast['note']}")
st.divider(); st.caption('PayAhead provides educational estimates, not financial advice. The dashboard cash-flow chart is not a bank forecast.')

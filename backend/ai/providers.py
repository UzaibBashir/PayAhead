import os,requests
class Mock:
 def explain(self,f):return f"Monthly surplus is {f['currency']} {f['surplus']:,.0f}. The purchase is {f['share']:.0f}% of monthly income. {f['recommendation']} Review obligations before deciding."
class Compatible:
 def __init__(self,url,key,model):self.url=url.rstrip('/');self.key=key;self.model=model
 def explain(self,f):
  prompt='Explain supplied purchase facts briefly. Do not add figures or facts, and never approve payment. '+str(f)
  r=requests.post(self.url+'/chat/completions',headers={'Authorization':'Bearer '+self.key},json={'model':self.model,'temperature':0,'messages':[{'role':'user','content':prompt}]},timeout=12);r.raise_for_status();return r.json()['choices'][0]['message']['content']
class Gemini:
 def __init__(self,key,model):self.key=key;self.model=model
 def explain(self,f):
  url=f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent';r=requests.post(url,params={'key':self.key},json={'contents':[{'parts':[{'text':'Explain these facts without adding numbers or approving payment: '+str(f)}]}]},timeout=12);r.raise_for_status();return r.json()['candidates'][0]['content']['parts'][0]['text']
def get_provider():
 name=os.getenv('AI_PROVIDER','mock').lower()
 if name=='mock':return Mock()
 if name=='gemini' and os.getenv('GEMINI_API_KEY'):return Gemini(os.environ['GEMINI_API_KEY'],os.getenv('AI_MODEL','gemini-2.0-flash'))
 keys={'openai':'OPENAI_API_KEY','groq':'GROQ_API_KEY','compatible':'AI_API_KEY'}
 if name in keys and os.getenv(keys[name]) and os.getenv('AI_MODEL'):
  default={'openai':'https://api.openai.com/v1','groq':'https://api.groq.com/openai/v1'}.get(name,os.getenv('AI_BASE_URL',''))
  url=os.getenv('AI_BASE_URL',default)
  if url:return Compatible(url,os.environ[keys[name]],os.environ['AI_MODEL'])
 return Mock()

"""Bounded product page metadata reader with DNS pinning and redirects disabled."""
import http.client,ipaddress,json,socket,ssl
from html.parser import HTMLParser
from urllib.parse import urlparse
MAX_BYTES=1_000_000
class Metadata(HTMLParser):
 def __init__(self):super().__init__();self.meta={};self.title=[];self.in_title=False;self.jsonld=[];self.in_json=False;self.json_data=''
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta':
   key=(a.get('property') or a.get('name') or '').lower();value=a.get('content','')
   if key and value:self.meta[key]=value
  if tag=='title':self.in_title=True
  if tag=='script' and a.get('type','').lower()=='application/ld+json':self.in_json=True;self.json_data=''
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag=='script' and self.in_json:self.jsonld.append(self.json_data);self.in_json=False
 def handle_data(self,data):
  if self.in_title:self.title.append(data)
  if self.in_json:self.json_data+=data
class PinnedHTTP(http.client.HTTPConnection):
 def __init__(self,host,port,ip,timeout):super().__init__(host,port,timeout=timeout);self.ip=ip
 def connect(self):self.sock=socket.create_connection((self.ip,self.port),self.timeout)
class PinnedHTTPS(http.client.HTTPSConnection):
 def __init__(self,host,port,ip,timeout):super().__init__(host,port,timeout=timeout,context=ssl.create_default_context());self.ip=ip
 def connect(self):
  raw=socket.create_connection((self.ip,self.port),self.timeout);self.sock=self._context.wrap_socket(raw,server_hostname=self.host)
def extract(url):
 parsed=urlparse(url)
 if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Enter a public http or https product URL.')
 port=parsed.port or (443 if parsed.scheme=='https' else 80)
 if port not in (80,443):raise ValueError('Only standard web ports are accepted.')
 ips=sorted({x[4][0] for x in socket.getaddrinfo(parsed.hostname,port,type=socket.SOCK_STREAM)})
 if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):raise ValueError('Local/private product hosts are blocked.')
 ip=ips[0];conn=(PinnedHTTPS if parsed.scheme=='https' else PinnedHTTP)(parsed.hostname,port,ip,timeout=5);path=parsed.path or '/'
 if parsed.query:path+='?'+parsed.query
 try:
  conn.request('GET',path,headers={'Host':parsed.hostname,'User-Agent':'PayAhead-Preview/1.0','Accept':'text/html','Connection':'close'});response=conn.getresponse()
  if response.status not in (200,):raise ValueError(f'Product page returned HTTP {response.status}; redirects are not followed.')
  if 'text/html' not in response.getheader('Content-Type','').lower():raise ValueError('Product page did not return HTML.')
  raw=response.read(MAX_BYTES+1)
  if len(raw)>MAX_BYTES:raise ValueError('Product page exceeds the 1 MB preview limit.')
 finally:conn.close()
 parser=Metadata();parser.feed(raw.decode('utf-8','replace'));title=parser.meta.get('og:title') or parser.meta.get('twitter:title') or ' '.join(' '.join(parser.title).split())
 price=parser.meta.get('product:price:amount') or parser.meta.get('og:price:amount');currency=parser.meta.get('product:price:currency') or parser.meta.get('og:price:currency') or 'USD'
 for blob in parser.jsonld:
  try:
   obj=json.loads(blob);items=obj if isinstance(obj,list) else [obj]
   for item in items:
    if isinstance(item,dict) and item.get('@type') in ('Product',['Product']):
     title=title or item.get('name','');offers=item.get('offers',{});offers=offers[0] if isinstance(offers,list) else offers;price=price or offers.get('price');currency=offers.get('priceCurrency',currency)
  except (ValueError,AttributeError,TypeError):pass
 try:parsed_price=float(price) if price else None
 except (ValueError,TypeError):parsed_price=None
 return {'name':title[:160],'price':parsed_price,'currency':currency[:3].upper(),'url':url,'source':'page metadata; retailer unverified','needsReview':True}

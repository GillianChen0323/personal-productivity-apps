"""Read-only Canvas API client and deterministic planning; no AI calls."""
import datetime as dt, hashlib, ipaddress, json, re, socket, time
import urllib.request as req
from urllib.parse import urlparse, urljoin
from urllib.error import HTTPError
from zoneinfo import ZoneInfo
BASE='https://courseworks2.columbia.edu'
TZ=ZoneInfo('America/New_York')
class SafeRedirect(req.HTTPRedirectHandler):
 def redirect_request(self,r,fp,code,msg,hdr,newurl):
  validate_download(newurl)
  out=super().redirect_request(r,fp,code,msg,hdr,newurl)
  if out:
   out.remove_header('Authorization')
  return out

def validate_download(url):
 p=urlparse(url)
 if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443): raise ValueError('文件链接不是有效 HTTPS 地址')
 for x in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM):
  if not ipaddress.ip_address(x[4][0]).is_global: raise ValueError('文件链接指向非公网地址')

def api_url(path):
 u=urljoin(BASE,path)
 if urlparse(u).netloc!=urlparse(BASE).netloc or not u.startswith(BASE+'/api/v1/'):raise ValueError('拒绝向非 Canvas API 发送凭据')
 return u

class Canvas:
 def __init__(self,token):self.token=token
 def get(self,path):
  u=api_url(path)
  for attempt in range(3):
   try:
    r=req.build_opener(SafeRedirect()).open(req.Request(u,headers={'Authorization':'Bearer '+self.token,'Accept':'application/json'}),timeout=40)
    with r:return json.load(r),r.headers.get('Link','')
   except HTTPError as e:
    if e.code==429 and attempt<2:time.sleep(2*(attempt+1));continue
    if e.code in (401,403):raise ValueError(f'Canvas 拒绝访问（{e.code}）：请检查令牌或课程权限') from None
    raise ValueError(f'Canvas 请求失败（HTTP {e.code}）') from None
  raise ValueError('Canvas 暂时限流，请稍后重试')
 def pages(self,path):
  path+=('&' if '?' in path else '?')+'per_page=100'
  result=[];seen=set()
  while path:
   u=api_url(path)
   if u in seen:raise ValueError('Canvas 分页循环异常')
   seen.add(u)
   if len(seen)>1000:raise ValueError('分页超过上限，本次结果未保存')
   rows,link=self.get(u)
   if not isinstance(rows,list):raise ValueError('Canvas 返回格式不正确')
   result.extend(rows)
   match=re.search(r'<([^>]+)>;\s*rel="next"',link)
   path=match.group(1) if match else None
  return result
 def download(self,url):
  validate_download(url)
  headers={}
  if urlparse(url).netloc==urlparse(BASE).netloc:headers['Authorization']='Bearer '+self.token
  with req.build_opener(SafeRedirect()).open(req.Request(url,headers=headers),timeout=90) as r:
   if 'text/html' in r.headers.get('Content-Type',''):raise ValueError('下载返回登录网页，请重新连接 Canvas')
   b=r.read(50*1024*1024+1)
   if len(b)>50*1024*1024:raise ValueError('文件超过 50 MB，请手动处理')
   return b


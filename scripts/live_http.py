"""Explicit HTTP pages only. Validated/pinned IP, TLS verification and scoped redirects."""
import http.client
from http.cookies import SimpleCookie, CookieError
import ipaddress
import socket
import ssl
from urllib.parse import urlsplit,urljoin
from audit import finding
from page_parser import PageParser

MAX_BODY=2*1024*1024


def validate_url(url,allow_loopback=False):
    p=urlsplit(url)
    if p.scheme not in {'http','https'} or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError('Use an HTTP(S) URL without credentials, query or fragment')
    if any(ord(c)<33 for c in url):raise ValueError('Invalid URL characters')
    port=p.port or (443 if p.scheme=='https' else 80)
    addresses={r[4][0] for r in socket.getaddrinfo(p.hostname,port,type=socket.SOCK_STREAM)}
    if not addresses:raise ValueError('No resolved addresses')
    for value in addresses:
        address=ipaddress.ip_address(value)
        if not address.is_global and not (allow_loopback and address.is_loopback):
            raise ValueError('Non-public destination rejected')
    return p,sorted(addresses)[0],port


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,port,ip,timeout):
        super().__init__(host,port,timeout=timeout,context=ssl.create_default_context());self.ip=ip
    def connect(self):
        sock=socket.create_connection((self.ip,self.port),self.timeout)
        self.sock=self._context.wrap_socket(sock,server_hostname=self.host)


def fetch(url,allow_loopback=False,timeout=8):
    original=urlsplit(url);origin=(original.scheme,original.hostname,original.port or (443 if original.scheme=='https' else 80))
    for _ in range(4):
        p,ip,port=validate_url(url,allow_loopback)
        if (p.scheme,p.hostname,port)!=origin:raise ValueError('Cross-origin redirect rejected')
        conn=PinnedHTTPS(p.hostname,port,ip,timeout) if p.scheme=='https' else http.client.HTTPConnection(ip,port,timeout=timeout)
        try:
            conn.request('GET',p.path or '/',headers={'Host':p.netloc,'User-Agent':'production-engineering/1.1','Accept-Encoding':'identity','Connection':'close'})
            res=conn.getresponse();headers=res.headers;status=res.status
            if status in {301,302,303,307,308}:
                if not headers.get('Location'):raise ValueError('Redirect missing Location')
                next_url=urljoin(url,headers['Location'])
                np=urlsplit(next_url)
                if (np.scheme,np.hostname,np.port or (443 if np.scheme=='https' else 80))!=origin:raise ValueError('Cross-origin redirect rejected')
                url=next_url;continue
            if headers.get('Content-Encoding','identity').lower()!='identity':raise ValueError('Encoded response not assessed')
            body=res.read(MAX_BODY+1)
            if len(body)>MAX_BODY:raise ValueError('HTTP response limit exceeded')
            return status,headers,body,url
        finally:conn.close()
    raise ValueError('Redirect limit exceeded')


def scan_http(url,allow_loopback=False):
    findings=[];check={'id':'http','status':'error'}
    try:
        status,headers,body,final=fetch(url,allow_loopback)
        def add(rule,severity,title,fix):
            f=finding('http.'+rule,'',0,severity,title,fix,source='http',confidence='observed')
            # Never include response/cookie/body values or query data.
            f['evidence']={'kind':'http','url':final,'status':status}
            findings.append(f)
        if not 200<=status<400:add('status','high','HTTP status is unsuccessful','Inspect deployment and route availability.')
        for name,severity in [('content-security-policy','medium'),('x-content-type-options','low'),('referrer-policy','low')]:
            if not headers.get(name):add('header.'+name,severity,'Missing '+name,'Configure and test the effective response policy.')
        if final.startswith('https:') and not headers.get('strict-transport-security'):add('header.hsts','medium','Missing HSTS','Assess an appropriate HSTS policy.')
        if headers.get('x-content-type-options','').lower() not in {'','nosniff'}:add('header.nosniff','medium','Invalid nosniff policy','Set X-Content-Type-Options: nosniff.')
        csp=headers.get('content-security-policy','')
        if 'unsafe-eval' in csp:add('header.csp_eval','medium','CSP permits unsafe-eval','Review necessity and remove unsafe script execution.')
        # Wildcard credentials is browser-rejected, not proof of data exposure.
        if headers.get('access-control-allow-origin')=='*' and headers.get('access-control-allow-credentials','').lower()=='true':
            add('cors.configuration','medium','Incompatible wildcard and credentialed CORS configuration','Test allowed and denied origins with actual authenticated requests.')
        cookie_count=0
        for raw in headers.get_all('Set-Cookie',[]):
            cookie=SimpleCookie();cookie.load(raw)
            if not cookie:raise ValueError('Cookie could not be parsed')
            for name,morsel in cookie.items():
                cookie_count+=1
                sensitive=any(x in name.lower() for x in ['session','auth','token','sid'])
                if sensitive and not morsel['httponly']:add('cookie.httponly','high','Session-like cookie lacks HttpOnly','Verify cookie purpose and enforce HttpOnly when appropriate.')
                if final.startswith('https:') and not morsel['secure']:add('cookie.secure','medium','Cookie lacks Secure','Use Secure for cookies sent over HTTPS.')
                if morsel['samesite'].lower()=='none' and not morsel['secure']:add('cookie.samesite','medium','SameSite=None lacks Secure','Modern browsers reject this cookie configuration.')
        if 'text/html' in headers.get_content_type():
            parser=PageParser();parser.feed(body.decode(headers.get_content_charset() or 'utf-8'));parser.close()
            for attr,rule in [('title','title'),('lang','lang'),('viewport','viewport')]:
                if not getattr(parser,attr):add('page.'+rule,'low','Missing HTML '+rule,'Inspect the actual page and provide appropriate metadata.')
            if parser.images_missing_alt:add('page.alt','medium','HTML images lack alt attributes','Provide meaningful alternatives or explicit decorative alt.')
            if parser.password_forms and final.startswith('http:'):add('password_http','high','Password form served over HTTP','Serve credential forms only over HTTPS.')
        check.update(status='completed',http_status=status,cookies_seen=cookie_count,url=final,
                     note='Response HTML only; JavaScript and browser behavior require separate evidence.')
    except (OSError,ValueError,UnicodeError,LookupError,CookieError,http.client.HTTPException):
        check['reason']='HTTP check unavailable, out of scope, malformed, or exceeded limits.'
    return findings,check


if __name__=='__main__':
    import argparse,json
    ap=argparse.ArgumentParser()
    ap.add_argument('url');ap.add_argument('--allow-loopback',action='store_true')
    args=ap.parse_args()
    f,c=scan_http(args.url,args.allow_loopback)
    print(json.dumps({'findings':f,'check':c}))

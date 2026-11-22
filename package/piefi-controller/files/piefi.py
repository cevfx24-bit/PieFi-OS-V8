#!/usr/bin/env python3
import json, sqlite3, secrets, os, subprocess, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler,HTTPServer
from datetime import datetime,timezone
DB='/etc/piefi/piefi.sqlite3'
def uci(k,d):
 try: return subprocess.check_output(['uci','-q','get','piefi.main.'+k],text=True).strip() or d
 except: return d
DB=uci('database',DB); HOST=uci('bind','127.0.0.1'); PORT=int(uci('port','8787'))
AUTH=uci('auth_command','/usr/bin/ndsctl auth'); DEAUTH=uci('deauth_command','/usr/bin/ndsctl deauth')
TOKEN_FILE=uci('token_file','/etc/piefi/api.token'); CHECK=int(uci('session_check_seconds','15'))
os.makedirs(os.path.dirname(DB),exist_ok=True); os.makedirs(os.path.dirname(TOKEN_FILE),exist_ok=True)
if not os.path.exists(TOKEN_FILE):
 with open(TOKEN_FILE,'w') as f: f.write(secrets.token_urlsafe(32))
 os.chmod(TOKEN_FILE,0o600)
TOKEN=open(TOKEN_FILE).read().strip()
def db():
 c=sqlite3.connect(DB,timeout=10); c.execute('PRAGMA journal_mode=WAL')
 c.execute("""CREATE TABLE IF NOT EXISTS vouchers(code TEXT PRIMARY KEY,minutes INTEGER NOT NULL,created TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'unused',redeemed TEXT,mac TEXT,expires REAL)""")
 c.execute("""CREATE TABLE IF NOT EXISTS sessions(mac TEXT PRIMARY KEY,code TEXT,expires REAL,active INTEGER DEFAULT 1)""")
 c.execute("""CREATE TABLE IF NOT EXISTS coins(id INTEGER PRIMARY KEY,amount INTEGER,event TEXT,created TEXT)""")
 c.execute("""CREATE TABLE IF NOT EXISTS credits(id INTEGER PRIMARY KEY,amount INTEGER,created TEXT,used INTEGER DEFAULT 0)""")
 c.commit(); return c
def cmd(command, mac):
 args=command.split()+[mac]
 return subprocess.run(args,timeout=8,check=True,capture_output=True,text=True)
def deauth_expired():
 while True:
  try:
   c=db(); now=time.time(); rows=c.execute('SELECT mac,code,expires FROM sessions WHERE active=1 AND expires<=?',(now,)).fetchall()
   for mac,code,exp in rows:
    try: cmd(DEAUTH,mac)
    except Exception as e: print('deauth command failed for',mac,repr(e))
    c.execute('UPDATE sessions SET active=0 WHERE mac=?',(mac,))
    c.execute("UPDATE vouchers SET status='expired' WHERE code=?",(code,))
   c.commit(); c.close()
  except Exception as e: print('session monitor error',repr(e))
  time.sleep(max(5,CHECK))
class H(BaseHTTPRequestHandler):
 def sendj(self,s,o):
  b=json.dumps(o).encode(); self.send_response(s); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
 def body(self):
  n=int(self.headers.get('Content-Length','0')); return json.loads(self.rfile.read(n) or b'{}')
 def authorized(self):
  return self.headers.get('Authorization','')=='Bearer '+TOKEN
 def do_GET(self):
  p=urllib.parse.urlparse(self.path).path
  if p=='/health': return self.sendj(200,{'status':'ok','version':'0.2.0'})
  if p=='/': 
   try: self.send_response(302); self.send_header('Location','/dashboard'); self.end_headers()
   except: pass
   return
  if p=='/dashboard':
   try:
    b=open('/www/piefi/index.html','rb').read(); self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
   except: self.sendj(404,{'error':'dashboard unavailable'})
   return
  if not self.authorized(): return self.sendj(401,{'error':'bearer token required'})
  c=db()
  if p=='/api/v1/vouchers':
   rows=c.execute('SELECT code,minutes,created,status,redeemed,mac,expires FROM vouchers ORDER BY created DESC LIMIT 300').fetchall()
   c.close(); return self.sendj(200,{'vouchers':[dict(zip(['code','minutes','created','status','redeemed','mac','expires'],r)) for r in rows]})
  if p=='/api/v1/sessions':
   rows=c.execute('SELECT mac,code,expires,active FROM sessions').fetchall(); c.close(); return self.sendj(200,{'sessions':rows})
  if p=='/api/v1/credits':
   rows=c.execute('SELECT amount,created,used FROM credits ORDER BY id DESC LIMIT 100').fetchall(); c.close(); return self.sendj(200,{'credits':rows})
  c.close(); return self.sendj(404,{'error':'not found'})
 def do_POST(self):
  if not self.authorized(): return self.sendj(401,{'error':'bearer token required'})
  try: data=self.body()
  except: return self.sendj(400,{'error':'invalid JSON'})
  p=urllib.parse.urlparse(self.path).path
  if p=='/api/v1/vouchers':
   try: mins=int(data.get('minutes',0)); count=min(max(int(data.get('count',1)),1),100)
   except: return self.sendj(400,{'error':'numeric minutes/count required'})
   if not 1<=mins<=1440: return self.sendj(400,{'error':'minutes range 1..1440'})
   c=db(); codes=[]
   for _ in range(count):
    code=secrets.token_hex(4).upper(); c.execute('INSERT INTO vouchers(code,minutes,created) VALUES(?,?,?)',(code,mins,datetime.now(timezone.utc).isoformat())); codes.append(code)
   c.commit(); c.close(); return self.sendj(201,{'codes':codes,'minutes':mins})
  if p=='/api/v1/redeem':
   code=str(data.get('code','')).strip().upper(); mac=str(data.get('mac','')).strip().lower()
   if not code or not mac or len(mac)>64:return self.sendj(400,{'error':'voucher code and MAC required'})
   c=db(); row=c.execute('SELECT minutes,status FROM vouchers WHERE code=?',(code,)).fetchone()
   if not row: c.close(); return self.sendj(404,{'error':'voucher not found'})
   if row[1]!='unused': c.close(); return self.sendj(409,{'error':'voucher not unused'})
   mins=row[0]
   try: cmd(AUTH,mac)
   except Exception as e: c.close(); return self.sendj(502,{'error':'gateway authorization failed','detail':str(e)})
   expires=time.time()+mins*60
   c.execute("UPDATE vouchers SET status='redeemed',redeemed=?,mac=?,expires=? WHERE code=?",(datetime.now(timezone.utc).isoformat(),mac,expires,code))
   c.execute('INSERT OR REPLACE INTO sessions(mac,code,expires,active) VALUES(?,?,?,1)',(mac,code,expires))
   c.commit(); c.close(); return self.sendj(200,{'redeemed':True,'minutes':mins,'expires_epoch':expires})
  if p=='/api/v1/coin-event':
   try: amount=int(data.get('amount',0))
   except: amount=0
   if not 1<=amount<=10000:return self.sendj(400,{'error':'amount range 1..10000'})
   c=db(); now=datetime.now(timezone.utc).isoformat()
   c.execute('INSERT INTO coins(amount,event,created) VALUES(?,?,?)',(amount,str(data.get('event','serial')),now))
   c.execute('INSERT INTO credits(amount,created) VALUES(?,?)',(amount,now)); c.commit(); c.close()
   return self.sendj(201,{'recorded':True})
  c=None; return self.sendj(404,{'error':'not found'})
 def log_message(self,*args): pass
if __name__=='__main__':
 db().close(); threading.Thread(target=deauth_expired,daemon=True).start(); HTTPServer((HOST,PORT),H).serve_forever()

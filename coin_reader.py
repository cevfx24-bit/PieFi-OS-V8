#!/usr/bin/env python3
import os,sys,termios,time,urllib.request,json
dev=sys.argv[1] if len(sys.argv)>1 else '/dev/ttyUSB0'
fd=os.open(dev,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
a=termios.tcgetattr(fd); a[4]=termios.B115200; a[5]=termios.B115200; a[2]|=termios.CS8; termios.tcsetattr(fd,termios.TCSANOW,a)
buf=b''
while True:
 try:
  buf+=os.read(fd,256)
  while b'\\n' in buf:
   line,buf=buf.split(b'\\n',1); line=line.decode(errors='ignore').strip()
   if line.startswith('COIN:'):
    try:
     val=int(line.split(':',1)[1]); req=urllib.request.Request('http://127.0.0.1:8787/api/v1/coin-event',data=json.dumps({'amount':val,'event':'esp32'}).encode(),headers={'Content-Type':'application/json'})
     # Auth token is required; fetch token from local file and attach.
     token=open('/etc/piefi/api.token').read().strip(); req.add_header('Authorization','Bearer '+token); urllib.request.urlopen(req,timeout=3).read()
    except Exception as e: print('event submit failed:',e,file=sys.stderr)
 except BlockingIOError: time.sleep(.15)

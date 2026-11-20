import http.server,socketserver,os,sys,functools
os.chdir(sys.argv[1]);port=int(sys.argv[2])
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
socketserver.TCPServer.allow_reuse_address=True
with socketserver.TCPServer(('127.0.0.1',port),H) as s: s.serve_forever()

## Copyright 2012 Joey
## 
## winamp-whip is released under GPL. Please read the license before continuing.
## 
## The latest source can be found here:
##	 https://github.com/jvq2/httpyd
##
import socketserver
import threading
from ctypes import windll, wintypes
import traceback

SendMessageW = windll.user32.SendMessageW
FindWindowW = windll.user32.FindWindowW
WinampHwnd = FindWindowW("Winamp v1.x", 0)

cmdcodes = {
	'prev':    40044,
	'next':    40048,
	'play':    40045,
	'pause':   40046,
	'stop':    40047,
	'fadeout': 40157,
	'forward': 40148,
	'rewind':  40144,
	'volup':   40058,
	'voldown': 40059
	}



def getWinamp(wclass="Winamp v1.x"):
	return windll.user32.FindWindowW("Winamp v1.x", 0)
"""
def play(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['play'], 0)
	
def pause(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['pause'], 0)
	
def next(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['next'], 0)
	
def prev(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['prev'], 0)
	
def stop(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['stop'], 0)
	
def fadeout(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['fadeout'], 0)
	
def forward(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['forward'], 0)
	
def rewind(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['rewind'], 0)
	
def volup(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['volup'], 0)
	
def voldown(hwnd=None):
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['voldown'], 0)"""
	
	
class RemoteServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	require_passwd = True
	passwd = 'whipit'
	pass

"""
0 Unknown Command
1 Success
2 Invalid Password
3 Requires Password
"""
	
	
class RemoteServer_handler(socketserver.StreamRequestHandler):
	authd = False
	
	
	
	#def setup(self):
	#	self.winampWnd = getWinamp()
	#	return socketserver.StreamRequestHandler.setup(self)
		
	def handle(self):
		
		# authorize all connections if a password is not required
		if not self.server.require_passwd:
			self.authd = True
		
		
		while True:
			
			try:
				self.data = self.rfile.readline()
			except:
				print("{0} closed the connection".format(self.client_address[0]))
				break
			
			# close if nothing is returned from the stream
			if not self.data:
				break # connection closed
			
			try:
				self.magic()
				pass
			except:
				# NEVER FAIL!!
				traceback.print_exc()
			
	
	
	def magic(self):
		self.data = self.data.strip()
		
		self.cmd, *self.params = self.data.decode('utf8').split()
		
		return self.dispatch(self.cmd, self.params)
	
	
	
	def dispatch(self, cmd, params=[]):
		if not cmd: return
		
		print(cmd, params)
		if cmd in ['play', 'pause', 'next', 'prev', 'stop', 'fadeout', 'forward', 'rewind', 'volup', 'voldown']:
			return self.playback(cmd)
		
		elif cmd == 'playstatus':
			return self.playstatus()
		
		elif cmd == 'commands':
			self.wfile.write(b'"play" | "pause" | "next" | "prev" | "stop" | "fadeout" | "forward" | "rewind" | "volup" | "voldown" | "passwd" | "commands" | "quit"')
			return
			
		elif cmd == 'quit':
			self.close()
			return
			
		elif cmd == 'passwd':
			if params and params[0] == self.server.passwd:
				self.authd = True
				self.wfile.write(b'"1 Success"')
			else:
				self.wfile.write(b'"2 Invalid Password"')
			return
		else:
			self.wfile.write(b'"0 Unknown Command"')
		return
	
	def send(self, text):
		return self.wfile.write(bytes(str(text),'utf8'))
	
	def unathd(self):
		return self.wfile.write(b'"3 Requires Password"')
		
		
		
	def windowMessage(self, wm, wparam=0, lparam=0):
		return SendMessageW(getWinamp(), wm, wparam, lparam)
		
	
	def playback(self, cmd):
		global cmdcodes
		if not self.authd: return self.unathd()
		self.windowMessage(0x0111, cmdcodes[cmd])
		self.wfile.write(b'1 Success')
		
	
	def playstatus(self):
		if not self.authd: return self.unathd()
		stats = self.windowMessage(0x400, 0, 104)
		
		if stats == 1:
			return self.send('PLAYSTATUS playing')
		elif stats == 3:
			return self.send('PLAYSTATUS paused')
		return self.send('PLAYSTATUS stopped')
	
	
	
	#def finish(self):
	#	## Note:
	#	##   If setup() or handle() raise an exception, this function
	#	##   will not be called.
	#	pass
	
	

if __name__ == "__main__":
	HOST, PORT = "localhost", 6969

	server = RemoteServer((HOST, PORT), RemoteServer_handler)

	server.serve_forever()
	input()


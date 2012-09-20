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

def play(hwnd=None):# 40045
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['play'], 0)
	
def pause(hwnd=None):# 40046
	global cmdcodes
	if not hwnd: hwnd = getWinamp()
	#if not hwnd: return -1
	return SendMessageW(hwnd, 0x0111, cmdcodes['pause'], 0)
	
	
class RemoteServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

	
	
class RemoteServer_handler(socketserver.StreamRequestHandler):
	self.winampWnd = 0
	self.authd = 0
	
	
	
	def setup(self):
		self.winampWnd = getWinamp()
		
	def handle(self):
		while not self.rfile.closed:
			
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
			except:
				# NEVER FAIL!!
				traceback.print_exc()
			
			self.wfile.write(self.data.upper())
	
	def magic(self):
		self.data = self.data.strip()
		
		print("{0} wrote:".format(self.client_address[0]))
		print(self.data)
		
		self.cmd, *self.params = self.data.split()
		
		return self.dispatch(self.cmd, self.params)
	
	
	def dispatch(self, cmd, params=[]):
		if not cmd: return
		
		if cmd == 'play':
			return play()
		elif cmd == 'pause':
			return pause()
		return
	
	
	def finish(self):
		## Note:
		##   If setup() or handle() raise an exception, this function
		##   will not be called.
		pass
	
	

if __name__ == "__main__":
	HOST, PORT = "localhost", 696969

	# Create the server, binding to localhost on port 9999
	server = RemoteServer((HOST, PORT), RemoteServer_handler)

	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	server.serve_forever()
	input()


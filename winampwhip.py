## Copyright 2012 Joey
## 
## winamp-whip is released under GPL. Please read the license before continuing.
## 
## The latest source can be found here:
##	 https://github.com/jvq2/httpyd
##
## Window messages gathered from here: (and some extra window snooping)
## http://forums.winamp.com/showthread.php?threadid=180297
##

import socketserver
import threading
from ctypes import windll, wintypes
import traceback
import os
import os.path



## A thanks goes to Shalabh Chaturvedi  for the original inspiration
## of this library. Shalabh's library relied on the win32api library
## and I found that this is not always available for use through the
## different  python  versions.  That led to the idea of  creating a
## win32api  independent  version of his winamp class and the remote
## winamp  client-server  pair (which was not in Shalabh's  original
## library).
class Winamp():

	hwnd = None
	dumpPath = os.environ['APPDATA']+'\\Winamp\\Winamp.m3u'
	
	playback_codes = {
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
	
	def __init__(self, hwnd=None):
		if not hwnd:
			self.hwnd = self.getWindow()
		
	def running(self):
		return not not self.window()
		
	def close(self):
		return self.sendMessage(0x0111, 40001)
		
	def open(self):
		#only start winamp if we know where its at
		if not os.path.isfile(os.environ['PROGRAMFILES']+'\\Winamp\\winamp.exe'):
			return False
		# start winamp; this function blocks until winamp is fully started.
		os.startfile(os.environ['PROGRAMFILES']+'\\Winamp\\winamp.exe')
		return True
		
	def window(self):
		return self.hwnd and self.hwnd or self.getWindow()
		
	def getWindow(self, wclass="Winamp v1.x"):
		return windll.user32.FindWindowW("Winamp v1.x", 0)
		
	def sendMessage(self, wm, wparam=0, lparam=0):
		return windll.user32.SendMessageW(self.window(), int(wm), int(wparam), int(lparam))
		
	
	def playback(self, cmd):
		return self.sendMessage(0x0111, self.playback_codes[cmd])
		
	
	def playStatus(self):
		stats = self.sendMessage(0x400, 0, 104)
		
		if stats == 1:
			return 'playing'
		elif stats == 3:
			return 'paused'
		return 'stopped'
	
	def currentTrack(self, track=None):
		if type(track) == type(None):
			return self.sendMessage(0x400, 0, 125)
		
		return self.sendMessage(0x400, track, 121)
		
	def trackName(self):
		## Shalabh's library used GetWindowText here. However, in newer
		## versions of winamp, the window text scrolls and creates a 
		## chopped version of the song title limited to a set width.
		#print(list(filter(lambda x:not x or not x[0]=='#', self.playList().split('\n'))))
		return list(filter(lambda x:not x or not x[0]=='#', self.playList().split('\n')))[self.currentTrack()].strip()
		#return self.playList()[self.currentTrack()]
		
	
	def numTracks(self):
		return self.sendMessage(0x400, 0, 124)
	
	def sampleRate(self):
		return self.sendMessage(0x400, 0, 126)
	def bitRate(self):
		return self.sendMessage(0x400, 1, 126)
	def numChannels(self):
		return self.sendMessage(0x400, 2, 126)
	
	def dumpList(self):
		"dumps the current playlist into WINAMPDIR/winamp.m3u"
		return self.sendMessage(0x400, 0, 120)
	
	def playList(self):
		self.dumpList()
		plf = open(self.dumpPath,'r')
		pl = plf.read()
		plf.close()
		return pl
	
	def seek(self, msecs=0):
		"seeks within the currently playing track. msecs is in milliseconds"
		return self.sendMessage(0x400, msecs, 106)
	
	def setVolume(self, vol):
		"Set the volume. The volume is a number from 0 to 255"
		if vol > 255: vol = 255
		if vol < 0: vol = 0
		return self.sendMessage(0x400, vol, 122)




class RemoteServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	require_passwd = True
	passwd = 'whipit'
	remote_open = False
	remote_close = False
	pass # no methods implemented here

"""
0 Unknown Command
1 Success
2 Invalid Password
3 Requires Password
4 Not Allowed
"""
	
	
class RemoteServer_handler(socketserver.StreamRequestHandler):
	authd = False
	winamp = None
	
	
	def handle(self):
		
		# authorize all connections if a password is not required
		if not self.server.require_passwd:
			self.authd = True
		
		self.winamp = Winamp()
		
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
			if not self.authd: return self.unathd()
			self.winamp.playback(cmd)
			return self.send('1 Success')
		
		elif cmd == 'playstatus':
			if not self.authd: return self.unathd()
			return self.send('PLAYSTATUS '+self.winamp.playStatus())
			#return self.playstatus()
			
		elif cmd == 'trackname':
			if not self.authd: return self.unathd()
			return self.send('TRACKNAME '+self.winamp.trackName())
			#return self.trackname()
			
			
		elif cmd == 'playlist':
			if not self.authd: return self.unathd()
			return self.send('PLAYLIST '+';'.join(self.winamp.playList().split()))
			#return self.trackname()
		
		
		elif cmd == 'commands' or cmd == 'help' or cmd == '?' or cmd == '/?':
			# TODO: add all the commands here
			return self.send('"play" | "pause" | "next" | "prev" | "stop" | "fadeout" | "forward" | "rewind" | "volup" | "voldown" | "passwd" | "commands"')
			
			
		elif cmd == 'close':
			if not self.authd: return self.unathd()
			if not self.server.remote_close:
				return self.send('4 Not Allowed')
			
			self.winamp.close()
			return self.send('1 Success')
			
		elif cmd == 'open':
			if not self.authd: return self.unathd()
			if not self.server.remote_open:
				return self.send('4 Not Allowed')
			
			self.winamp.open()
			return self.send('1 Success')
			
		elif cmd == 'passwd':
			if params and params[0] == self.server.passwd:
				self.authd = True
				return self.send('1 Success')
			# bad password
			return self.send('2 Invalid Password')
			
		
		# if no other commands match
		return self.send('0 Unknown Command')
	
	def send(self, text):
		return self.wfile.write(bytes(str(text),'utf8'))
	
	def unathd(self):
		return self.send('3 Requires Password')
		
		

	
	

if __name__ == "__main__":
	HOST, PORT = "localhost", 6969

	server = RemoteServer((HOST, PORT), RemoteServer_handler)
	server.remote_open = True
	server.remote_close = True

	server.serve_forever()
	input()


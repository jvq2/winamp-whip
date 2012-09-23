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
import socket



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
	version = None
	
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
	'voldown': 40059,
	'stopafter': 40157,
	'playlist-beg': 40154,
	'playlist-end': 40158,
	'repeat':  40022,
	'shuffle': 40023,
	'backten': 40197,
	'playcd':  40323
	}
	
	def __init__(self, hwnd=None):
		if not hwnd:
			self.hwnd = self.getWindow()
		
		self.version = self.getVersion()
		
		
	def getVersion(self):
		"""Return the which version of winamp is running."""
		## sendMessage(0x400,0,0) returns a hex value of the version. Ex: 0x5033
		## In the example, 5 is the major version and 33 is the minor.
		return hex(self.sendMessage(0x400))[2:].replace('0', '.', 1)
		
	def running(self):
		"""Returns a boolean value of whether or not winamp is running."""
		return not not self.getWindow()
		
	def close(self):
		"""Close winamp"""
		return self.sendMessage(0x0111, 40001)
		
	def open(self):
		"""Open an instance of winamp"""
		#only start winamp if we know where its at
		if not os.path.isfile(os.environ['PROGRAMFILES']+'\\Winamp\\winamp.exe'):
			return False
		# start winamp; this function blocks until winamp is fully started.
		os.startfile(os.environ['PROGRAMFILES']+'\\Winamp\\winamp.exe')
		return True
		
	def window(self):
		"""Returns self.hwnd or calls getWindow() if self.hwnd is None."""
		return self.hwnd and self.hwnd or self.getWindow()
		
	def getWindow(self, wclass="Winamp v1.x"):
		"""Used internally. Retrieve a window handle to winamp"""
		return windll.user32.FindWindowW("Winamp v1.x", 0)
		
	def sendMessage(self, wm, wparam=0, lparam=0):
		"""Send a window message to winamp. This method is used internally by methods like playback() and playstatus()"""
		return windll.user32.SendMessageW(self.window(), int(wm), int(wparam), int(lparam))
		
	
	def playback(self, cmd):
		"""Sends general playback commands to winamp. The input should be a key name in playback_codes. See playback_codes for a list of keywords."""
		return self.sendMessage(0x0111, self.playback_codes[cmd])
		
	
	def playStatus(self):
		"""Returns the status of winamp. Return values are the strings "playing", "paused", or "stopped"."""
		stats = self.sendMessage(0x400, 0, 104)
		
		if stats == 1:
			return 'playing'
		elif stats == 3:
			return 'paused'
		return 'stopped'
	
	def currentTrack(self, track=None):
		"""If track is not None sets the current playing track in the internal playlist.
		If track is None, or not provided, this method returns the current track index."""
		if type(track) == type(None):
			return self.sendMessage(0x400, 0, 125)
		
		return self.sendMessage(0x400, track, 121)
		
	def trackName(self):
		"""Currently returns the filename of the playing song."""
		## Shalabh's library used GetWindowText here. However, in newer
		## versions of winamp, the window text scrolls and creates a 
		## chopped version of the song title limited to a set width.
		return list(filter(lambda x:not x or not x[0]=='#', self.playList().split('\n')))[self.currentTrack()].strip()
		
		
	
	def numTracks(self):
		"""Returns the number of tracks in the playlist"""
		return self.sendMessage(0x400, 0, 124)
	
	
	def sampleRate(self):
		"""Returns the sample rate of the playing song"""
		return self.sendMessage(0x400, 0, 126)
		
	def bitRate(self):
		"""Returns the bit rate of the playing song"""
		return self.sendMessage(0x400, 1, 126)
		
	def numChannels(self):
		"""Returns the number of channels in the playing song"""
		return self.sendMessage(0x400, 2, 126)
		
	
	def dumpList(self):
		"""Dumps the current playlist into WINAMPDIR/winamp.m3u 
		and returns the current position in the playlist"""
		return self.sendMessage(0x400, 0, 120)
	
	def playList(self):
		"""Returns a copy of the internal playlist. This method calls dumpList() internally."""
		self.dumpList()
		plf = open(self.dumpPath,'r')
		pl = plf.read()
		plf.close()
		return pl
	
	def seek(self, msecs=0):
		"""Seeks within the currently playing track. The time input is in milliseconds"""
		return self.sendMessage(0x400, msecs, 106)
	
	def setVolume(self, vol):
		"""Set the volume. The volume is a number from 0 to 255"""
		if vol > 255: vol = 255
		if vol < 0: vol = 0
		return self.sendMessage(0x400, vol, 122)


class Remote():
	""" Convenience class"""
	sock = None
	host = ""
	port = 6969
	password = "whipit"
	exit_on_close = False
	
	def __init__(self, host=None, port=None, password=None):
		if host: 	self.host = host
		if port:	self.port = port
		if password: self.password = password
		
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host, self.port))
		
		if self.password:
			self.passwd(self.password)
		return
	
	def __del__(self):
		if self.exit_on_close:
			self.send('close')
			
		self.sock.close()
		return
	
	def send(self, text):
		return self.sock.sendall(bytes(text + "\n", "utf-8"))
		
	def inout(self, cmd):
		self.send(cmd)
		return self.sock.recv(1024).decode('utf8')
	
	def playback(self, cmd):
		return self.inout(cmd)
		
	def seek(self, x):
		return self.inout("seek {0}".format(x))
		
	def setVolume(self, x):
		return self.inout("setvolume {0}".format(x))
		
	def passwd(self, x):
		return self.inout("passwd {0}".format(x))
	
	def open(self):
		return self.inout("open")
	
	def close(self):
		return self.inout("close")
		
	def version(self):
		return self.inout("version")
		
	def running(self):
		return self.inout("running")
		
	def playlist(self):
		return self.inout("playlist")
		
	def playStatus(self):
		return self.inout("playstatus")
		
	def trackName(self):
		return self.inout("trackname")
		
	def currentTrack(self):
		return self.inout("currenttrack")
		
	def numTracks(self):
		return self.inout("numtracks")
		
	def mute(self):
		return self.inout("setvolume 0")
		
	def play(self):
		return self.inout("play")
		
	def stop(self):
		return self.inout("stop")
		
	def pause(self):
		return self.inout("pause")
		
	def next(self):
		return self.inout("next")
		
	def prev(self):
		return self.inout("prev")
		
	def fadeout(self):
		return self.inout("fadeout")
		
	def forward(self):
		return self.inout("forward")
		
	def rewind(self):
		return self.inout("rewind")
		
	def volUp(self):
		return self.inout("volup")
		
	def volDown(self):
		return self.inout("voldown")
		
	def bitRate(self):
		return self.inout("bitrate")
		
	def sampleRate(self):
		return self.inout("samplerate")
		
	def numChannels(self):
		return self.inout("numchannels")
		
	
	

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
		
		cmd = cmd.lower()
		
		print(cmd, params)
		
		if cmd in self.winamp.playback_codes:
			if not self.authd: return self.unathd()
			self.winamp.playback(cmd)
			return self.send('1 Success')
		
		elif cmd == 'version':
			if not self.authd: return self.unathd()
			return self.send('VERSION {0}'.format(self.winamp.version))
			
		elif cmd == 'playstatus':
			if not self.authd: return self.unathd()
			return self.send('PLAYSTATUS {0}'.format(self.winamp.playStatus()))
			
		elif cmd == 'trackname':
			if not self.authd: return self.unathd()
			return self.send('TRACKNAME {0}'.format(self.winamp.trackName()))
			
		elif cmd == 'running':
			if not self.authd: return self.unathd()
			return self.send('RUNNING {0}'.format(self.winamp.running()))
			
		elif cmd == 'samplerate':
			if not self.authd: return self.unathd()
			return self.send('SAMPLERATE {0}'.format(self.winamp.sampleRate()))
			
		elif cmd == 'bitrate':
			if not self.authd: return self.unathd()
			return self.send('BITRATE {0}'.format(self.winamp.bitRate()))
			
		elif cmd == 'numchannels':
			if not self.authd: return self.unathd()
			return self.send('NUMCHANNELS {0}'.format(self.winamp.numChannels()))
			
		elif cmd == 'setvolume':
			if not self.authd: return self.unathd()
			return self.send('SETVOLUME {0}'.format(self.winamp.setVolume(int(params[0]))))
			
		elif cmd == 'seek':
			if not self.authd: return self.unathd()
			return self.send('SEEK {0}'.format(self.winamp.seek(int(params[0]))))
			
		elif cmd == 'currenttrack':
			if not self.authd: return self.unathd()
			return self.send('CURRENTTRACKS {0}'.format(self.winamp.currentTrack()))
			
		elif cmd == 'numtracks':
			if not self.authd: return self.unathd()
			return self.send('NUMTRACKS {0}'.format(self.winamp.numTracks()))
			
			
		elif cmd == 'playlist':
			if not self.authd: return self.unathd()
			return self.send('PLAYLIST '+';'.join(self.winamp.playList().split()))
		
		
		elif cmd == 'commands' or cmd == 'help' or cmd == '?' or cmd == '/?':
			# TODO: add all the commands here
			return self.send('"play" | "pause" | "next" | "prev" | "stop" | "fadeout" | "forward" | "rewind" | "volup" | "voldown" | "passwd" | "playlist" | "commands" | "open" | "close" | "seek [milliseconds]" | "setvolume [0-255]" | "numtracks" | "currenttrack" | "playstatus" | "running" | "bitrate" | "samplerate" | "numchannels" | "trackname" | "version" | "playcd" | "stopafter" | "playlist-beg" | "playlist-end" | "repeat" | "shuffle" | "backten" | "playcd"')
			
			
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
	HOST, PORT = "", 6969

	server = RemoteServer((HOST, PORT), RemoteServer_handler)
	server.remote_open = True
	server.remote_close = True

	server.serve_forever()
	input()


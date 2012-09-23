import winampwhip
import traceback

try:

	remote = winampwhip.Remote("127.0.0.1")
	remote.play()
	input("done.")
	
except:
	traceback.print_exc()
	input()
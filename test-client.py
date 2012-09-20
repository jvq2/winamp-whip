import socket
import sys


HOST, PORT = "localhost", 6969
#data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	# Connect to server
	sock.connect((HOST, PORT))
	while True:
		data = input("Send: ")
		sock.sendall(bytes(data + "\n", "utf-8"))
		
		# Receive data from the server
		received = str(sock.recv(1024), "utf-8")
		print("Received: {0}".format(received))
		
finally:
	sock.close()

input()
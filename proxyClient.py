import socket
import sys

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print ("USAGE {} [PORT]".format(argv[0]))
		exit(0)

	port = int(sys.argv[1])
	
	servFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	servFd.connect(('0.0.0.0',port))

	message = servFd.recv(1023)

	print("SERVER SAYS: {}".format(message))

	servFd.close()


	
	
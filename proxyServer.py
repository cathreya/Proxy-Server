import socket
import sys
import threading


class ProxyServer:

	def __init__(self,port):
		self.port = port

		try:
			self.servFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			print("Failed at create socket")
			exit(1)

		self.servFd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.servFd.bind(("",port))
		except Exception as e:
			print("Failed at Bind")
			print(e)
			exit(1)

		try:
			self.servFd.listen(5)
		except:
			print("Failed at Listen")
			exit(1)

		print("Listening on port {}".format(port))

	def acceptClients(self):
		while(True):
			clientFd, clientAddr = self.servFd.accept()
			print("Connected to {}".format(clientAddr))

			clientThread = threading.Thread(target=self.handleClient, args=(clientFd,clientAddr))

			clientThread.setDaemon(True)
			clientThread.start()


	def handleClient(self, clientFd, clientAddr):
		message = "Welcome to the server"

		clientFd.send(message)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print ("USAGE {} [PORT]".format(argv[0]))
		exit(0)

	port = int(sys.argv[1])
	server = ProxyServer(port)
	server.acceptClients()

	
	
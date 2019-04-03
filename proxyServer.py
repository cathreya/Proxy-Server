import socket
import sys
import threading


class ProxyServer:

	def __init__(self,port):
		self.port = port
		self.maxMessageSize = 1000000

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

	def authenticate(self, tok):
		with open("proxyAuth.txt", 'r') as o:
			auth = o.readline()

		print(auth)
		print(tok)

		return auth.strip() == tok.strip()

	def acceptClients(self):
		while(True):
			clientFd, clientAddr = self.servFd.accept()
			print("Connected to {}".format(clientAddr))

			clientThread = threading.Thread(target=self.handleClient, args=(clientFd,clientAddr))

			clientThread.setDaemon(True)
			clientThread.start()


	def handleClient(self, clientFd, clientAddr):

		message = clientFd.recv(self.maxMessageSize)

		cliReq = message.decode("utf_8")
		# print(message[:-2])
		# print(cliReq)

		addr,path,port,auth = self.parseRequest(cliReq)

		if not self.authenticate(auth):
			print("Auth Failed")
			clientFd.sendall(b"HTTP/1.1 403 Forbidden\nContent-Type: text/plain\nContent-Length: 21\n\nInvalid Authorization")
			clientFd.close()
			return

		
		rep = cliReq.replace("http://"+addr+":"+str(port)+path, path)
		print(rep)

		try:
			destFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			destFd.settimeout(1)
			print(addr,port)
			destFd.connect((addr,port))
			destFd.sendall(rep.encode("utf_8"))

			while True:
				data = destFd.recv(self.maxMessageSize)
				if(len(data) > 0):
					clientFd.sendall(data)
				else:
					break

			destFd.close()
			clientFd.close()
			print("Done")

		except Exception as e:
			print("Error retrieving from destination")
			print(e)
			if destFd:
				destFd.close()
			if clientFd:
				clientFd.sendall(b"HTTP/1.1 500 Internal Server Error\nContent-Type: text/plain\nContent-Length: 33\n\nError retrieving from destination")
				clientFd.close()
					





	def parseRequest(self, request):
		# b'GET http://127.0.0.1/ HTTP/1.1\r\n
		# Host: 127.0.0.1\r\n
		# User-Agent: python-requests/2.18.4\r\n
		# Accept-Encoding: gzip, deflate\r\n
		# Accept: */*\r\n
		# Connection: keep-alive\r\n\r\n'

		req = request.split("\r\n")

		addr = req[0].split(" ")[1]
		
		l = request.find("Authorization: Basic ")
		if not l:
			return -1
		r = request[l:].find("\r\n")
		l += len("Authorization: Basic ")


		auth = request[l:l+r]

		if len(addr.split(":")) < 3:
			port = 8080
		else:
			tmp = addr.split(":")[2]
			l = tmp.find("/")
			port = int(tmp[:l])



		l = addr.find("//")
		addr = addr[l+2:]
		

		path = addr.find("/")

		path = addr[path:]

		r = addr.find(":")
		addr = addr[:r]


		
		return (addr,path,port,auth)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print ("USAGE {} [PORT]".format(argv[0]))
		exit(0)

	port = int(sys.argv[1])
	server = ProxyServer(port)
	server.acceptClients()

	
	
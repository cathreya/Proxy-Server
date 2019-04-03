import socket
import sys
import threading


class ProxyServer:

	def __init__(self,port):
		self.port = port
		self.maxMessageSize = 1000000
		self.cache = {}

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

		message = clientFd.recv(self.maxMessageSize)

		cliReq = message.decode("utf_8")
		# print(message[:-2])
		# print(cliReq)

		addr, path, port = self.getDestServer(cliReq)
		print("Address: " + addr + "\nPath: " + path + "\nPort: " + str(port))
		requestUrl = "http://" + addr + ":" + str(port) + path
		
		rep = cliReq.replace(requestUrl, path)
		print(rep)

		# Won't work with large messages yet
		if self.checkCache(requestUrl):
			data = self.getCache(requestUrl)
			clientFd.sendall(data)

		try:
			destFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			destFd.settimeout(1)
			print(addr,port)
			destFd.connect((addr,port))
			destFd.sendall(rep.encode("utf_8"))
			dataBegin = True
			while True:
				data = destFd.recv(self.maxMessageSize)
				if(len(data) > 0):
					print(data)
					self.addCache(requestUrl, data, dataBegin)
					clientFd.sendall(data)
					dataBegin = False
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
				clientFd.sendall(b"Error retrieving data from the destination")
				clientFd.close()

	def checkCache(self, requestUrl):
		return False

	def getCache(self, requestUrl):
		return None

	def addCache(self, requestUrl, data, dataBegin):
		pass

	def blacklisted(self, host):
		blacklist_file = "blacklist.txt"

		try:
			with open(blacklist_file, 'r') as f:
				b_list = f.readlines() # read file into list
		except IOError:
			print("{} not found; unable to check for blacklisting".format(blacklist_file))
			return False # return not blacklisted

		ip = socket.gethostbyname(host) # get ip of client requested url
		ip = parseBlack(ip)

		for cidr in b_list:
			flag = True
			c = parseBlack(cidr)

			for i in range(len(c)):
				if c[i] != ip[i]:
					flag = False
					break 

			if flag:
				return flag
					
		return flag

	def parseBlack(self, address):
		cidr_flag = address.find("/")

		if cidr_flag == -1:
			domain = address
			cidr_flag = False
		else:
			domain = address[:cidr_flag]
			sig = int(address[(cidr_flag + 1):])
		
		domain = domain.split(".")
		for i in range(len(domain)):
			domain[i] = format(int(domain[i]), 'b') # convert segment to binary string

			temp = ""
			if len(domain[i]) < 8:
				for j in range(8 - len(domain[i])):
					temp += "0"
			domain[i] = temp + domain[i] # convert to 8 bit binary string
		domain = "".join(domain)

		if cidr_flag:
			return domain[:sig] # cutoff at sig if cidr
		
		return domain


	def getDestServer(self, req):
		# b'GET http://127.0.0.1/ HTTP/1.1\r\n
		# Host: 127.0.0.1\r\n
		# User-Agent: python-requests/2.18.4\r\n
		# Accept-Encoding: gzip, deflate\r\n
		# Accept: */*\r\n
		# Connection: keep-alive\r\n\r\n'

		req = req.split("\r\n")
		addr = req[0].split(" ")[1]
		
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


		
		return (addr,path,port)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print ("USAGE {} [PORT]".format(argv[0]))
		exit(0)

	port = int(sys.argv[1])
	server = ProxyServer(port)
	server.acceptClients()

	
	
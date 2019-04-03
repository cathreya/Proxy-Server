import socket
import sys
import threading
from datetime import datetime


class ProxyServer:

	def __init__(self,port):
		self.port = port
		self.maxMessageSize = 1000000
		self.cache = {}
		self.cache_timestamp = {}

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


		# print("Address: " + addr + "\nPath: " + path + "\nPort: " + str(port))
		requestUrl = "http://" + addr + ":" + str(port) + path

		addr,path,port,auth = self.parseRequest(cliReq)

		if not self.authenticate(auth):
			print("Auth Failed")
			clientFd.sendall(b"HTTP/1.1 403 Forbidden\nContent-Type: text/plain\nContent-Length: 21\n\nInvalid Authorization")
			clientFd.close()
			return


		
		rep = cliReq.replace(requestUrl, path)
		# print(rep)


		# First thing the server does is check if the requested data is in the
		# cache (checkCache) or not. If it is, it checks if it's modified since: 
		# then it re-requests the data (checkCache returns False). If not 
		# modified, it sends the data from cache (getCache).
		# If it is not in cache, we add timestamp to list of requests 
		# (addCache) and check if three requests were made in the last 5 minutes. 
		# If yes, we cache it (addCache). Since there's a maximum of 3 cache values 
		# allowed, if we have to remove a cache value for making space (addCache) 
		# we look at the oldest timestamp.

		# Won't work with large messages yet
		if self.checkCache(requestUrl):
			# All this interface is concerned with is getting the data. Validation, 
			# etc is handled by the function
			data = self.getCache(requestUrl)
			print("-"*20 + "\nDATA FROM CACHE\n" + "-"*20)
			print(data)
			clientFd.sendall(data)
			return

		try:
			destFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			destFd.settimeout(1)
			# print(addr,port)
			destFd.connect((addr,port))
			destFd.sendall(rep.encode("utf_8"))

			print("-"*20 + "\nDATA SENT TO SERVER FROM PROXY\n" + "-"*20)
			print(rep)

			dataBegin = True
			
			print("-"*20 + "\nPART DATA RECEIVED TO PROXY FROM SERVER\n" + "-"*20)
			while True:
				data = destFd.recv(self.maxMessageSize)
				if(len(data) > 0):
					print(data)

					# Add to cache - if validated
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
				clientFd.sendall(b"HTTP/1.1 500 Internal Server Error\nContent-Type: text/plain\nContent-Length: 33\n\nError retrieving from destination")
				clientFd.close()
					

	def checkCache(self, requestUrl):
		'''
		Checks if data has been requested in the last 5 minutes. Updates 
		cache for timeouts.
		'''

		if not requestUrl in self.cache_timestamp:
			self.cache_timestamp[requestUrl] = []
		
		# Adding the time to list
		self.cache_timestamp[requestUrl].append(datetime.now())

		if not requestUrl in self.cache:
			return False

		# Check for outdated

		return True

	def getCache(self, requestUrl):
		'''
		Returns the data stored in the cache 
		'''
	
		return self.cache[requestUrl]

	def addCache(self, requestUrl, data, dataBegin):
		'''
		Checks if data has been requested (more than) thrice in the last 5 
		minutes. If so, it adds the data to the cache.
		'''

		# Return if less than 3 requests
		if len(self.cache_timestamp[requestUrl]) < 3:
			return
		
		# Return if 3 requests were over 5 minutes
		timediff = datetime.now() - self.cache_timestamp[requestUrl][-3]
		if timediff.seconds > 300:
			return 


		# Add data to cache
		print("*****Adding data to cache*****")
		if dataBegin:
			if not requestUrl in self.cache:
				self.cache[requestUrl] = ""
			self.cache[requestUrl] = data
		else:
			self.cache[requestUrl] += data
	

		# If the cache now contains 4 values, remove oldest one
		if len(self.cache) == 4:
			oldkey = requestUrl
			for key in self.cache:
				if self.cache_timestamp[key][-1] < self.cache_timestamp[oldkey][-1]:
					oldkey = key
			del self.cache[oldkey]


	def blacklisted(self, host):
		blacklist_file = "blacklist.txt"

		try:
			with open(blacklist_file, 'r') as f:
				b_list = f.readlines() # read file into list
		except IOError:
			print("{} not found; unable to check for blacklisting".format(blacklist_file))
			return False # return not blacklisted

		ip = socket.gethostbyname(host) # get ip of client requested url
		ip = self.parseBlack(ip)

		for cidr in b_list:
			flag = True
			c = self.parseBlack(cidr)

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

	
	
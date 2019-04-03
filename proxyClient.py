import socket
import sys
import requests

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print ("USAGE {} [MYPORT] [PROXY_PORT]".format(argv[0]))
		exit(0)

	port = int(sys.argv[2])
	myport = int(sys.argv[1])
	# servFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# servFd.connect(('0.0.0.0',port))

	# message = servFd.recv(1023)

	# print("SERVER SAYS: {}".format(message))

	# servFd.close()

	# os.system("curl --request %s --proxy 127.0.0.1:%s --local-port %s 127.0.0.1:%s/%s" % (METHOD, PROXY_PORT, CLIENT_PORT, SERVER_PORT, filename))

	proxyaddr = "http://127.0.0.1:{}".format(str(port)) 
	sproxyaddr = "https://127.0.0.1:{}".format(str(port)) 

	proxy = {"http": proxyaddr, 
			 "https": sproxyaddr}

	# r = requests.get('http://127.0.0.1:7201', proxies = proxy, auth=("proxy@proxy","theearthisflat"))
	# r = requests.get('http://127.0.0.1:7204/file.txt', proxies = proxy, auth=("proxy@proxy","theearthisflat"), )
	# r = requests.get('http://127.0.0.1:7201/file.txt', proxies = proxy, auth=("proxy@proxy","theearthisflatnot"))
	r = requests.get('http://192.0.2.17:8080/file.txt', proxies = proxy, auth=("proxy@proxy","theearthisflat"))
	# r = requests.get('http://127.0.0.1:7200/2.data')
	
	print(r.status_code)
	print(r.text)

	copied = open("copy","wb")
	copied.write(r.text.encode("utf_8"))
	copied.close()
	
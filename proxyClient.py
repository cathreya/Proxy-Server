import socket
import sys
import requests

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print ("USAGE {} [PORT]".format(argv[0]))
		exit(0)

	port = int(sys.argv[1])
	
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

	r = requests.get('http://127.0.0.1:7201/file.txt', proxies = proxy)
	# r = requests.get('http://127.0.0.1:7200/2.data')
	
	print(r.text)
	print("\n")

	copied = open("copy","wb")
	copied.write(r.text.encode("utf_8"))
	copied.close()
	
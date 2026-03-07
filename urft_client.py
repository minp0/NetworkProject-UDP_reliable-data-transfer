import sys
import socket

def main():
    if __name__ == "__main__": # run when this file is executed -> not a module
        if len(sys.argv) !=4 :
            print("Error, input not valid -> python urft_client.py <file_path> <server_ip> <server_port> ")
        else:
            # init value
            file_path = sys.argv[1]
            server_ip = sys.argv[2]
            server_port = sys.argv[3]
            print(f"{file_path}, {server_ip}, {server_port}")
            start_client(file_path, server_ip, server_port)


def start_client(path, ip, port):
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    s.sendto(path.encode('utf-8'),(ip, port))
    message, addr_serv= s.recvfrom(2048)
    print(message.decode())
    s.close()     

# main()
start_client("something","localhost", 12345)
# start_client("something","25.12.207.234", 10000)

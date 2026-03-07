import sys
import socket

from realiable import *

def main():
    if __name__ == "__main__": # run when this file is executed -> not a module
        if len(sys.argv) !=3 :
            print("Error, input not valid -> python urft_server.py <server_ip> <server_port> ")
        else:
            # init value
            server_ip = sys.argv[2]
            server_port = sys.argv[3]
            # print(f"{server_ip}, {server_port}")
            start_server(server_ip, server_port)

def start_server(ip, port):
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    s.bind((ip, port))
    message, addr_client = s.recvfrom(2048)

    # ต้องเป็น ip ที่ server รอฟัง ไม่ใช่ว่ารอฟังจาก ip ไหน
    while True:
        print("Got connection from", addr_client)
        s.sendto("Hello from server".encode('utf-8') , addr_client)
        break


# main()
start_server("loopback", 10000)
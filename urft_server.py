import sys
import socket

from realiable import *

def main():
    if __name__ == "__main__": # run when this file is executed -> not a module
        if len(sys.argv) !=3 :
            print("Error, input not valid -> python urft_server.py <server_ip> <server_port> ")
        else:
            # init value
            server_ip = sys.argv[1]
            server_port = int(sys.argv[2])
            # print(f"{server_ip}, {server_port}")
            start_server(server_ip, server_port)

def start_server(ip, port):
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    s.bind((ip, port))

    print(f"Receiver ready at {ip}:{[port]}...")

    # ต้องเป็น ip ที่ server รอฟัง ไม่ใช่ว่ารอฟังจาก ip ไหน
    try:
        while True:
            message, addr_client = s.recvfrom(2048)
            print("Got connection from ->", addr_client)
            
            # Make new Class เฉยๆ
            packet = Segment()
            s.sendto(packet.unpack(message) , addr_client)

    except KeyboardInterrupt:
        print("Shutting down by keyboard input")
        


# main()
start_server("loopback", 10000)
# start_server("192.168.10.116", 10000)   
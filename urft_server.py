import sys
import socket

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
    s.listen(1) # only listen to 1 connection at a time


    # ต้องเป็น ip ที่ server รอฟัง ไม่ใช่ว่ารอฟังจาก ip ไหน
    while True:
        c, addr = s.accept()
        print("Got connection from", addr)
        c.send("Hello from server".encode())
        c.close()
        break


# main()
start_server("localhost", 12345)
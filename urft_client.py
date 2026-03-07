import sys
import socket
import time

from realiable import *

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


# Mock data
messages = ["Hello!", "UDP-RDT", "Testing"]

def start_client(path, ip, port):
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    for i,msg in enumerate(messages):
        seq_num = i + 1
        msg_bytes = msg.encode('utf-8')  
        
        segment = Segment()
        packet = segment.pack(12345,10000,0,seq_num,0,msg_bytes)
        s.sendto(packet,(ip,port))

        # timer for ack
        try:
            s.settimeout(0.2)       # 200 millisecond
            ack_data , _  = s.recvfrom(2048)
            segment.unpack(ack_data) 
        except s.timeout:
            print("Timeout! Packet might be lost.")



    # s.sendto(path.encode('utf-8'),(ip, port))
    # message, addr_serv= s.recvfrom(2048)
    # print(message.decode())
    s.close()     



main()
# start_client("something","loopback", 10000)
# start_client("something","25.12.207.234", 10000)

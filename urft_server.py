import sys
import socket
import time

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

    print(f"Receiver ready at {ip}:{port}...")

    # ต้องเป็น ip ที่ server รอฟัง ไม่ใช่ว่ารอฟังจาก ip ไหน
    try:

        segment = Realiable()
        file_name, addr_client = segment.standby_connection(s)

        global start_time
        start_time = time.time()
        print(f"\n[SERVER] Receiving file: {file_name}")

        # Create/overwrite file for receiving data
        with open(file_name, "wb") as file:
            bytes_received = 0
            
            while True:
                try:
                    s.settimeout(socket_timeout)
                    packet, current_addr = s.recvfrom(BUFFER_SIZE)
                    
                    # Only accept packets from the connected client
                    if current_addr != addr_client:
                        continue
                    
                    # Unpack the packet
                    message, seq, data_len = segment.unpack(packet)
                    
                    # Get flag from packet header
                    flag = packet[0]
                    
                    if flag == 2:  # Data packet
                        # Extract actual payload (remove null padding)
                        payload = packet[11:]
                        file.write(payload)             # เวลา write file ต้อง write เป็น binary
                        bytes_received += data_len
                        
                        # Send ACK
                        ack_packet = segment.pack_ACK(seq, data_len)
                        s.sendto(ack_packet, addr_client)
                        print(f"[ACK] Sent ACK for seq {seq}, total received: {bytes_received} bytes")
                        
                    elif flag == 4:  # FIN packet
                        print(f"\n[FIN] Received FIN packet, file transfer complete!")
                        print(f"[SUCCESS] File '{file_name}' saved ({bytes_received} bytes)")
                        break
                    
                except socket.timeout:
                    print("[TIMEOUT] No more data received, closing connection")
                    break
                # except Exception as e:
                #     print(f"[ERROR] {e}")
                #     break
        
        print("[READY] Waiting for next connection...\n")


    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down by keyboard input")
        
    finally: 
        print("Close socket")
        s.close()


# main()

import os
if os.path.exists("Hello Min _Outputfile.bin"):
    os.remove("Hello Min _Outputfile.bin")

start_time = 0
start_server("loopback", 10000)
end_time = time.time()
print(f"Total time : {end_time-start_time:.2f} seconds")
# start_server("192.168.10.116", 10000)   
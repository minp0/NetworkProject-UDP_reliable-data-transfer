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

        # ใช้ `Realiable` สำหรับการ pack/unpack และฟังก์ชัน ACK/retransmit
        # คอมเมนต์ภาษาไทย: เราใช้คลาสนี้เพื่อให้โค้ดจัดการฟอร์แมตของแพ็กเก็ตและการส่ง ACK ได้สะดวกขึ้น
        segment = Realiable()
        file_name, addr_client, hs_seq = segment.standby_connection(s)

        global start_time
        start_time = time.time()
        print(f"\n[SERVER] Receiving file: {file_name}")

        # คำนวณ expected_seq สำหรับการรับ packet ข้อมูลต่อไป
        expected_seq = hs_seq

        # ใช้ receive_with_dictionary() สำหรับ Selective Repeat
        print(f"[WINDOW] Starting Selective Repeat with Dictionary tracking")
        received_data, bytes_received, fin_received = segment.receive_with_dictionary(s, expected_seq)
        
        if received_data is not None and fin_received:
            # Create/overwrite file only when transfer is complete
            with open(file_name, "wb") as file:
                file.write(received_data)
            print(f"[SUCCESS] File '{file_name}' saved ({bytes_received} bytes)")
        else:
            print(f"[ERROR] Failed to receive complete file")
            bytes_received = 0
        
        # Print statistics and close connection
        end_time = time.time()
        elapsed_time = end_time - start_time
        if bytes_received > 0:
            throughput = (bytes_received * 8) / elapsed_time / 1_000_000  # Mbps
            print(f"[STATS] Time: {elapsed_time:.2f}s, Throughput: {throughput:.2f} Mbps")
        
        print(f"\n[SERVER] File transfer complete. Closing connection...")
        # Return immediately to exit the function
        return


    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down by keyboard input")
        
    finally: 
        print("Close socket")
        s.close()


# start_server("loopback", 10000)
# main()

# import os
# if os.path.exists("Hello Min _Outputfile.bin"):
#     os.remove("Hello Min _Outputfile.bin")

start_time = 0
bytes_received = 0
# start_server("loopback", 10000)
main()
# start_server("192.168.10.116", 10000)   

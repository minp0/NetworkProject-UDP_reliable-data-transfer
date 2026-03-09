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
        file_name, addr_client, hs_seq, hs_len = segment.standby_connection(s)

        global start_time
        start_time = time.time()
        print(f"\n[SERVER] Receiving file: {file_name}")

        # คำนวณ expected_seq = seq ซ้ายใหม่ของ handshake + data_len ของ handshake
        # นี่คือค่ีจะหรคบขอมูลที่ server คาดว่า seq ของแผนกตอไป
        expected_seq = hs_seq + hs_len

        # Create/overwrite file for receiving data
        with open(file_name, "wb") as file:
            bytes_received = 0
            last_ack_packet = None  # Track last ACK sent for retransmit on timeout
            timeout_counter = 0  # Count consecutive timeouts
            max_timeout_retries = 5  # Max retransmit attempts on timeout
            
            while True:
                try:
                    s.settimeout(socket_timeout)
                    packet, current_addr = s.recvfrom(BUFFER_SIZE)
                    
                    # Only accept packets from the connected client
                    if current_addr != addr_client:
                        continue
                    
                    # Unpack the packet payload and metadata
                    message, seq, data_len = segment.unpack(packet)
                    flag = packet[0]

                    if flag == 2:  # Data packet
                        if seq == expected_seq:
                            # แพ็กเก็ตมาตามคหมาย หรือเป็นลำดับ จีงเลยกมีค่า expected_seq
                            file.write(message)
                            bytes_received += data_len
                            # ส่ง ACK กลับเท่ยัวว่าเก็ตขอมูลของชนิด data_len
                            ack_packet = segment.pack_ACK(seq, data_len)
                            s.sendto(ack_packet, addr_client)
                            print(f"[ACK] Sent ACK for seq {seq}, total received: {bytes_received} bytes")
                            # บันทึก ACK นี้ไว้ เพื่อใช้ในการส่งซ้ำถ้า timeout
                            last_ack_packet = ack_packet
                            timeout_counter = 0  # รีเซ็ต timeout counter เมื่อได้รับข้อมูลใหม่
                            # อัปเดท expected_seq เพื่อไปที่ซ้ายใหม่ถัดไป
                            expected_seq += data_len

                        elif seq < expected_seq:
                            # แพ็กเก่ชำซ้ำไหน (packet ที่ได้รับมากก่อนหน้า) -> ส่ง ACK นั้นอีกครั้ง
                            # client จะตรวจสอบ ACK แนว ลางส่ง packet ที่ตามมาตามคหมาย
                            ack_packet = segment.pack_ACK(seq, data_len)
                            s.sendto(ack_packet, addr_client)
                            print(f"[DUP] Duplicate Seq {seq} -> resent ACK")
                            last_ack_packet = ack_packet

                        else:
                            # แผฟปรรด (future packet): ไม่สนใจ จอยคอยหน้าซนิดที่หายไป
                            print(f"[OUT-OF-ORDER] Received Seq {seq}, expected {expected_seq} -> ignoring")

                    elif flag == 4:  # FIN packet
                        print(f"\n[FIN] Received FIN packet, file transfer complete!")
                        print(f"[SUCCESS] File '{file_name}' saved ({bytes_received} bytes)")
                        break
                    
                except socket.timeout:
                    # ถ้า timeout ให้ส่ง ACK ที่เก็บไว้อีกครั้ง (retransmit last ACK)
                    # เพื่อให้ client ถ้า ACK สูญหาย client จะ retransmit packet มา
                    if last_ack_packet is not None:
                        timeout_counter += 1
                        print(f"[TIMEOUT] No data, retransmitting last ACK (attempt {timeout_counter}/{max_timeout_retries})")
                        s.sendto(last_ack_packet, addr_client)
                        if timeout_counter >= max_timeout_retries:
                            print(f"[TIMEOUT] Max retransmit attempts reached, closing connection")
                            break
                    else:
                        # ยังไม่ส่ง ACK ครั้งแรก ให้รอแพ็กเก็ตต่อไป
                        print("[TIMEOUT] Waiting for first data packet...")
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
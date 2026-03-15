import sys
import socket
import os

from realiable import *

def main():
    if __name__ == "__main__": # run when this file is executed -> not a module
        if len(sys.argv) != 4:
            print("Error, input not valid -> python urft_client.py <file_path> <server_ip> <server_port>")
        else:
            # init value
            file_path = sys.argv[1]
            server_ip = sys.argv[2]
            server_port = int(sys.argv[3])
            print(f"Sending file: {file_path} to {server_ip}:{server_port}")
            start_client(file_path, server_ip, server_port)

# file_name = "Hello Min _Outputfile.bin"

def start_client(file_path, server_ip, server_port):
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    segment = Realiable()
    
    file_name = os.path.basename(file_path) 
    try:
        # Step 1: Handshake - send filename
        # เดี๋ยวต้องมาแก้ ถ้าทำบน linux
        print(f"\n[HANDSHAKE] Sending filename: {file_name}")
        hs_seq, hs_len = segment.start_connecting(s, server_ip, server_port, file_name)
        # ตรวจสอบผลการ handshake
        if hs_seq == 0:
            print("[ERROR] Handshake failed")
            return
        # Step 2: Read file and send in chunks using Selective Repeat Window
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found")
            return
        file_size = os.path.getsize(file_path)
        print(f"\n[FILE INFO] Size: {file_size} bytes, Chunk size: {MSS} bytes")
        print(f"[WINDOW] Starting Selective Repeat with window size: {WINDOW_SIZE}")
        
        with open(file_path, "rb") as f:
            # อ่านไฟล์ทั้งหมดแล้วแบ่งออกเป็น chunks
            chunks = []
            while True:
                chunk = f.read(MSS)
                if not chunk:
                    break
                chunks.append(chunk)
            
            print(f"[FILE] Total chunks to send: {len(chunks)}")
            
            # คำนวณ seq ให้เริ่มจากการที่ handshake จบแล้ว
            seq_start = hs_seq + hs_len
            
            # ส่งข้อมูลโดยใช้ Selective Repeat Window
            success, fin_seq = segment.send_with_window(s, (server_ip, server_port), seq_start, chunks)
            if success:
                print(f"[SUCCESS] All {len(chunks)} chunks sent successfully!")
                
                # Step 3: Send FIN packet (after all chunks have been acked)
                print(f"\n[FINISH] Sending FIN packet...")
                fin_packet, _ = segment.pack(4, fin_seq, 0, b'')
                s.sendto(fin_packet, (server_ip, server_port))
                print(f"[FIN] FIN packet sent with seq {fin_seq}")
                
                # Wait for FIN ACK from server
                if segment.wait_ACK(s, fin_seq, 0):
                    print(f"[FIN-ACK] Received FIN ACK from server")
                elif segment.retransmit(s, fin_packet, fin_seq, 0, (server_ip, server_port), max_retries=3):
                    print(f"[FIN-ACK] Received FIN ACK after retransmit")
                else:
                    print(f"[WARN] No FIN ACK received after retransmit attempts")
            else:
                print(f"[ERROR] Failed to send file using Selective Repeat")
                s.close()
                return
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        try:
            s.close()
            print(f"[CLIENT] Socket closed")
        except:
            pass


main()
# start_client("something","loopback", 10000)
# start_client("something","25.12.207.234", 10000)
# Test with test_1MiB.bin
# start_client("../test_5MiB.bin", "192.168.10.116", 10000)

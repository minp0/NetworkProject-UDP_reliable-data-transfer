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

file_name = "Hello Min _Outputfile.bin"

def start_client(file_path, server_ip, server_port):
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    segment = Realiable()
    
    try:
        # Step 1: Handshake - send filename
        # เดี๋ยวต้องมาแก้ ถ้าทำบน linux
        print(f"\n[HANDSHAKE] Sending filename: {file_name}")
        hs_seq, hs_len = segment.start_connecting(s, server_ip, server_port, file_name)
        # ตรวจสอบผลการ handshake
        if hs_seq == 0:
            print("[ERROR] Handshake failed")
            return
        # Step 2: Read file and send in chunks
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found")
            return
        file_size = os.path.getsize(file_path)
        print(f"\n[FILE INFO] Size: {file_size} bytes, Chunk size: {MSS} bytes")
        
        with open(file_path, "rb") as f:
            # คำนวณ seq ให้เริ่มจากการที่ handshake จบแล้ว
            # seq ของแพ็กเก็ตข้อมูลจะต้องเป็น seq_handshake + len_handshake คือค่าตัวเลขลำดับต่องาน
            seq = hs_seq + hs_len  # Start No.2
            chunks_sent = 0
            
            while True:
                chunk = f.read(MSS)
                if not chunk:               # ถ้าหมดแล้วก็ break ซะ
                    break
                
                # Send data packet (flag=2)
                packet, data_len = segment.pack(2, seq, 0, chunk)
                s.sendto(packet, (server_ip, server_port))
                
                # Wait for ACK
                if segment.wait_ACK(s, seq, data_len):
                    chunks_sent += 1
                    progress = (chunks_sent * MSS / file_size) * 100
                    print(f"[PROGRESS] Chunk {chunks_sent} sent (Seq={seq}, {progress:.1f}%)")
                    seq += data_len
                else:
                    # attempt retransmit
                    print(f"[WARN] No ACK for seq {seq}, attempting retransmit")
                    if segment.retransmit(s, packet, seq, data_len, (server_ip, server_port)):
                        chunks_sent += 1
                        progress = (chunks_sent * MSS / file_size) * 100
                        print(f"[PROGRESS] Chunk {chunks_sent} sent after retransmit (Seq={seq}, {progress:.1f}%)")
                        seq += data_len
                    else:
                        print(f"[ERROR] Failed to receive ACK after retransmit for seq {seq}")
                        return
        
        # Step 3: Send FIN packet
        print(f"\n[FINISH] Sending FIN packet...")
        fin_packet, _ = segment.pack(4, seq, 0, b'')
        s.sendto(fin_packet, (server_ip, server_port))
        
        print(f"[SUCCESS] File sent! Total chunks: {chunks_sent}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        s.close()


# Test with test_1MiB.bin
start_client("test_5MiB.bin", "loopback", 10000)

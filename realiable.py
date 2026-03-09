import struct
import socket

# Network sizing: MTU(1500) - IP header(20) - UDP header(8) = 1472 bytes
BUFFER_SIZE = 1472      # 
MSS = 1461              # Payload size per packet -> MSS - 11(header)
window_size = 32768     # 32 KB (recommended for efficiency)


socket_timeout = 0.2  # 1 / 1000 * 200 millisecond

# !  flag(unsigned char) 1 | seq(unsigned int) 4 | ack | data_len | payload 
format_segment = f"!BIIH"          #  + f"{window_size}s"

# header_size = struct.calcsize(format_segment)       #    11  bytes
header_size = 11
print(f"Header size: {header_size} bytes, MSS: {MSS} bytes, Buffer: {BUFFER_SIZE} bytes")



# flag -> 0 start seq | 1 -> ack | 2 -> send data  | 4 -> fin
class Realiable():
    def __init__(self):
        self.MSS = MSS

    # for pack payload
    def pack(self, flag, seq, ack, payload:bytes) -> tuple[bytes, int] :
        """Pack packet: flag(1) + seq(4) + ack(4) + data_len(2) + payload"""
        # Ensure payload is bytes and pad to size
        data_len = len(payload)
        
        packet = struct.pack(format_segment + f"{data_len}s", flag, seq, ack, data_len, payload)
        print(f"Sending Seq {seq}...")
        return packet,data_len


    def unpack(self, packet) -> tuple[bytes, int, int]:
        """Unpack packet: extract flag, seq, ack, payload"""
        header = packet[:header_size]
        payload = packet[header_size:]

        flag, seq, ack, data_len = struct.unpack(format_segment, header)
        data = struct.unpack(f"{data_len}s", payload)[0]

        # need total_length of data for ack
        # print(data)
        # message = data.decode("utf-8").strip('\x00')
        print(f"Received Packet: Seq={seq}, Ack={ack}, Flag={flag}")

        return data, seq, data_len
    



    # for ACK
    def pack_ACK(self, seq, data_len) -> bytes :
        """pack ACK packet"""
        flag = 1  # ACK flag
        ack = seq + data_len
        ack_packet = struct.pack(format_segment, flag, 1, ack, 0)
        
        print(f"Send Ack: {ack}")
        return ack_packet
    
    def unpack_ACK(self, ack_packet) -> any :
        """Unpack ACK packet"""
        header = ack_packet[:header_size]
        flag, _, ack, _= struct.unpack(format_segment, header)
        if flag != 1:
            print("This should not happend")
            return False
        
        print(f"ACK Received for Seq: {ack}")
        return ack

    
    def wait_ACK(self, sock, seq, data_len) -> bool:
        """
        รอ ACK จาก server โดยรับ cumulative ACK (ack >= expected_ack)
        เหตุผล: ACK packet อาจมาถึง out-of-order ถ้า ack เก่ามาหลัง ack ใหม่กว่า
        ให้ discard ack เก่า และอ่านต่อจนกว่าจะได้ ack >= expected_ack
        """
        try:
            sock.settimeout(socket_timeout)
            expected_ack = seq + data_len
            
            while True:
                ack_packet, _ = sock.recvfrom(BUFFER_SIZE)
                ack = self.unpack_ACK(ack_packet)

                if ack >= expected_ack:
                    # ได้ ACK ที่ >= expected หรือ cumulative ACK
                    print(f"ACK received correctly: {ack}")
                    return True
                else:
                    # ack < expected_ack = ACK เก่าจาก packet ก่อนหน้า ให้ discard แล้วอ่านต่อ
                    print(f"[OLD ACK] Received old ACK {ack}, expected >= {expected_ack}, discarding...")
                    continue
        
        except socket.timeout:
            print("Timeout! Packet might be lost.")
            return False
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False


    # def retransmit():
        # pass

    # เพิ่มฟังก์ชัน `retransmit`: ถ้า ACK หาย ฝั่ง client จะส่ง packet ซ้ำ (retransmit)
    # ฟังก์ชันนี้พยายามส่งซ้ำจนกว่าได้รับ ACK ที่คาดหวังหรือครบจำนวน retries
    def retransmit(self, sock, packet: bytes, seq: int, data_len: int, addr, max_retries: int = 10) -> bool:
        """Retransmit `packet` to `addr` until expected ACK received or retries exhausted.

        Returns True if ACK received, False otherwise.
        
        เมื่อ ACK ไม่มาทันเวลา (timeout) หรือได้ ACK ที่ผิด ต้องส่งแพ็กเก็ตนั้นอีกครั้ง
        รับ cumulative ACK (ack >= expected) เพราะ ACK อาจมาถึง out-of-order
        ลองส่งซ้ำได้สูงสุด max_retries ครั้ง ถ้าไม่สำเร็จจะคืนค่า False
        """
        attempts = 0
        expected_ack = seq + data_len
        while attempts < max_retries:
            try:
                sock.sendto(packet, addr)
                print(f"Retransmit attempt {attempts+1} for Seq {seq}")

                sock.settimeout(socket_timeout)
                
                # อ่าน ACK ซ้ำๆ จนกว่าได้ ACK >= expected (cumulative ACK)
                while True:
                    ack_packet, _ = sock.recvfrom(BUFFER_SIZE)
                    ack = self.unpack_ACK(ack_packet)

                    if ack >= expected_ack:
                        # ได้ ACK ที่ >= expected
                        print(f"ACK received on retransmit: {ack}")
                        return True
                    else:
                        # ack < expected = ACK เก่า ให้ discard แล้วอ่านต่อ
                        print(f"[OLD ACK] Old ACK {ack}, expected >= {expected_ack}, retrying...")
                        continue

            except socket.timeout:
                print(f"Retransmit timeout attempt {attempts+1} for Seq {seq}")
            except Exception as e:
                print(f"Retransmit error: {e}")

            attempts += 1

        print(f"Retransmit failed after {max_retries} attempts for Seq {seq}")
        return False




    # first handshake -> send name of file

    def start_connecting(self, socket, server_addr, server_port, filename) -> tuple:
        """Client handshake: send filename to server (SYN with payload)
        
        Return (seq, data_len) so client can calculate correct seq for next packets
        ส่งกลับ (seq, data_len) ของ handshake เพื่อให้ client นำไปคำนวณ seq สำหรับแพ็กเก็ต data
        """
        flag = 0  # SYN flag
        seq = 1  # initial sequence
        ack = 0
        payload = filename.encode("utf-8")  # Will be padded in pack()
        
        packet, data_len = self.pack(flag, seq, ack, payload)
        socket.sendto(packet, (server_addr,server_port))
        
        print(f"Sent SYN with filename '{filename}' to {server_addr}")
        
        # Wait for ACK from server
        if not self.wait_ACK(socket, seq, data_len):
            # ถ้า ACK ไม่มาหรือเกิด timeout ให้ส่งแพ็กเก็ต handshake ซ้ำ
            if not self.retransmit(socket, packet, seq, data_len, (server_addr, server_port)):
                print("[ERROR] Handshake failed after retransmit attempts")
                return 0, 0

        return seq, data_len
        


    # for server recieve file_name
    def standby_connection(self, socket):
        """Server: wait for client SYN with filename"""
        packet, addr_client = socket.recvfrom(BUFFER_SIZE)
        print("Got connection from ->", addr_client)
        
        # Unpack SYN packet
        file_name, seq, data_len = self.unpack(packet)
        file_name = file_name.decode("utf-8")

        # Send ACK
        ack_handshake = self.pack_ACK(seq, data_len)
        socket.sendto(ack_handshake, addr_client)

        # คืน seq และ data_len ด้วย เพื่อให้ server รู้ว่า seq ต่อไปควรจะเป็นเท่าไหร่
        # server จะใช้ seq + data_len มาเป็น expected_seq สำหรับรับแพ็กเก็ตข้อมูลต่อไป
        return file_name, addr_client, seq, data_len
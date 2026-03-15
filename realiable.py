import struct
import socket
import time

# Network sizing: MTU(1500) - IP header(20) - UDP header(8) = 1472 bytes
BUFFER_SIZE = 1472
MSS = 1461              # Payload size per packet -> MSS - 11(header)
WINDOW_SIZE = 64       # Selective Repeat

socket_timeout = 0.55   # 0.55 seconds

# !  flag(unsigned char) 1 | seq(unsigned int) 4 | ack | data_len | payload 
format_segment = f"!BIIH"          #  + f"{MSS}s"

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


    def unpack(self, packet) -> tuple[bytes, int, int, int]:
        """Unpack packet: extract flag, seq, ack, payload"""
        header = packet[:header_size]
        payload = packet[header_size:]

        flag, seq, ack, data_len = struct.unpack(format_segment, header)
        if data_len > 0:
            data = struct.unpack(f"{data_len}s", payload)[0]
        else:
            data = b''

        # need total_length of data for ack
        # print(data)
        # message = data.decode("utf-8").strip('\x00')
        print(f"Received Packet: Seq={seq}, Ack={ack}, Flag={flag}, DataLen={data_len}")

        return data, seq, data_len, flag
    



    # for ACK
    def pack_ACK(self, seq) -> bytes :
        """pack ACK packet for specific sequence number"""
        flag = 1  # ACK flag
        ack = seq  # ACK for this specific seq number
        ack_packet = struct.pack(format_segment, flag, 0, ack, 0)
        
        print(f"Send Ack for seq: {ack}")
        return ack_packet
    
    def unpack_ACK(self, ack_packet) -> any :
        """Unpack ACK packet and return the seq number that was acked"""
        header = ack_packet[:header_size]
        flag, _, ack, _= struct.unpack(format_segment, header)
        if flag != 1:
            print("This should not happened - not an ACK packet")
            return None
        
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
        file_name, seq, data_len, flag = self.unpack(packet)
        file_name = file_name.decode("utf-8").strip('\x00')
        
        # Expected sequence number for next packet
        expected_seq = seq + data_len

        # Send ACK for handshake (ack for the handshake packet)
        ack_handshake = self.pack_ACK(expected_seq)
        socket.sendto(ack_handshake, addr_client)

        # คืน file_name, addr_client, และ expected_seq
        # server จะใช้ expected_seq เพื่อเตรียมรับแพ็กเก็ตข้อมูลต่อไป
        return file_name, addr_client, expected_seq
    
    
    # ====== Selective Repeat Window Methods ======
    
    def send_with_window(self, sock, addr, seq_start, payload_list, max_retries=10):
        """
        Send data using Selective Repeat with sliding window.
        
        Args:
            sock: UDP socket
            addr: Destination address (server_addr, server_port)
            seq_start: Starting sequence number
            payload_list: List of payload bytes to send
            max_retries: Maximum retransmit attempts per packet
        
        Returns:
            True if all packets sent and acked successfully, False otherwise
        """
        window_size = WINDOW_SIZE
        seq = seq_start
        
        # Track unacked packets with per-packet timer/retry state
        unacked = {}
        payload_idx = 0
        next_seq = seq_start
        last_data_seq = seq_start
        ack_poll_interval = 0.05
        
        print(f"\\n[CLIENT] Starting Selective Repeat - Window Size: {window_size}")
        
        try:
            sock.settimeout(ack_poll_interval)
            
            while payload_idx < len(payload_list) or unacked:
                
                # ===== SEND Phase: Fill the window =====
                while payload_idx < len(payload_list) and len(unacked) < window_size:
                    flag = 2  # Data flag
                    payload = payload_list[payload_idx]
                    ack_num = 0  # No ack needed for data packets
                    
                    packet, data_len = self.pack(flag, next_seq, ack_num, payload)
                    sock.sendto(packet, addr)
                    
                    unacked[next_seq] = {
                        "packet": packet,
                        "data_len": data_len,
                        "sent_at": time.monotonic(),
                        "retries": 0,
                    }
                    print(f"[WINDOW] Sent Seq {next_seq} ({len(unacked)} in window)")
                    
                    last_data_seq = next_seq
                    next_seq += data_len
                    payload_idx += 1
                
                # ===== ACK Reception Phase =====
                try:
                    ack_packet, _ = sock.recvfrom(BUFFER_SIZE)
                    acked_seq = self.unpack_ACK(ack_packet)
                    
                    if acked_seq and acked_seq in unacked:
                        del unacked[acked_seq]
                        print(f"[ACK] Removed seq {acked_seq} from window ({len(unacked)} remaining)")
                    elif acked_seq:
                        print(f"[ACK] Received ack for unknown seq {acked_seq}")
                
                except socket.timeout:
                    pass

                # ===== Packet-level retransmission =====
                now = time.monotonic()
                for pending_seq, packet_info in list(unacked.items()):
                    if now - packet_info["sent_at"] < socket_timeout:
                        continue

                    if packet_info["retries"] >= max_retries:
                        print(f"[ERROR] Seq {pending_seq} exceeded max retries ({max_retries})")
                        return False, pending_seq

                    sock.sendto(packet_info["packet"], addr)
                    packet_info["sent_at"] = now
                    packet_info["retries"] += 1
                    print(f"[RETRANSMIT] Resent Seq {pending_seq} (attempt {packet_info['retries']}/{max_retries})")
                
            print("[CLIENT] All packets sent and acked successfully!\n")
            return True, next_seq
            
        except Exception as e:
            print(f"[ERROR] Send with window failed: {e}")
            return False, seq_start
    
    
    def receive_with_dictionary(self, sock, expected_seq, total_bytes_to_receive=None):
        """
        Receive data using Selective Repeat with Dictionary to track received packets.
        
        Args:
            sock: UDP socket
            expected_seq: Starting expected sequence number
            total_bytes_to_receive: Total bytes expected (optional, for knowing when to stop)
        
        Returns:
            (received_data, total_packets_received) or (None, 0) if error
        """
        # Dictionary to track out-of-order packets: {seq: payload_bytes}
        received_packets = {}

        current_expected = expected_seq
        delivered_buffer = bytearray()
        timeout_count = 0
        max_timeouts = 10  # Increased from 3 to allow more time for Selective Repeat
        fin_received = False  # Initialize here to avoid "not associated with a value" error
        fin_seq = None
        addr_client = None
        
        print(f"\n[SERVER] Starting Selective Repeat Reception from seq {expected_seq}")
        print(f"[SERVER] Using Dictionary to track received packets\n")
        
        try:
            sock.settimeout(socket_timeout)
            
            while timeout_count < max_timeouts:
                try:
                    packet, addr_client = sock.recvfrom(BUFFER_SIZE)
                    data, seq, data_len, flag = self.unpack(packet)
                    
                    # Check for FIN packet (flag = 4)
                    if flag == 4:
                        print(f"\n[FIN] Received FIN packet from client at seq {seq}")
                        # Send ACK for FIN back to client
                        ack_pkt = self.pack_ACK(seq)
                        sock.sendto(ack_pkt, addr_client)
                        print(f"[FIN-ACK] Sent FIN ACK back to client")
                        fin_received = True
                        fin_seq = seq

                        if current_expected == fin_seq:
                            print(f"[FIN] All data received before FIN seq {fin_seq}")
                            break

                        print(f"[FIN] Waiting for missing data before FIN seq {fin_seq}")
                        timeout_count = 0
                        continue
                    
                    # Handle only DATA packets (flag = 2)
                    if flag != 2:
                        continue
                    
                    if seq < current_expected or seq in received_packets:
                        # Duplicate packet - just send ack again
                        print(f"[DUP] Seq {seq} already received, sending ack again")
                        ack_pkt = self.pack_ACK(seq)
                        sock.sendto(ack_pkt, addr_client)
                        timeout_count = 0  # Reset timeout counter - still receiving from client
                        continue
                    
                    # Store received packet in dictionary
                    received_packets[seq] = data
                    
                    # Send ACK for this specific packet
                    ack_pkt = self.pack_ACK(seq)
                    sock.sendto(ack_pkt, addr_client)
                    print(f"[RECV] Seq {seq} received and ACKed")
                    
                    # Check if we can deliver data in order
                    delivered_data = 0
                    while current_expected in received_packets:
                        payload = received_packets.pop(current_expected)
                        delivered_buffer.extend(payload)
                        delivered_data += len(payload)
                        current_expected += len(payload)
                    
                    if delivered_data:
                        print(f"[DELIVERED] Data up to seq {current_expected - 1}")

                    if fin_seq is not None and current_expected == fin_seq:
                        print(f"[COMPLETE] Missing data filled. Transfer complete up to FIN seq {fin_seq}")
                        break
                    
                    # Show status only if there are gaps (out-of-order packets)
                    all_seqs = sorted(received_packets.keys())
                    if len(received_packets) > 1:  # Only show if we have multiple packets
                        undelivered_count = len(all_seqs)
                        if undelivered_count > 0:
                            print(f"[STATUS] Received {len(received_packets)} packets, Delivered up to {current_expected - 1}, Waiting for {undelivered_count} packets")
                            # Only show first few waiting packets
                            waiting_seqs = all_seqs[:5]
                            for seq_key in waiting_seqs:
                                print(f"  - Seq {seq_key}: Gap detected, waiting for earlier packets")
                    
                    timeout_count = 0  # Reset timeout counter on successful receive
                    
                except socket.timeout:
                    if fin_seq is not None and current_expected == fin_seq:
                        print(f"[COMPLETE] Transfer already complete at FIN seq {fin_seq}")
                        break

                    timeout_count += 1
                    if timeout_count < max_timeouts:
                        print(f"[TIMEOUT] No data received (attempt {timeout_count}/{max_timeouts})")
                        # Show current status during timeout
                        if received_packets:
                            all_seqs = sorted(received_packets.keys())
                            undelivered_count = len(all_seqs)
                            print(f"[TIMEOUT-STATUS] Expected next: {current_expected}, Have {len(received_packets)} packets, Waiting for {undelivered_count}")
                        # Send acks for all received packets
                        for seq_key in received_packets:
                            ack_pkt = self.pack_ACK(seq_key)
                            sock.sendto(ack_pkt, addr_client)
                    else:
                        print(f"[TIMEOUT] Max timeouts reached, stopping reception")
                        break
                        
            print(f"[SERVER] Reception complete. Total unique packets received: {len(received_packets)}\n")

            transfer_complete = fin_seq is not None and current_expected == fin_seq
            if not transfer_complete:
                print(f"[ERROR] Transfer incomplete. Expected next seq {current_expected}, FIN seq {fin_seq}")
                return None, len(delivered_buffer), False

            # Grace window: keep socket alive briefly to ACK duplicate FIN packets
            # in case the first FIN-ACK is lost on the way to client.
            if fin_seq is not None and addr_client is not None:
                grace_deadline = time.monotonic() + (socket_timeout * 2)
                original_timeout = sock.gettimeout()
                sock.settimeout(0.1)
                try:
                    while time.monotonic() < grace_deadline:
                        try:
                            packet, late_addr = sock.recvfrom(BUFFER_SIZE)
                            _, seq, _, flag = self.unpack(packet)
                            if flag == 4 and seq == fin_seq:
                                ack_pkt = self.pack_ACK(fin_seq)
                                sock.sendto(ack_pkt, late_addr)
                                print(f"[FIN-GRACE] Re-ACK FIN seq {fin_seq}")
                        except socket.timeout:
                            continue
                finally:
                    sock.settimeout(original_timeout)

            return bytes(delivered_buffer), len(delivered_buffer), fin_received
            
        except Exception as e:
            print(f"[ERROR] Receive with dictionary failed: {e}")
            return None, 0, False
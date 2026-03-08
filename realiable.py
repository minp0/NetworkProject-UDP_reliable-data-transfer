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
        try:
            sock.settimeout(socket_timeout)
            ack_packet, _ = sock.recvfrom(BUFFER_SIZE)
            ack = self.unpack_ACK(ack_packet)

            expected_ack = seq + data_len
            if ack == expected_ack:
                print(f"ACK received correctly: {ack}")
                return True
            else:
                print(f"ACK mismatch! Expected {expected_ack}, got {ack}")
                # retransmit() ack นั้น ไม่ใช่ expected_ack
                return False
        
        # except socket.timeout:
        #     print("Timeout! Packet might be lost.")
        #     print("Retransmitting...")
        #     # retransmitt()
        #     return False
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False



    # first handshake -> send name of file

    def start_connecting(self, socket, server_addr, server_port, filename) -> bool:
        """Client handshake: send filename to server (SYN with payload)"""
        flag = 0  # SYN flag
        seq = 1  # initial sequence
        ack = 0
        payload = filename.encode("utf-8")  # Will be padded in pack()
        
        packet, data_len = self.pack(flag, seq, ack, payload)
        socket.sendto(packet, (server_addr,server_port))
        
        print(f"Sent SYN with filename '{filename}' to {server_addr}")
        
        # Wait for ACK from server
        if  self.wait_ACK(socket, seq, data_len):
            pass
            #retrans
        return data_len
        


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

        return file_name, addr_client
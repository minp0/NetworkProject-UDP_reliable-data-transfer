import struct

# Network sizing: MTU(1500) - IP header(20) - UDP header(8) = 1472 bytes
MSS = 1463              # Payload size per packet
window_size = 32768     # 32 KB (recommended for efficiency)
BUFFER_SIZE = 1472      # MSS + custom header size

# !  flag(unsigned char) 1 | seq(unsigned int) 4 | ack | payload
format_segment = f"!BII"          #  + f"{window_size}s"
header_size = struct.calcsize(format_segment)       #    9  bytes
print(f"Header size: {header_size} bytes, MSS: {MSS} bytes, Buffer: {BUFFER_SIZE} bytes")


class Realiable():
    def __init__(self):
        pass

    # for pack payload
    def pack(self, flag, seq, ack, payload):
        """Pack packet: flag(1) + seq(4) + ack(4) + payload"""
        # Ensure payload is bytes and pad to size
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        payload = payload.ljust(MSS, b'\x00')
        
        packet = struct.pack(format_segment + f"{MSS}s", flag, seq, ack, payload)
        print(f"Sending Seq {seq}...")
        return packet


    def unpack(self, packet):
        """Unpack packet: extract flag, seq, ack, payload"""
        header = packet[:header_size]
        payload = packet[header_size:]

        flag, seq, ack = struct.unpack(format_segment, header)
        data = struct.unpack(f"{MSS}s", payload)[0]


        total_length = len(data)
        message = data.decode("utf-8").strip('\x00')
        print(f"Received Packet: Seq={seq}, Ack={ack}, Flag={flag}, Msg='{message}'")

        return message, seq , total_length
    



    # for ACK
    def pack_ACK(self, seq, data_length):
        """pack ACK packet"""
        flag = 1  # ACK flag
        ack = seq + data_length
        empty_payload = b'\x00' * MSS
        ack_packet = struct.pack(format_segment + f"{MSS}s", flag, seq, ack, empty_payload)
        print(f"Send Ack: {ack}")
        return ack_packet
    
    def unpack_ACK(self, ack_packet):
        """Unpack ACK packet"""
        header = ack_packet[:header_size]
        flag, seq, ack = struct.unpack(format_segment, header)
        print(f"ACK Received for Seq: {ack}")



    # first handshake -> send name of file
    # flag -> 0 start syn | 1 -> ack | 2 ->  | 4 -> fin
    def start_connecting(self, socket, server_addr, server_port, filename):
        """Client handshake: send filename to server (SYN with payload)"""
        flag = 0  # SYN flag
        seq = 1  # initial sequence
        ack = 0
        payload = filename  # Will be padded in pack()
        
        packet = self.pack(flag, seq, ack, payload)
        socket.sendto(packet, (server_addr,server_port))
        
        print(f"Sent SYN with filename '{filename}' to {server_addr}")
        
        # Wait for ACK from server
        ack_packet, _ = socket.recvfrom(BUFFER_SIZE)
        self.unpack_ACK(ack_packet)


    # for server recieve file_name
    def standby_connection(self, socket):
        """Server: wait for client SYN with filename"""
        packet, addr_client = socket.recvfrom(BUFFER_SIZE)
        print("Got connection from ->", addr_client)
        
        # Unpack SYN packet
        file_name, seq, data_length = self.unpack(packet)
        file_name = file_name.encode('utf-8')

        # Send ACK
        ack_handshake = self.pack_ACK(seq, data_length)
        socket.sendto(ack_handshake, addr_client)

        return file_name
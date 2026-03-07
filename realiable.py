import struct

window_size = 250       # ไม่ควรเกิน 64 KB
MSS = 1450              # ไม่เกิน 1500 byte จะเต็ม MTU

# ! | src_port(unsigned short) 2 | dest_port | flag(unsigned char) 1 | seq(unsigned int) 4 | ack | payload
format_segment = f"!HHBII"          #  + f"{window_size}s"
header_size = struct.calcsize(format_segment)
print(header_size)                  # 13 bytes


class Segment():
    def old__init__(self,src_port,dest_port,flag,seq,ack,payload):
        self.payload = payload
        self.seq = seq
        self.ack = ack
        self.flag = flag
        self.src_port = src_port
        self.dest_prot = dest_port

    def old_pack(self):
        # struct.pack(format, v1, v2, ...)
        byte_stream = struct.pack(format_segment,self.src_port,self.dest_port,self.flag,self.seq,self.ack,self.payload)
        return byte_stream
    
    def __init__(self):
        pass

    def pack(self,src_port,dest_port,flag,seq,ack,payload):
        packet = struct.pack(format_segment+"10s",src_port,dest_port,flag,seq,ack,payload)

        print(f"Sending Seq {seq}...")
        return packet

    # first handshake -> send name of file
    def start_connecting(self,message):
        pass

    def unpack(self,packet):
        header = packet[:header_size]
        payload = packet[header_size:]

        src, dest, flag, seq, ack= struct.unpack(format_segment,header)
        data = struct.unpack(f"10s",payload)[0]            # มาแก้ size ทีหลัง


        print(data)
        message = data.decode("utf-8").strip('\x00')
        print(f"Received Packet: Seq={seq}, Flag={flag}, Msg='{message}'")

        return self.pack_ACK(seq)

    def pack_ACK(self,seq):
        ack_packet = struct.pack("!I", seq)
        return ack_packet
    
    def unpack_ACK(self,ack_packet):
        ack_seq = struct.unpack("!I", ack_packet)[0]
        print(f"ACK Received for Seq: {ack_seq}")

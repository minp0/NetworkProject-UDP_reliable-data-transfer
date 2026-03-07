import struct

window_size = 250 # ไม่ควรเกิน 64 KB
MSS = 1450 # ไม่เกิน 1500 byte จะเต็ม MTU

# ! | src_port(unsigned short) | dest_port | flag(unsigned char) | seq(unsigned int) | ack | payload
format_segment = f"!HHBII{window_size}s"

class Segment():
    def __init__(self,src_port,dest_port,flag,seq,ack,payload):
        self.payload = payload
        self.seq = seq
        self.ack = ack
        self.flag = flag
        self.src_port = src_port
        self.dest_prot = dest_port

    def pack(self):
        # struct.pack(format, v1, v2, ...)
        byte_stream = struct.pack(format_segment,self.src_port,self.dest_port,self.flag,self.seq,self.ack,self.payload)
        return byte_stream

    # first handshake -> send name of file
    def start_connecting(self,message):
        pass

    def unpack(self,packet):
        self.src_port,self.dest_port,self.flag,self.seq,self.ack,self.payload = struct.unpack(format_segment,packet)
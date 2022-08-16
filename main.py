#!/usr/bin/python3
import os
import socket
import struct
import sys
from enum import IntEnum
from fpm import fpm_pb2
from qpb import qpb_pb2

# To enable FPM module with protobuf, the following option in 
# /etc/frr/daemons needs to be added for zebra
# zebra_options="  -A 127.0.0.1 -s 90000000  -M fpm:protobuf"
FPM_PORT=2620

class Protocol(IntEnum):
    UNKNOWN_PROTO = 0
    LOCAL = 1
    CONNECTED = 2
    KERNEL = 3
    STATIC = 4 
    RIP = 5
    RIPNG = 6
    OSPF = 7
    ISIS = 8
    BGP = 9
    OTHER = 10


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost', FPM_PORT))
    sock.listen(1)
    while True:
        conn, client_addr = sock.accept()
        try:
            while True:
                data = conn.recv(4)
                version,msg_type,length = struct.unpack('!BBH', data)
                payload = conn.recv(length-4)
                if msg_type == 1:
                    print("Unexpected Netlink message")
                    continue

                zebra_msg = fpm_pb2.Message()
                zebra_msg.ParseFromString(payload)
                if zebra_msg.add_route:
                    r = zebra_msg.add_route
                    if r.address_family == qpb_pb2.AddressFamily.IPV4:
                        while len(r.key.prefix.bytes) < 4:
                            r.key.prefix.bytes += b'\0'
                        dst = socket.inet_ntoa(r.key.prefix.bytes)
                        next_hop = ""
                        if r.nexthops[0].if_id:
                            next_hop = str(r.nexthops[0].if_id)
                        if r.nexthops[0].address:
                            next_hop = socket.inet_ntoa(struct.pack("!I", r.nexthops[0].address.v4.value))
                        print("ADD IPV4 %s/%d via %s proto %s" % (dst, r.key.prefix.length, next_hop,
                                                                  Protocol[r.protocol]))
                        if r.protocol == Protocol.BGP:
                          os.system("ovn-nbctl lr-route-add rtr %s/%d %s " % (dst, r.key.prefix.length, next_hop))
                    if r.address_family == qpb_pb2.AddressFamily.IPV6:
                        continue
                        while len(r.key.prefix.bytes) < 16:
                            r.key.prefix.bytes += b'\0'
                        dst = socket.inet_ntoa(r.key.prefix.bytes)
                        print("%s/%d via %s" % (dst, r.key.prefix.length, str(r.nexthops)))
                        continue

                if zebra_msg.delete_route:
                    r = zebra_msg.delete_route
                    if r.address_family == qpb_pb2.AddressFamily.IPV4:
                        while len(r.key.prefix.bytes) < 4:
                            r.key.prefix.bytes += b'\0'
                        dst = socket.inet_ntoa(r.key.prefix.bytes)
                        next_hop = ""
                        print("DELETE IPV4 %s/%d " % (dst, r.key.prefix.length))
                        os.system("ovn-nbctl lr-route-del rtr %s/%d" % (dst, r.key.prefix.length))
                    continue
                print("")
        except KeyboardInterrupt:
            return
        finally:
            conn.close()
    return


if __name__ == "__main__":
    main()

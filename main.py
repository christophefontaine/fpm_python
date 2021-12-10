#!/usr/bin/python3
import socket
import struct
import sys
from fpm import fpm_pb2

# To enable FPM module with protobuf, the following option in 
# /etc/frr/daemons needs to be added for zebra
# zebra_options="  -A 127.0.0.1 -s 90000000  -M fpm:protobuf"
FPM_PORT=2620

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
                if msg_type == 2:
                    zebra_msg = fpm_pb2.Message()
                    zebra_msg.ParseFromString(payload)
                    print(str(zebra_msg))
        finally:
            conn.close()
    return


if __name__ == "__main__":
    main()

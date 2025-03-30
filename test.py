import psutil
import socket

def get_local_ip():
    interfaces = psutil.net_if_addrs()
    for interface, addresses in interfaces.items():
        for addr in addresses:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                return addr.address  # Returns the first non-localhost IPv4 address

    return "No active network connection found"

local_ip = get_local_ip()
print("Local IP:", local_ip)

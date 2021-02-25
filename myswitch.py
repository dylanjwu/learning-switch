# the only import statement you should ever need
# gives you access to Switchyard classes/functions
from switchyard.lib.userlib import *
import time

BROADCAST_ADDR = 'ff:ff:ff:ff:ff:ff'
EVICTION_POLICY = 'time' # time, freq, or size
MAX_F_TABLE_SIZE = 6
TIMEOUT_SECS = 5
f_table = {}

def evict_least_traffic(net):
    # by application payload bytes (ignoring lower layer headers)
    pass

def evict(net, crit):
    global f_table

    log_info("in evict() function")
    least_addr = list(f_table.keys())[0]
    log_info("{}".format(least_addr))

    if (not(crit=='time' or crit=='freq' or crit=='size')):
        return

    least = f_table[least_addr][crit]
    for addr in f_table:
        x = f_table[addr][crit]
        if x < least:
            least = x
            least_addr = addr
    
    log_info(f"Evicting entry with addr {least_addr} at port {f_table[least_addr]['port']}")
    f_table.__delitem__(least_addr)


def evict_time_out_ports():
    log_info("in evict_time_out_ports() function")
    entries_to_evict = []
    for addr in f_table:
        curr_time = time.time()
        timestamp = f_table[addr]['time']
        #if 30 sec diff between curr_time and mapping's time, evict
        log_info(f"Time difference of: {curr_time-timestamp}")
        if curr_time - timestamp >= TIMEOUT_SECS:
            entries_to_evict.append(addr)
            log_info(f"Evicting entry with addr {addr} at port {f_table[addr]['port']}")
            log_info(f"Time difference of: {curr_time-timestamp}")

    for addr_to_evict in entries_to_evict:
        f_table.__delitem__(addr_to_evict)

def initialize_f_table(net):
    global f_table
    log_info("Hub is starting up with these ports")
    for port in net.ports():
        log_info("{}: ethernet address {}".format(port.name, port.ethaddr))
        log_info(str(port.ethaddr))
        f_table[str(port.ethaddr)] = {'port': port.name, 'time': time.time(), 'freq': 0, 'size': 0}

def print_f_table():
    log_info(f"PRINTING F_TABLE (length of {len(f_table)}):\n")
    for addr in f_table:
        log_info(f"{addr}: {f_table[addr]}")

def broadcast(net, packet, input_port):
    # send packet out all ports except the one from which it arrived
    for port in net.ports():
        if port.name != input_port:
            net.send_packet(port.name, packet)
            

# net: network object; is necessary
def main(net):
    global f_table
    initialize_f_table(net)

    while True:
        try:            
            print_f_table()
            evict_time_out_ports()

            timestamp,input_port,packet = net.recv_packet()
            packet_size = len(packet.to_bytes())

            # Part 1: RECIEVE PACKET
            # drop packet if destination is the switch
            dst_addr = packet[0].dst
            src_addr = packet[0].src
            if dst_addr in [port.ethaddr for port in net.ports()]:
                continue
                 
            if str(src_addr) not in f_table.keys():
                if len(f_table) >= MAX_F_TABLE_SIZE:
                    evict(net, EVICTION_POLICY)

                f_table[str(src_addr)] = {'port': input_port, 
                                          'time': time.time(), 
                                          'freq': 1, 
                                          'size': packet_size}
            else:
                f_table[str(src_addr)]['time'] = time.time()
                f_table[str(src_addr)]['freq'] += 1
                f_table[str(src_addr)]['size'] += packet_size


        except Shutdown:
            log_info("Got shutdown signal; exiting")
            break
        except NoPackets:
            log_info("No packets were available")
            continue

        # if we arrive here, we must have received a packet
        log_info("Received {} on {}".format(packet, input_port))
        
        # Part 2: SEND PACKET
        # broadcast packet if destination address is broadcast address
        if str(packet[0].dst) == BROADCAST_ADDR:
            broadcast(net, packet, input_port)
        
        else:
            # check if port has same address as the packet's dst address
            already_sent = False
            for addr in f_table:
                if addr == str(dst_addr):
                    net.send_packet(f_table[addr]['port'], packet)
                    already_sent = True
            if not already_sent:
                broadcast(net, packet, input_port)
        # time.sleep(10)

    net.shutdown()

   
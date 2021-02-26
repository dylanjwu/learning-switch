# the only import statement you should ever need
# gives you access to Switchyard classes/functions
from switchyard.lib.userlib import *
import time

BROADCAST_ADDR = 'ff:ff:ff:ff:ff:ff'
MAX_F_TABLE_SIZE = 6
TIMEOUT_SECS = 20

f_table = {}

#evicts the oldest item in f_table if we are out of space. If there are two items that arrived at the same time, the item that is removed is randomly selected.
def evict(net):
    least_addr = list(f_table.keys())[0]
    least = f_table[least_addr]['time']
    
    for addr in f_table:
        x = f_table[addr]['time']
        if x < least:
            least = x
            least_addr = addr
    elif x==least: #randomly selects which item to remove if they have the same time
        random_select = random.choice([0,1])
        if random_select==0:
        least = x
    log_info(f"Evicting entry with addr {least_addr} on port {f_table[least_addr]['port']}")
    f_table.__delitem__(least_addr)


# Removes the entries in f_table that have "timed-out" or have been in f_table for longer than TIMEOUT_SECS
def evict_time_out_ports():
    entries_to_evict = []
    for addr in f_table:
        curr_time = time.time()
        timestamp = f_table[addr]['time']
        if curr_time - timestamp >= TIMEOUT_SECS:
            entries_to_evict.append(addr)
            log_info(f"Evicting entry with addr {addr} at port {f_table[addr]['port']}")
            log_info(f"Time difference of: {curr_time-timestamp}")
   
    for addr_to_evict in entries_to_evict:
        f_table.__delitem__(addr_to_evict)


# populates the array "f_table" with all ports
def initialize_f_table(net):
    log_info("Hub is starting up with these ports")
    for port in net.ports():
        log_info("{}: ethernet address {}".format(port.name, port.ethaddr))
        log_info(str(port.ethaddr))
        f_table[str(port.ethaddr)] = {'port': port.name, 'time': time.time()}

#prints the current state of f_table
def print_f_table():
    log_info(f"PRINTING F_TABLE (length of {len(f_table)}):\n")
    for addr in f_table:
        log_info(f"{addr}: {f_table[addr]}")


# send packet out all ports except the one from which it arrived
def broadcast(net, packet, input_port):
    for port in net.ports():
        if port.name != input_port:
            net.send_packet(port.name, packet)
            
            
# net: network object; is necessary
def main(net):
    initialize_f_table(net)

    while True:
        try:            
            print_f_table()
            evict_time_out_ports()

            timestamp,input_port,packet = net.recv_packet()

            # Part 1: RECIEVE PACKET
            # drop packet if destination is the switch
            dst_addr = packet[0].dst
            src_addr = packet[0].src
            if dst_addr in [port.ethaddr for port in net.ports()]:
                continue
                 
            if str(src_addr) not in f_table.keys():
                if len(f_table) >= MAX_F_TABLE_SIZE:
                    evict(net)
                f_table[str(src_addr)] = {'port': input_port, 'time': time.time()}
            else:
                f_table[str(src_addr)]['time'] = time.time()


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

   

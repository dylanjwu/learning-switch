# the only import statement you should ever need
# gives you access to Switchyard classes/functions
from switchyard.lib.userlib import *
import time

f_table = {}

def find_first_open_port():
    for port in f_table:
        if f_table[port]['addr'] == None:
            return port
    return None

def find_port_to_evict(net):
    oldest_port = net.ports()[0]
    oldest_time = f_table[oldest_port]['time']
    for port in f_table:
        timestamp = f_table[port]['time']
        if timestamp != None and timestamp < oldest_time:
            oldest_time = timestamp
            oldest_port = port
    return oldest_port

def evict_time_out_ports():
    for port in f_table:
        curr_time = time.time()
        timestamp = f_table[port]['time']
        #if 30 sec diff between curr_time and mapping's time, evict
        print("PORT: " + port)
        if timestamp != None and curr_time - timestamp >= 30:
            f_table[port] = {'addr': None, 'time': None}

def initialize_f_table(net):
    log_info("Hub is starting up with these ports")
    for port in net.ports():
        log_info("{}: ethernet address {}".format(port.name, port.ethaddr))
        f_table[port.name] = {'addr': None, 'time': None}
        print(port)
        print(f_table[port.name])

# net: network object; is necessary
def main(net):

    initialize_f_table(net)

    while True:
        # evict_time_out_ports()
        try:
            # net.recv_packet(timeout=None) returns named 3-tuple
            # unless timeout >= 0, method 'blocks' until packet is received
            # raises shutdown exception if Switchyard framework is shut down
            # raises NoPackets exception if no packets received before timeout value
            timestamp,input_port,packet = net.recv_packet()
            if packet[0].dst in [port.ethaddr for port in net.ports()]:
                continue
            open_port = find_first_open_port()
            if f_table[input_port]['addr'] == None:
                curr_port = input_port
            if open_port != None:
                curr_port = open_port
            else:
                curr_port = find_port_to_evict(net) 

            f_table[curr_port] = {'addr': packet[0].src, 'time': timestamp}
           
        except Shutdown:
            log_info("Got shutdown signal; exiting")
            break
        except NoPackets:
            log_info("No packets were available")
            continue

        # if we arrive here, we must have received a packet
        log_info("Received {} on {}".format(packet, input_port))
        
        # send_packet(output_port, packet) returns None, 
        # or ValueError exception if output_port or packet is invalid
        # e.g., something other than a packet is passed as 2nd parameter

        # if ethernet address in received frame is the same as an ethernet address
        # assigned to one of the ports in the hub
        # then the frame should be ignored

        # check if port has same address as the packet's dst address
        already_sent = False
        for port in f_table:
            if port != input_port and f_table[port]['addr'] == packet[0].dst:
                net.send_packet(port, packet)
                already_sent = True


        # send packet out all ports accept the one from which it arrived
        if not already_sent:
            for port in net.ports():
                if port.name != input_port:
                    net.send_packet(port.name, packet)

    # should always be the last thing to do
    net.shutdown()

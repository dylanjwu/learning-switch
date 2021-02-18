# the only import statement you should ever need
# gives you access to Switchyard classes/functions
from switchyard.lib.userlib import *
import time

f_table = {}

def find_first_open_port():
    for port in range(len(f_table)):
        if f_table[port]['addr'] == None:
            return port
    return -1

def find_port_to_evict():
    oldest_time = f_table[0]['time']
    oldest_port = 0
    for port in range(len(f_table)):
        if f_table[port]['time'] < oldest_time:
            oldest_time = f_table[port]['time']
            oldest_port = port
    return oldest_port


# net: network object; is necessary
def main(net):

    log_info("Hub is starting up with these ports")
    for port in net.ports():
        log_info("{}: ethernet address {}".format(port.name, port.ethaddr))
        f_table[port] = {'addr': None, 'time': None}

    while True:
        try:
            # net.recv_packet(timeout=None) returns named 3-tuple
            # unless timeout >= 0, method 'blocks' until packet is received
            # raises shutdown exception if Switchyard framework is shut down
            # raises NoPackets exception if no packets received before timeout value
            timestamp,input_port,packet = net.recv_packet()
            if f_table[input_port]['addr'] == None:
                f_table[input_port]['addr'] = packet.src
                f_table[input_port]['time'] = timestamp

            open_port = find_first_open_port()
            if open_port != -1:
                f_table[open_port]['addr'] = packet.src
                f_table[open_port]['time'] = timestamp

            else:
                to_evict = find_port_to_evict() 
                f_table[to_evict]['addr'] = packet.src
                f_table[to_evict]['time'] = timestamp

            """
            alternatively:
            recvdata = net.recv_packet()
            print("At {}, received {} on {}".format(
                recvdata.timestap, recvdata.packet, recvdata.input_port))
            """
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
            if port != input_port and port['addr'] == packet[0].dst:
                net.send_packet(port, packet)
                already_sent = True


        # send packet out all ports accept the one from which it arrived
        if not already_sent:
            for port in net.ports():
                if port.name != input_port:
                    net.send_packet(port.name, packet)

    # should always be the last thing to do
    net.shutdown()





# TODO: Implement learning bridge algorithm 
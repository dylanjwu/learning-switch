# the only import statement you should ever need
# gives you access to Switchyard classes/functions
from switchyard.lib.userlib import *


# net: network object; is necessary
def main(net):
    log_info("Hub is starting up with these ports")
    for port in net.ports():
        log_info("{}: ethernet address {}".format(port.name, port.ethaddr))

    while True:
        try:
            # net.recv_packet(timeout=None) returns named 3-tuple
            # unless timeout >= 0, method 'blocks' until packet is received
            # raises shutdown exception if Switchyard framework is shut down
            # raises NoPackets exception if no packets received before timeout value
            timestamp,input_port,packet = net.recv_packet()
            if packet[0].dst in [p.ethaddr for p in net.ports()]:
                continue

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


        # send packet out all ports accept the one from which it arrived
        for port in net.ports():
            if port.name != input_port:
                net.send_packet(port.name, packet)

    # should always be the last thing to do
    net.shutdown()


# TODO: Implement learning bridge algorithm 
# -*- coding: utf-8 -*-

"""
Copyright 2021 Maen Artimy

Permission is hereby granted, free of charge, to any person obtaining a 
copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
"""

import networkx.drawing as nxd
import logging
from netaddr import EUI
import sys
import argparse


"""
This application simulates the original Spanning Tree Algorithem.
The code produces accurate end results after the algoirthm converges;
however, timers and delays are not considered.

"""


class BPDU(object):
    def __init__(self, root, cost, id, port):
        self.root = root
        self.cost = cost
        self.id = id
        self.port = port

    def getBest(self, other):
        """
        Given two BPDUs C1 and C2, the best received BPDU is determined as
        follows:
        1. Lowest root bridge id: C1 is better than C2 if rootID in C1 is 
        lower than the rootID in C2
        2. Lowest root path cost: C1 is better than C2 if cost in C1 is lower 
        than the cost in C2
        3. Lowest sender bridge id: C1 is better than C2 if sender bridge ID 
        in C1 is lower than the sender bridge ID in C2
        4. Lowest sender port id: C1 is better than C2 if sender bridge port 
        in C1 is lower than the sender bridge port in C2
        """

        if not other:
            return self
        elif self.root < other.root:
            return self
        elif self.root == other.root and self.cost < other.cost:
            return self
        elif self.root == other.root and self.cost == other.cost and self.id < other.id:
            return self
        elif self.root == other.root and self.cost == other.cost and self.id == other.id and self.port < other.port:
            return self
        elif self.root == other.root and self.cost == other.cost and self.id == other.id and self.port == other.port:
            return self

        return other

    def __str__(self):
        # return f"\033[91m[{self.root}, {self.cost}, {self.id}, {self.port}]\033[0m"
        return f"[{hex(self.root)}, {self.cost}, {hex(self.id)}, {self.port}]"


class Port(object):
    """
    A switch port.
    """

    ROLE_ROOT = "Root Port"
    ROLE_UNDESG = "Undesignated"
    ROLE_DESG = "Designated"

    ST_FORWARD = "Forwarding"
    ST_BLOCKED = "Blocked"

    ROLE_STATUS_MAP = {
        ROLE_ROOT: ST_FORWARD,
        ROLE_DESG: ST_FORWARD,
        ROLE_UNDESG: ST_BLOCKED
    }

    def __init__(self, num, cost):
        self.num = num
        self.cost = cost
        self.remote_port = None
        self.resetSTP()

    def resetSTP(self):
        self.best_bpdu = None
        self.role = Port.ROLE_UNDESG
        self.status = Port.ST_BLOCKED
        self.cost_to_root = None

    def setRemote(self, remote):
        self.remote_port = remote

    def sendBPDU(self, m):
        # The best transmitted or received BPDU is saved
        self.best_bpdu = self.best_bpdu.getBest(m) if self.best_bpdu else m
        self.remote_port.receiveBPDU(m)

    def receiveBPDU(self, m):
        # The best transmitted or received BPDU is saved
        self.best_bpdu = self.best_bpdu.getBest(m) if self.best_bpdu else m

    def setRole(self, role):
        # Update switch role and status
        self.role = role
        self.status = self.ROLE_STATUS_MAP[role]


class Bridge(object):
    """
    A Switch.
    """

    def __init__(self, label, id):
        self.label = label
        self.id = id
        self.ports = []

    def boot(self):
        """
        When a bridge is booted up, it assumes it is the root and transmits 
        this BPDU on each port: <Bridge ID>.<0>.<Bridge ID><Port>
        """

        # I'm root
        self.best_bpdu = BPDU(self.id, 0, self.id, 0)
        self.root = True

        # Reset STP data in all ports
        for p in self.ports:
            p.resetSTP()

        logging.debug(f"Bridge {hex(self.id)} boots.")

    def processBPDUs(self):
        """
        The bridge creates a new BPDU that based on the best received BPDU: 
        <Root ID>.<cost to root + port cost>.<Bridge ID><Port>.
        If the bridge's new BPDU is better than the BPDU it received on a port, 
        it would transmit the new BPDU, otherwise it will no longer transmit 
        BPDUs on that port. This port will be either root port or blocked port.
        Ports that are not a root port or blocked port (BP) are designated
        ports (DP). There must be only one DP per LAN segment. 
        The bridge will continue sending BPDUs on these ports and forward data 
        packets.
        """

        # best = []
        # for p in self.ports:
        #     if p.best_bpdu:
        #         best.append(BPDU(p.best_bpdu.root, p.best_bpdu.cost + p.cost, self.id, p.num))

        # Creat a BPDU for each port based on the best BPDU from the port by
        # adding the port cost and the egress port number.
        best = [BPDU(p.best_bpdu.root, p.best_bpdu.cost + p.cost,
                     self.id, p.num) for p in self.ports if p.best_bpdu]

        # Select the best BPDU from all ports
        best_bpdu = BPDU(self.id, 0, self.id, 0)
        root_port = None
        for b in best:
            if b.getBest(best_bpdu) == b:
                best_bpdu = b
                root_port = b.port
        logging.debug(
            f"Bridge {hex(self.id)} best BPDU is {best_bpdu} via port {root_port}.")

        self.root = best_bpdu.root == self.id

        if self.root:
            logging.debug(f"Bridge {hex(self.id)} is Root bridge.")
            # to_send = BPDU(self.id, 0, self.id, 0)

            for p in self.ports:
                best_bpdu.port = p.num
                p.sendBPDU(best_bpdu)
                p.setRole(Port.ROLE_DESG)
                logging.debug(
                    f"Bridge {hex(self.id)} sends BPDU {best_bpdu} via port {p.num}.")
        else:
            for p in self.ports:
                # If this bridge BPDU is better than the BPDU received from the
                # port, send the BPDU, otherwise stop
                if best_bpdu.getBest(p.best_bpdu) == best_bpdu:
                    # # To prevent self-loop
                    # if best_bpdu.id == self.id and best_bpdu.port < p.num:
                    #     print(f"Bridge {hex(self.id)} not sending BPDU {best_bpdu} to port {p.num}.")
                    #     p.setRole(Port.ROLE_UNDESG)
                    #     continue    
                    p.sendBPDU(best_bpdu)
                    p.setRole(Port.ROLE_DESG)
                    p.cost_to_root = None
                    logging.debug(
                        f"Bridge {hex(self.id)} sends BPDU {best_bpdu} via port {p.num}.")
                elif p.num == root_port:
                    p.cost_to_root = best_bpdu.cost
                    p.setRole(Port.ROLE_ROOT)
                else:
                    p.cost_to_root = None
                    p.setRole(Port.ROLE_UNDESG)

    def reportSTP(self):
        """
        Report bridghe and port status.
        """

        root_id = "This bridge is Root" if self.root else f"Root ID: {hex(self.best_bpdu.root)}"
        print(f"Bridge: {self.label}:")
        print(f"ID: {hex(self.id)}. {root_id}.")

        row_format = "{:<8} {:<15} {:<15} {:<8} {:<15}"
        print("—" * 65)
        print(row_format.format('Port', 'Role', 'Status', 'Cost', 'Cost-to-Root'))
        print("—" * 65)
        for p in sorted(self.ports, key=lambda x: x.num):
            ctr = p.cost_to_root if p.cost_to_root else '—'
            print(row_format.format(p.num, p.role, p.status, p.cost, ctr))
        print()


class Network(object):

    COST_MAP = {
        10: 100,
        100: 19,
        1000: 4,
        10000: 2
    }

    def __init__(self):
        self.bridges = {}

    def getBridge(self, label, id):
        if id in self.bridges:
            return self.bridges[id]
        br = Bridge(label, id)
        self.bridges[id] = br
        return br

    def getAllBridges(self):
        return self.bridges.values()

    def connect(self, br1, port1, br2, port2, speed):
        local = Port(port1, self.COST_MAP[speed])
        remote = Port(port2, self.COST_MAP[speed])
        local.setRemote(remote)
        remote.setRemote(local)
        br1.ports.append(local)
        br2.ports.append(remote)

    def __str__(self):
        return ",".join(map(str, self.bridges.keys()))


# def buildNetworkFromYAML():
#     # Open the file and load the file
#     with open('stp_network.yaml') as f:
#         data = yaml.load(f, Loader=SafeLoader)
#         logging.debug(data)

#     # Build the network
#     net = Network()

#     for edge in data['edges']:
#         src = edge['src']
#         dst = edge['dst']

#         g1 = net.getBridge(src['id'])
#         g2 = net.getBridge(dst['id'])
#         net.connect(g1, src['port'], g2, dst['port'], edge['spd'])

#     return net


def buildNetworkFromDOT(file):
    # Read network topology written in DOT format

    MG = None

    try:
        MG = nxd.nx_pydot.read_dot(file)
    except FileNotFoundError:
        print('File Not Found!')
        sys.exit(0)

    nodes = {}
    edges_data = MG.edges.data()
    nodes_data = MG.nodes.data()

    net = Network()

    for label, attr in nodes_data:
        # Concatenating the MAC and Bridge Priority to get Bridge ID
        mac = attr.get('mac', 'ff:ff:ff:ff:ff:ff').replace('"', '')
        pri = attr.get('priority', '32768')
        id = int(pri) * 2**48 + int(EUI(mac))
        nodes[label] = id

    for s, d, attr in edges_data:
        n = s.split(':')
        m = d.split(':')

        src_node = n[0]
        src_port = int(n[1])
        dst_node = m[0]
        dst_port = int(m[1])

        g1 = net.getBridge(src_node, nodes[src_node])
        g2 = net.getBridge(dst_node, nodes[dst_node])
        speed = int(attr['speed'])
        net.connect(g1, src_port, g2, dst_port, speed)
    return net


STEPS = 5
LOG_FILE = 'stp_simulator.log'


def setArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", help="Input file")
    parser.add_argument("-s", "--steps", help="Number of simulation steps")
    parser.add_argument("-l", "--loglevel", help="Set the logging level")
    args = parser.parse_args()

    if args.steps:
        steps = int(args.steps)
    else:
        steps = STEPS
    if args.loglevel:
        numeric_level = getattr(logging, args.loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            print(f'Invalid log level: {args.loglevel}')
            sys.exit(0)
        logging.basicConfig(filename=LOG_FILE,
                            filemode='w', level=numeric_level)
    else:
        logging.basicConfig(filename=LOG_FILE,
                            filemode='w', level=logging.INFO)
    if args.infile:
        logging.info(f"Reading file: {args.infile}")
    else:
        print('usage: stp_simulator.py -i <inputfile>')
        sys.exit(0)

    return args.infile, steps


if __name__ == "__main__":

    infile, steps = setArguments()

    # Build the network
    net = buildNetworkFromDOT(infile)

    logging.info(f"Simulation starting.")

    # Boot switches
    for br in net.getAllBridges():
        br.boot()

    # Start STP
    for i in range(steps):
        logging.debug(f"Entering Step: {i}")

        for br in net.getAllBridges():
            br.processBPDUs()

    logging.info(f"Simulation completed.")

    # Print results
    for br in net.getAllBridges():
        br.reportSTP()

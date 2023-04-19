#! /usr/bin/python2.7

from __future__ import print_function

# Doing * imports is bad :'(
from core.generate_topo import *
from core.generate_xp import *

import core.core as core
# import numpy as np
import os

REMOTE_SERVER_RUNNER_HOSTNAME = ["mininet@192.168.122.77"]
REMOTE_SERVER_RUNNER_PORT = ["22"]


def getPostProcessingList(**kwargs):
    toReturn = []
    topoBasename = os.path.basename(kwargs["topoAbsPath"])
    toReturn.append(("client.pcap",
                      "_".join([str(x) for x in [kwargs["testDirectory"], kwargs["xp"], kwargs["protocol"], kwargs["multipath"],
                                                 topoBasename, "client.pcap"]])))
    toReturn.append(("server.pcap",
                      "_".join([str(x) for x in [kwargs["testDirectory"], kwargs["xp"], kwargs["protocol"], kwargs["multipath"],
                                                 topoBasename, "server.pcap"]])))
    toReturn.append(("command.log", "command.log"))
    toReturn.append(("ping.log", "ping.log"))
    if kwargs["xp"] == HTTPS:
        toReturn.append(("https_client.log", "https_client.log"))
        toReturn.append(("https_server.log", "https_server.log"))
    else:
        toReturn.append(("quic_client.log", "quic_client.log"))
        toReturn.append(("quic_server.log", "quic_server.log"))

    toReturn.append(("netstat_client_before", "netstat_client_before"))
    toReturn.append(("netstat_server_before", "netstat_server_before"))
    toReturn.append(("netstat_client_after", "netstat_client_after"))
    toReturn.append(("netstat_server_after", "netstat_server_after"))

    return toReturn


def quicTests(topos, protocol="mptcp", tmpfs="/mnt/tmpfs"):
    experienceLauncher = core.ExperienceLauncher(REMOTE_SERVER_RUNNER_HOSTNAME, REMOTE_SERVER_RUNNER_PORT)

    def testsXp(**kwargs):
        def testsMultipath(**kwargs):
            def test(**kwargs):
                xpDict = {
                    XP_TYPE: kwargs["xp"],
                    SCHEDULER_CLIENT: "default",
                    SCHEDULER_SERVER: "default",
                    CC: "olia" if kwargs["multipath"] == 1 else "cubic",
                    CLIENT_PCAP: "yes",
                    SERVER_PCAP: "yes",
                    HTTPS_FILE: "random",
                    HTTPS_RANDOM_SIZE: "20000",
                    QUIC_MULTIPATH: kwargs["multipath"],
                    RMEM: (10240, 87380, 16777216),
                }
                if int(kwargs["multipath"]) == 0:
                    kwargs["protocol"] = "tcp"

                kwargs["postProcessing"] = getPostProcessingList(**kwargs)
                core.experiment(experienceLauncher, xpDict, **kwargs)

            # core.experimentFor("multipath", [0, 1], test, **kwargs)
            core.experimentFor("multipath", [1], test, **kwargs)

        # core.experimentFor("xp", [HTTPS, QUIC], testsMultipath, **kwargs)
        core.experimentFor("xp", [QUIC], testsMultipath, **kwargs)

    core.experimentTopos(topos, "https_quic", protocol, tmpfs, testsXp)
    experienceLauncher.finish()


def generateExperimentalDesignRandomTopos(nbMptcpTopos=10, pathsPerTopo=2, bandwidth=(0.1, 100), rtt=(0, 400), queuingDelay=(0.0, 2.0), loss=(0.0, 2.5)):
    """ Assume only two paths per MPTCP topology, uniform distribution """
    mptcpTopos = []
    for nbTopo in range(nbMptcpTopos):
        mptcpTopo = {PATHS: [], NETEM: []}
        for nbPath in range(pathsPerTopo):
            # bandwidthPath = "{0:.2f}".format(np.random.uniform(low=bandwidth[0], high=bandwidth[1]))
            # rttPath = "{0:.0f}".format(np.random.uniform(low=rtt[0], high=rtt[1]))
            # delayPath = "{0:.1f}".format(float(rttPath) / 2.0)
            # lossPath = "{0:.2f}".format(np.random.uniform(low=loss[0], high=loss[1]))
            # queuingDelayPath = "{0:.3f}".format(np.random.uniform(low=queuingDelay[0], high=queuingDelay[1]))
            # tcpTopos.append({PATHS: [{BANDWIDTH: bandwidthPath, DELAY: delayPath}], NETEM: [(0, 0, "loss " + str(lossPath) + "%")]})
            # mptcpTopo[PATHS].append({BANDWIDTH: bandwidthPath, DELAY: delayPath, QUEUING_DELAY: queuingDelayPath})
            # mptcpTopo[NETEM].append((nbPath, 0, "loss " + str(lossPath) + "%"))
            pass

        mptcpTopos.append(mptcpTopo)
        reversedMptcpTopoPaths = mptcpTopo[PATHS][::-1]
        reversedMptcpTopoNetem = []
        nbPath = 0
        for netem in mptcpTopo[NETEM][::-1]:
            reversedMptcpTopoNetem.append((nbPath, netem[1], netem[2]))
            nbPath += 1

        reversedMptcpTopo = {PATHS: reversedMptcpTopoPaths, NETEM: reversedMptcpTopoNetem}
        mptcpTopos.append(reversedMptcpTopo)

    return mptcpTopos


def launchTests(times=5):
    """ Notice that the loss must occur at time + 2 sec since the minitopo test waits for 2 seconds between launching the server and the client """
    # mptcpTopos = generateExperimentalDesignRandomTopos(nbMptcpTopos=200)
    # logging = open("topos_with_loss.log", 'w')
    # print(mptcpTopos, file=logging)
    # logging.close()

    mptcpTopos = 	[
		{'paths': [{'queuingDelay': '0.010', 'bandwidth': '11.258', 'delay': '5.061', 'jitter': '0'},{'queuingDelay': '0.023', 'bandwidth': '14.750', 'delay': '83.044', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '8.929', 'delay': '2.842', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '8.791', 'delay': '82.462', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.013', 'bandwidth': '13.101', 'delay': '2.873', 'jitter': '0'},{'queuingDelay': '0.021', 'bandwidth': '5.514', 'delay': '58.431', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '9.292', 'delay': '5.093', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '5.561', 'delay': '33.705', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.004', 'bandwidth': '9.462', 'delay': '6.929', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '6.165', 'delay': '51.372', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.004', 'bandwidth': '6.735', 'delay': '4.515', 'jitter': '0'},{'queuingDelay': '0.025', 'bandwidth': '11.560', 'delay': '35.027', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.009', 'bandwidth': '10.590', 'delay': '3.297', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '13.955', 'delay': '19.145', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.008', 'bandwidth': '6.029', 'delay': '2.753', 'jitter': '0'},{'queuingDelay': '0.011', 'bandwidth': '19.605', 'delay': '17.292', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.022', 'bandwidth': '7.006', 'delay': '4.106', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '19.509', 'delay': '28.979', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.019', 'bandwidth': '7.625', 'delay': '7.717', 'jitter': '0'},{'queuingDelay': '0.021', 'bandwidth': '17.066', 'delay': '25.033', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.006', 'bandwidth': '10.773', 'delay': '7.346', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '16.190', 'delay': '38.689', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.006', 'bandwidth': '13.880', 'delay': '9.538', 'jitter': '0'},{'queuingDelay': '0.021', 'bandwidth': '15.846', 'delay': '74.535', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '16.458', 'delay': '7.029', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '19.263', 'delay': '63.779', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.018', 'bandwidth': '15.058', 'delay': '6.084', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '19.611', 'delay': '67.908', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '18.536', 'delay': '8.434', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '18.778', 'delay': '64.494', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.025', 'bandwidth': '19.099', 'delay': '9.230', 'jitter': '0'},{'queuingDelay': '0.018', 'bandwidth': '15.284', 'delay': '74.703', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.017', 'bandwidth': '18.247', 'delay': '8.652', 'jitter': '0'},{'queuingDelay': '0.006', 'bandwidth': '16.839', 'delay': '88.282', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.017', 'bandwidth': '13.231', 'delay': '8.931', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '15.794', 'delay': '56.938', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.008', 'bandwidth': '9.636', 'delay': '5.954', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '15.168', 'delay': '59.131', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '15.157', 'delay': '6.426', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '10.721', 'delay': '56.157', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '19.593', 'delay': '7.967', 'jitter': '0'},{'queuingDelay': '0.006', 'bandwidth': '14.041', 'delay': '28.717', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '16.512', 'delay': '9.796', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '18.440', 'delay': '13.868', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '18.533', 'delay': '8.399', 'jitter': '0'},{'queuingDelay': '0.021', 'bandwidth': '14.189', 'delay': '39.986', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '16.538', 'delay': '9.622', 'jitter': '0'},{'queuingDelay': '0.021', 'bandwidth': '7.242', 'delay': '51.347', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '14.560', 'delay': '7.998', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '8.748', 'delay': '13.488', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '13.863', 'delay': '4.407', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '8.957', 'delay': '22.083', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '16.439', 'delay': '2.275', 'jitter': '0'},{'queuingDelay': '0.019', 'bandwidth': '14.606', 'delay': '28.975', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.010', 'bandwidth': '19.308', 'delay': '3.854', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '16.212', 'delay': '33.599', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.020', 'bandwidth': '14.905', 'delay': '3.647', 'jitter': '0'},{'queuingDelay': '0.020', 'bandwidth': '17.827', 'delay': '29.724', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.021', 'bandwidth': '14.506', 'delay': '5.372', 'jitter': '0'},{'queuingDelay': '0.026', 'bandwidth': '13.141', 'delay': '57.852', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.018', 'bandwidth': '17.294', 'delay': '5.452', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '8.364', 'delay': '51.377', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '16.244', 'delay': '4.566', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '12.089', 'delay': '31.763', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '17.002', 'delay': '1.833', 'jitter': '0'},{'queuingDelay': '0.004', 'bandwidth': '9.094', 'delay': '21.550', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.023', 'bandwidth': '11.627', 'delay': '1.607', 'jitter': '0'},{'queuingDelay': '0.012', 'bandwidth': '5.635', 'delay': '34.467', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.023', 'bandwidth': '13.168', 'delay': '2.126', 'jitter': '0'},{'queuingDelay': '0.006', 'bandwidth': '7.124', 'delay': '76.064', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.025', 'bandwidth': '5.916', 'delay': '2.450', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '5.819', 'delay': '78.003', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.021', 'bandwidth': '5.825', 'delay': '1.445', 'jitter': '0'},{'queuingDelay': '0.015', 'bandwidth': '9.258', 'delay': '80.977', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '8.428', 'delay': '4.798', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '12.372', 'delay': '85.098', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.008', 'bandwidth': '6.314', 'delay': '2.464', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '14.910', 'delay': '66.684', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.009', 'bandwidth': '6.472', 'delay': '1.461', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '19.897', 'delay': '97.789', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '9.780', 'delay': '3.849', 'jitter': '0'},{'queuingDelay': '0.005', 'bandwidth': '16.764', 'delay': '94.681', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.009', 'bandwidth': '13.959', 'delay': '1.470', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '18.416', 'delay': '80.374', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '19.053', 'delay': '1.490', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '18.758', 'delay': '89.342', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.007', 'bandwidth': '17.096', 'delay': '3.501', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '13.560', 'delay': '68.609', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '18.689', 'delay': '6.293', 'jitter': '0'},{'queuingDelay': '0.017', 'bandwidth': '9.577', 'delay': '93.521', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.010', 'bandwidth': '18.403', 'delay': '3.335', 'jitter': '0'},{'queuingDelay': '0.008', 'bandwidth': '7.436', 'delay': '91.319', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '13.088', 'delay': '3.229', 'jitter': '0'},{'queuingDelay': '0.004', 'bandwidth': '5.342', 'delay': '87.774', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '6.459', 'delay': '4.390', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '8.729', 'delay': '92.991', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.006', 'bandwidth': '6.080', 'delay': '1.412', 'jitter': '0'},{'queuingDelay': '0.010', 'bandwidth': '6.294', 'delay': '68.140', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '6.628', 'delay': '2.979', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '5.851', 'delay': '31.497', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '5.685', 'delay': '1.166', 'jitter': '0'},{'queuingDelay': '0.005', 'bandwidth': '8.439', 'delay': '32.788', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.019', 'bandwidth': '9.593', 'delay': '2.936', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '13.693', 'delay': '43.424', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '7.505', 'delay': '1.698', 'jitter': '0'},{'queuingDelay': '0.007', 'bandwidth': '15.293', 'delay': '65.330', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.019', 'bandwidth': '10.961', 'delay': '1.542', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '16.181', 'delay': '63.125', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.027', 'bandwidth': '13.833', 'delay': '2.061', 'jitter': '0'},{'queuingDelay': '0.007', 'bandwidth': '19.063', 'delay': '78.496', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '17.185', 'delay': '3.844', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '14.007', 'delay': '64.934', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '18.837', 'delay': '3.263', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '12.322', 'delay': '85.434', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.026', 'bandwidth': '19.336', 'delay': '1.595', 'jitter': '0'},{'queuingDelay': '0.026', 'bandwidth': '10.206', 'delay': '66.124', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.025', 'bandwidth': '14.676', 'delay': '3.834', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '9.768', 'delay': '95.972', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.013', 'bandwidth': '12.247', 'delay': '5.770', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '7.619', 'delay': '97.731', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.015', 'bandwidth': '8.639', 'delay': '7.980', 'jitter': '0'},{'queuingDelay': '0.017', 'bandwidth': '6.499', 'delay': '92.658', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.014', 'bandwidth': '6.176', 'delay': '8.830', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '9.999', 'delay': '75.639', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.023', 'bandwidth': '8.926', 'delay': '9.357', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '13.907', 'delay': '98.420', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '11.931', 'delay': '9.121', 'jitter': '0'},{'queuingDelay': '0.018', 'bandwidth': '14.004', 'delay': '84.569', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.026', 'bandwidth': '6.967', 'delay': '7.851', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '15.335', 'delay': '94.701', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '5.131', 'delay': '9.333', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '19.675', 'delay': '60.874', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '5.035', 'delay': '9.800', 'jitter': '0'},{'queuingDelay': '0.018', 'bandwidth': '18.509', 'delay': '66.661', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.007', 'bandwidth': '5.705', 'delay': '7.591', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '17.148', 'delay': '86.032', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '6.191', 'delay': '3.677', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '17.458', 'delay': '99.336', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.015', 'bandwidth': '5.759', 'delay': '3.174', 'jitter': '0'},{'queuingDelay': '0.025', 'bandwidth': '18.386', 'delay': '96.579', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '6.467', 'delay': '4.339', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '18.494', 'delay': '72.621', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.023', 'bandwidth': '5.673', 'delay': '5.546', 'jitter': '0'},{'queuingDelay': '0.025', 'bandwidth': '11.977', 'delay': '56.412', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.023', 'bandwidth': '8.290', 'delay': '1.567', 'jitter': '0'},{'queuingDelay': '0.026', 'bandwidth': '12.442', 'delay': '37.632', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.020', 'bandwidth': '11.462', 'delay': '3.201', 'jitter': '0'},{'queuingDelay': '0.025', 'bandwidth': '7.826', 'delay': '11.464', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '11.990', 'delay': '5.775', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '5.120', 'delay': '32.385', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.017', 'bandwidth': '13.165', 'delay': '8.647', 'jitter': '0'},{'queuingDelay': '0.025', 'bandwidth': '5.058', 'delay': '28.267', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.022', 'bandwidth': '7.965', 'delay': '9.788', 'jitter': '0'},{'queuingDelay': '0.018', 'bandwidth': '8.590', 'delay': '22.001', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.017', 'bandwidth': '9.283', 'delay': '9.599', 'jitter': '0'},{'queuingDelay': '0.005', 'bandwidth': '5.459', 'delay': '24.932', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.018', 'bandwidth': '5.441', 'delay': '9.577', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '7.888', 'delay': '60.654', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.020', 'bandwidth': '11.697', 'delay': '6.928', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '8.161', 'delay': '59.183', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.025', 'bandwidth': '15.301', 'delay': '9.438', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '7.504', 'delay': '36.536', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '16.545', 'delay': '9.221', 'jitter': '0'},{'queuingDelay': '0.020', 'bandwidth': '8.172', 'delay': '64.519', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.019', 'bandwidth': '18.523', 'delay': '9.850', 'jitter': '0'},{'queuingDelay': '0.020', 'bandwidth': '6.859', 'delay': '93.935', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '18.168', 'delay': '6.464', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '5.596', 'delay': '97.928', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '18.599', 'delay': '9.011', 'jitter': '0'},{'queuingDelay': '0.007', 'bandwidth': '5.348', 'delay': '77.005', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.020', 'bandwidth': '14.120', 'delay': '9.830', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '9.039', 'delay': '99.879', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '19.005', 'delay': '9.503', 'jitter': '0'},{'queuingDelay': '0.005', 'bandwidth': '11.999', 'delay': '95.710', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '18.379', 'delay': '9.963', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '19.453', 'delay': '95.763', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '14.397', 'delay': '6.794', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '19.973', 'delay': '68.987', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.027', 'bandwidth': '12.159', 'delay': '9.055', 'jitter': '0'},{'queuingDelay': '0.011', 'bandwidth': '19.700', 'delay': '42.594', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '18.102', 'delay': '8.314', 'jitter': '0'},{'queuingDelay': '0.011', 'bandwidth': '18.665', 'delay': '15.519', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '19.906', 'delay': '8.644', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '12.982', 'delay': '14.423', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.020', 'bandwidth': '16.282', 'delay': '5.411', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '16.580', 'delay': '23.827', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '13.415', 'delay': '1.547', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '18.377', 'delay': '12.270', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.014', 'bandwidth': '18.552', 'delay': '1.446', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '18.374', 'delay': '29.622', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.009', 'bandwidth': '17.784', 'delay': '1.313', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '11.672', 'delay': '45.804', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '15.574', 'delay': '1.565', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '6.125', 'delay': '26.596', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.010', 'bandwidth': '19.380', 'delay': '1.638', 'jitter': '0'},{'queuingDelay': '0.020', 'bandwidth': '5.759', 'delay': '13.147', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.014', 'bandwidth': '18.420', 'delay': '5.646', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '5.062', 'delay': '10.498', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '17.985', 'delay': '6.271', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '9.324', 'delay': '10.410', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.010', 'bandwidth': '16.932', 'delay': '9.985', 'jitter': '0'},{'queuingDelay': '0.005', 'bandwidth': '6.837', 'delay': '28.933', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.007', 'bandwidth': '13.442', 'delay': '9.425', 'jitter': '0'},{'queuingDelay': '0.005', 'bandwidth': '5.703', 'delay': '68.964', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '7.886', 'delay': '9.977', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '6.035', 'delay': '88.353', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '6.004', 'delay': '8.493', 'jitter': '0'},{'queuingDelay': '0.011', 'bandwidth': '7.940', 'delay': '62.734', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '6.174', 'delay': '6.629', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '12.288', 'delay': '30.342', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.010', 'bandwidth': '5.955', 'delay': '9.422', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '16.231', 'delay': '15.289', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '6.295', 'delay': '7.230', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '15.981', 'delay': '14.848', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.027', 'bandwidth': '5.106', 'delay': '5.085', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '9.497', 'delay': '17.550', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '6.528', 'delay': '1.075', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '5.839', 'delay': '23.172', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '5.817', 'delay': '1.819', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '10.244', 'delay': '13.717', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.027', 'bandwidth': '5.884', 'delay': '5.594', 'jitter': '0'},{'queuingDelay': '0.023', 'bandwidth': '9.172', 'delay': '13.556', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '6.503', 'delay': '5.471', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '6.692', 'delay': '50.445', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '7.270', 'delay': '6.250', 'jitter': '0'},{'queuingDelay': '0.023', 'bandwidth': '5.301', 'delay': '87.149', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '5.580', 'delay': '2.185', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '7.196', 'delay': '81.959', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '12.217', 'delay': '1.492', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '6.607', 'delay': '64.156', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '11.809', 'delay': '1.130', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '11.904', 'delay': '94.367', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.027', 'bandwidth': '13.941', 'delay': '1.886', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '16.791', 'delay': '96.551', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.023', 'bandwidth': '19.550', 'delay': '3.671', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '19.439', 'delay': '78.442', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.013', 'bandwidth': '18.476', 'delay': '3.211', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '13.686', 'delay': '81.238', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '17.418', 'delay': '1.750', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '9.755', 'delay': '60.127', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '19.512', 'delay': '1.086', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '17.009', 'delay': '67.658', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '19.817', 'delay': '4.376', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '18.944', 'delay': '95.762', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.009', 'bandwidth': '14.846', 'delay': '1.046', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '19.176', 'delay': '99.527', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.007', 'bandwidth': '12.146', 'delay': '2.629', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '19.911', 'delay': '59.420', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.009', 'bandwidth': '6.976', 'delay': '1.133', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '18.158', 'delay': '30.532', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '10.796', 'delay': '2.088', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '14.563', 'delay': '10.270', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '13.809', 'delay': '5.181', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '19.889', 'delay': '12.773', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '6.006', 'delay': '4.861', 'jitter': '0'},{'queuingDelay': '0.026', 'bandwidth': '19.275', 'delay': '14.802', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '5.226', 'delay': '9.320', 'jitter': '0'},{'queuingDelay': '0.024', 'bandwidth': '19.374', 'delay': '17.606', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '5.671', 'delay': '9.604', 'jitter': '0'},{'queuingDelay': '0.021', 'bandwidth': '11.670', 'delay': '11.754', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '6.464', 'delay': '9.974', 'jitter': '0'},{'queuingDelay': '0.012', 'bandwidth': '5.363', 'delay': '14.085', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '10.597', 'delay': '8.020', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '5.909', 'delay': '28.353', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.006', 'bandwidth': '11.473', 'delay': '4.507', 'jitter': '0'},{'queuingDelay': '0.004', 'bandwidth': '9.987', 'delay': '11.068', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '11.495', 'delay': '6.691', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '16.066', 'delay': '20.067', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '14.161', 'delay': '2.959', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '19.996', 'delay': '20.565', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '11.259', 'delay': '1.269', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '19.129', 'delay': '43.899', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '10.199', 'delay': '1.494', 'jitter': '0'},{'queuingDelay': '0.004', 'bandwidth': '12.833', 'delay': '39.741', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '5.881', 'delay': '1.167', 'jitter': '0'},{'queuingDelay': '0.015', 'bandwidth': '9.862', 'delay': '21.004', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '5.015', 'delay': '1.912', 'jitter': '0'},{'queuingDelay': '0.023', 'bandwidth': '6.280', 'delay': '27.107', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.025', 'bandwidth': '5.552', 'delay': '1.166', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '6.048', 'delay': '18.564', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '6.708', 'delay': '6.475', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '6.755', 'delay': '11.554', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '10.754', 'delay': '9.128', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '6.926', 'delay': '12.273', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.011', 'bandwidth': '12.427', 'delay': '9.797', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '12.351', 'delay': '12.227', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '15.363', 'delay': '8.852', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '14.112', 'delay': '22.551', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '19.817', 'delay': '6.477', 'jitter': '0'},{'queuingDelay': '0.026', 'bandwidth': '18.411', 'delay': '13.919', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '16.456', 'delay': '4.397', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '12.294', 'delay': '11.108', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '11.185', 'delay': '4.454', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '18.035', 'delay': '13.392', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '5.027', 'delay': '1.353', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '17.784', 'delay': '12.863', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '10.990', 'delay': '1.204', 'jitter': '0'},{'queuingDelay': '0.025', 'bandwidth': '19.463', 'delay': '48.084', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '19.378', 'delay': '1.751', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '19.049', 'delay': '30.440', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '19.832', 'delay': '2.639', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '18.781', 'delay': '49.145', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '19.454', 'delay': '1.127', 'jitter': '0'},{'queuingDelay': '0.019', 'bandwidth': '13.517', 'delay': '24.115', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '18.950', 'delay': '1.498', 'jitter': '0'},{'queuingDelay': '0.018', 'bandwidth': '5.791', 'delay': '34.724', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '19.956', 'delay': '3.331', 'jitter': '0'},{'queuingDelay': '0.009', 'bandwidth': '5.283', 'delay': '66.573', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '19.693', 'delay': '5.411', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '6.090', 'delay': '56.739', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '19.870', 'delay': '6.999', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '5.469', 'delay': '89.422', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '18.811', 'delay': '9.571', 'jitter': '0'},{'queuingDelay': '0.004', 'bandwidth': '11.634', 'delay': '93.088', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '19.298', 'delay': '5.605', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '15.485', 'delay': '98.702', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '19.589', 'delay': '4.284', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '17.430', 'delay': '54.869', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '19.496', 'delay': '9.273', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '19.221', 'delay': '59.122', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.004', 'bandwidth': '14.425', 'delay': '9.993', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '18.825', 'delay': '94.272', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.006', 'bandwidth': '8.948', 'delay': '8.683', 'jitter': '0'},{'queuingDelay': '0.010', 'bandwidth': '19.870', 'delay': '95.630', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.003', 'bandwidth': '6.796', 'delay': '8.837', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '13.352', 'delay': '97.321', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '5.746', 'delay': '9.086', 'jitter': '0'},{'queuingDelay': '0.019', 'bandwidth': '13.068', 'delay': '96.957', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '7.837', 'delay': '7.797', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '6.944', 'delay': '97.342', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '11.150', 'delay': '7.124', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '7.591', 'delay': '98.603', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.007', 'bandwidth': '13.825', 'delay': '9.894', 'jitter': '0'},{'queuingDelay': '0.023', 'bandwidth': '5.332', 'delay': '95.785', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.005', 'bandwidth': '19.127', 'delay': '9.072', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '10.197', 'delay': '97.800', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '19.434', 'delay': '9.859', 'jitter': '0'},{'queuingDelay': '0.027', 'bandwidth': '11.388', 'delay': '65.031', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.026', 'bandwidth': '16.700', 'delay': '9.290', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '11.599', 'delay': '97.761', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '14.622', 'delay': '9.511', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '19.491', 'delay': '96.419', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.027', 'bandwidth': '9.856', 'delay': '9.551', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '19.236', 'delay': '59.488', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '6.150', 'delay': '9.793', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '12.983', 'delay': '42.704', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '5.091', 'delay': '9.797', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '19.197', 'delay': '14.462', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '12.749', 'delay': '9.800', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '14.167', 'delay': '12.260', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.015', 'bandwidth': '12.625', 'delay': '9.786', 'jitter': '0'},{'queuingDelay': '0.012', 'bandwidth': '14.145', 'delay': '26.396', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '11.008', 'delay': '9.825', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '12.658', 'delay': '42.224', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '7.115', 'delay': '8.178', 'jitter': '0'},{'queuingDelay': '0.010', 'bandwidth': '18.895', 'delay': '48.475', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.004', 'bandwidth': '5.062', 'delay': '2.910', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '19.157', 'delay': '58.936', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.019', 'bandwidth': '7.259', 'delay': '4.009', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '18.886', 'delay': '74.452', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.025', 'bandwidth': '5.024', 'delay': '2.612', 'jitter': '0'},{'queuingDelay': '0.012', 'bandwidth': '19.083', 'delay': '98.448', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.017', 'bandwidth': '5.236', 'delay': '1.514', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '13.163', 'delay': '97.883', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '11.997', 'delay': '1.902', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '10.344', 'delay': '98.501', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '13.351', 'delay': '1.017', 'jitter': '0'},{'queuingDelay': '0.017', 'bandwidth': '9.350', 'delay': '99.256', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '17.944', 'delay': '1.498', 'jitter': '0'},{'queuingDelay': '0.021', 'bandwidth': '6.386', 'delay': '97.062', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '18.967', 'delay': '2.107', 'jitter': '0'},{'queuingDelay': '0.025', 'bandwidth': '5.425', 'delay': '92.570', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.007', 'bandwidth': '18.836', 'delay': '5.452', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '5.072', 'delay': '78.024', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.011', 'bandwidth': '19.967', 'delay': '6.387', 'jitter': '0'},{'queuingDelay': '0.028', 'bandwidth': '5.529', 'delay': '32.500', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '19.927', 'delay': '5.289', 'jitter': '0'},{'queuingDelay': '0.017', 'bandwidth': '7.132', 'delay': '48.890', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '19.937', 'delay': '5.174', 'jitter': '0'},{'queuingDelay': '0.002', 'bandwidth': '5.314', 'delay': '37.853', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.014', 'bandwidth': '19.500', 'delay': '6.089', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '14.186', 'delay': '16.042', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.012', 'bandwidth': '17.871', 'delay': '7.239', 'jitter': '0'},{'queuingDelay': '0.023', 'bandwidth': '19.837', 'delay': '15.235', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.002', 'bandwidth': '19.298', 'delay': '5.150', 'jitter': '0'},{'queuingDelay': '0.014', 'bandwidth': '19.848', 'delay': '12.360', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.011', 'bandwidth': '19.486', 'delay': '8.357', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '19.565', 'delay': '23.930', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '10.787', 'delay': '6.601', 'jitter': '0'},{'queuingDelay': '0.006', 'bandwidth': '19.867', 'delay': '10.656', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '9.311', 'delay': '5.999', 'jitter': '0'},{'queuingDelay': '0.012', 'bandwidth': '14.318', 'delay': '45.499', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '9.888', 'delay': '9.926', 'jitter': '0'},{'queuingDelay': '0.005', 'bandwidth': '11.972', 'delay': '56.717', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '5.382', 'delay': '9.601', 'jitter': '0'},{'queuingDelay': '0.015', 'bandwidth': '8.999', 'delay': '71.961', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '5.600', 'delay': '7.231', 'jitter': '0'},{'queuingDelay': '0.006', 'bandwidth': '6.104', 'delay': '95.625', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '10.629', 'delay': '5.788', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '11.213', 'delay': '92.745', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.022', 'bandwidth': '19.332', 'delay': '5.503', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '9.976', 'delay': '98.020', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.014', 'bandwidth': '19.805', 'delay': '2.981', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '14.852', 'delay': '84.459', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.000', 'bandwidth': '18.329', 'delay': '1.168', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '11.769', 'delay': '94.659', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '19.781', 'delay': '1.075', 'jitter': '0'},{'queuingDelay': '0.016', 'bandwidth': '19.825', 'delay': '99.436', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '18.304', 'delay': '6.061', 'jitter': '0'},{'queuingDelay': '0.013', 'bandwidth': '19.819', 'delay': '93.576', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.020', 'bandwidth': '10.557', 'delay': '8.222', 'jitter': '0'},{'queuingDelay': '0.019', 'bandwidth': '19.659', 'delay': '98.809', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.016', 'bandwidth': '5.055', 'delay': '9.766', 'jitter': '0'},{'queuingDelay': '0.001', 'bandwidth': '18.416', 'delay': '94.843', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.007', 'bandwidth': '19.526', 'delay': '9.797', 'jitter': '0'},{'queuingDelay': '0.018', 'bandwidth': '19.576', 'delay': '97.118', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.025', 'bandwidth': '19.945', 'delay': '6.631', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '8.692', 'delay': '45.930', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.028', 'bandwidth': '18.981', 'delay': '8.894', 'jitter': '0'},{'queuingDelay': '0.023', 'bandwidth': '7.647', 'delay': '10.038', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.029', 'bandwidth': '19.063', 'delay': '5.809', 'jitter': '0'},{'queuingDelay': '0.006', 'bandwidth': '5.450', 'delay': '13.842', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.030', 'bandwidth': '12.481', 'delay': '7.581', 'jitter': '0'},{'queuingDelay': '0.000', 'bandwidth': '10.952', 'delay': '14.717', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.024', 'bandwidth': '5.235', 'delay': '1.492', 'jitter': '0'},{'queuingDelay': '0.003', 'bandwidth': '15.666', 'delay': '10.205', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.001', 'bandwidth': '9.016', 'delay': '1.134', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '6.559', 'delay': '14.165', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.015', 'bandwidth': '5.145', 'delay': '4.468', 'jitter': '0'},{'queuingDelay': '0.030', 'bandwidth': '10.830', 'delay': '98.872', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
		{'paths': [{'queuingDelay': '0.026', 'bandwidth': '8.378', 'delay': '9.594', 'jitter': '0'},{'queuingDelay': '0.029', 'bandwidth': '5.391', 'delay': '55.402', 'jitter': '0'}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
	]
# {'paths': [{'queuingDelay': '0.048', 'bandwidth': '5.00', 'delay': '10.0', 'jitter': '0'}, {'queuingDelay': '0.063', 'bandwidth': '3.00', 'delay': '40', 'jitter': '0'}], 'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]}
#{'paths': [{'queuingDelay': '0.01', 'bandwidth': '10.00', 'delay': '10.0', 'jitter': '0'}, {'queuingDelay': '0.01', 'bandwidth': '10.00', 'delay': '10', 'jitter': '0'}], 'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},


    for i in range(times):
        quicTests(mptcpTopos)

launchTests(times=1)

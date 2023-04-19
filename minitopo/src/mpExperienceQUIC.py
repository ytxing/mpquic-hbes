from mpExperience import MpExperience
from mpParamXp import MpParamXp
from collections import defaultdict
import os
import time
import signal

fileparam = defaultdict(list)
# name,size(0.1KB),priority,dependency
#prefetch

fileparam["randompre"].extend([500, 1, 0])
#goole

# fileparam["randomhigh15"].extend([15, 220, 0])
# fileparam["randomhighest361"].extend([361, 255, 0])
# fileparam["randomlow22240"].extend([2224, 147, 0])
# fileparam["randomhigh59"].extend([59, 220, 0])
# fileparam["randomhigh646"].extend([646, 220, 0])
# fileparam["randomlow5"].extend([5, 147, 0])
# fileparam["randomlow6"].extend([6, 147, 0])
# fileparam["randommedium1"].extend([1, 183, 0])


#priority normalize


# fileparam["randomhighest361"].extend([361, 8, 0])
# fileparam["randomhigh15"].extend([15, 7, 0])
# fileparam["randomhigh59"].extend([59, 7, 0])
# fileparam["randomhigh646"].extend([646, 7, 0])
# fileparam["randommedium1"].extend([1, 6, 0])
# fileparam["randomlow22240"].extend([22240, 5, 0])
# fileparam["randomlow5"].extend([5, 5, 0])
# fileparam["randomlow6"].extend([6, 5, 0])

# fileparam["random1"].extend([100, 255, 0])
# fileparam["random4"].extend([200, 255, 0])
# fileparam["random5"].extend([500, 255, 0])
# fileparam["random6"].extend([1000, 255, 0])
# fileparam["random7"].extend([2500, 255, 0])
# fileparam["random1"].extend([2500, 110, 0])
# fileparam["random2"].extend([2500, 255, 0])

# branch
# fileparam["random0"].extend([100, 255, 0])
# fileparam["random1"].extend([100, 255, 0])
# fileparam["random2"].extend([100, 110, 0])
# fileparam["random3"].extend([2500, 255, 0])
# fileparam["random4"].extend([2500, 110, 0])
# fileparam["random5"].extend([500, 255, 0])
# fileparam["random6"].extend([500, 110, 0])

#fileparam["random0"].extend([100, 5, 0])
# fileparam["random1"].extend([100, 5, 0])
# fileparam["random2"].extend([100, 2, 0])
# fileparam["random3"].extend([2500, 5, 0])
# fileparam["random4"].extend([2500, 2, 0])
# fileparam["random5"].extend([500, 5, 0])
# fileparam["random6"].extend([500, 2, 0])

#DFCFS
# fileparam["random"].extend([100, 5, 0])

# fileparam["random0"].extend([512, 110, 0])
# fileparam["random1"].extend([512, 110, 0])
# fileparam["random2"].extend([512, 110, 0])
# fileparam["random3"].extend([512, 110, 0])
# fileparam["random4"].extend([512, 110, 0])
# fileparam["random5"].extend([512, 110, 0])
# fileparam["random6"].extend([512, 110, 0])
# fileparam["random7"].extend([512, 110, 0])
# fileparam["random8"].extend([512, 110, 0])
# fileparam["random9"].extend([50, 255, 0])

# fileparam["random0"].extend([1280, 147, 0])

#fileparam["random3"].extend([1000, 1, 0])
#fileparam["random4"].extend([1000, 1, 0])

fileparam["random0"].extend([1000, 110, 0])
fileparam["random1"].extend([1000, 110, 0])
fileparam["random2"].extend([1000, 110, 0])
fileparam["random3"].extend([1000, 110, 0])
fileparam["random4"].extend([1000, 110, 0])
fileparam["random5"].extend([1000, 110, 0])
fileparam["random6"].extend([1000, 110, 0])
fileparam["random7"].extend([1000, 110, 0])
fileparam["random8"].extend([1000, 110, 0])
fileparam["random9"].extend([50, 254, 0])

# fileparam["random13"].extend([500, 1, 0])
# fileparam["random14"].extend([500, 1, 0])
# fileparam["random15"].extend([500, 1, 0])
# fileparam["random16"].extend([500, 1, 0])
# fileparam["random17"].extend([500, 1, 0])
# fileparam["random18"].extend([500, 1, 0])
# fileparam["random19"].extend([500, 1, 0])

# fileparam["random5"].extend([500, 1, 0])
# fileparam["random6"].extend([500, 1, 0])
# fileparam["random7"].extend([500, 1, 0])
# fileparam["random8"].extend([500, 1, 0])
# fileparam["random9"].extend([500, 1, 0])

#big file
# fileparam["random0"].extend([100000, 1, 0])
# fileparam["random1"].extend([100000, 1, 0])

#simulate githubassets.com
# fileparam["random256-5"].extend([50, 256, 0])
# fileparam["random256-50"].extend([500, 256, 0])
# fileparam["random220-5"].extend([50, 220, 0])
# fileparam["random147-05"].extend([5, 147, 0])
# fileparam["random147-5"].extend([50, 147, 0])
# fileparam["random147-50"].extend([500, 147, 0])
# fileparam["random147-100"].extend([1000, 147, 0])
# fileparam["random147-200"].extend([2000, 147, 0])

#changeDelayGradual
changedelayflag = 0
timetochange = 0.05 #s
startcount = 0
totalround = 100
sleeptime = 0#s
slowdelay = 10 #ms
delta = 8 #ms

#dependencyTreeFlag 
deepTreeFlag = 0

#changeDelaySudden
changeDelaySuddenflag = 0 # if set changeDelaySuddenflag to 1 please set changedelay flag to 0
timeToChangeDelaySudden = 0.3
slowDelaySudden = 80
jitterSudden = 20

class MpExperienceQUIC(MpExperience):
	GO_BIN = "/usr/local/go1.9/bin/go"
	SERVER_LOG = "quic_server.log"
	CLIENT_LOG = "quic_client.log"
	# CLIENT_GO_FILE = "~/go/src/github.com/lucas-clemente/pstream/example/client_benchmarker/main.go"
	CLIENT_GO_FILE = "~/go/src/github.com/lucas-clemente/pstream/example/client_branch/main.go"
	#CLIENT_GO_FILE = "~/go/src/github.com/lucas-clemente/pstream/example/client_serial/main.go"
	CLIENT_DEEPTREE_GO_FILE = "/home/mininet/go/src/github.com/lucas-clemente/pstream/example/client_browse_deptree/main.go"
	SERVER_GO_FILE = "~/go/src/github.com/lucas-clemente/pstream/example/main.go"
	CERTPATH = "~/go/src/github.com/lucas-clemente/pstream/example/"
	PING_OUTPUT = "ping.log"
	# DEPENDENCY_GRAPHS_FILE = "~/dependency_graphs/www.amazon.com_/www.amazon.com_.json"
	DEPENDENCY_GRAPHS_FILE = "~/dependency_graphs/www.google.com_/www.google.com_.json"

	def __init__(self, xpParamFile, mpTopo, mpConfig):

		MpExperience.__init__(self, xpParamFile, mpTopo, mpConfig)
		self.loadParam()
		self.mpTopo.commandTo(self.mpConfig.client, "rm " + \
			MpExperienceQUIC.PING_OUTPUT )
		self.ping()
		MpExperience.classicRun(self)

	def ping(self):
		count = self.xpParam.getParam(MpParamXp.PINGCOUNT)
		for i in range(0, self.mpConfig.getClientInterfaceCount()):
			cmd = self.pingCommand(self.mpConfig.getClientIP(i),
				self.mpConfig.getServerIP(), n = count)
			#  cmd = self.pingCommand(self.mpConfig.getClientIP(i),
			# 	 self.mpConfig.getServerIP())
			self.mpTopo.commandTo(self.mpConfig.client, cmd)

	def pingCommand(self, fromIP, toIP, n=5):
		s = "ping -c " + str(n) + " -I " + fromIP + " " + toIP + \
				  " >> " + MpExperienceQUIC.PING_OUTPUT
		print(s)
		return s
	# def pingCommand(self, fromIP, toIP):
	# 	s = "ping " + " -I " + fromIP + " " + toIP + \
	# 			  " >> " + MpExperienceQUIC.PING_OUTPUT + " &"
	# 	print(s)
	# 	return s

	def loadParam(self):
		"""
		todo : param LD_PRELOAD ??
		"""
		self.file = self.xpParam.getParam(MpParamXp.HTTPSFILE)
		self.multipath = self.xpParam.getParam(MpParamXp.QUICMULTIPATH)

	def prepare(self):
		MpExperience.prepare(self)
		self.mpTopo.commandTo(self.mpConfig.client, "rm " + \
				MpExperienceQUIC.CLIENT_LOG )
		self.mpTopo.commandTo(self.mpConfig.server, "rm " + \
				MpExperienceQUIC.SERVER_LOG )
		if self.file  == "random":
			for k, v in fileparam.items():
				cmd = "dd if=/dev/urandom of="
				cmd += k
				cmd += " bs=100 count="
				cmd += str(v[0])
				self.mpTopo.commandTo(self.mpConfig.client, cmd)
		self.ping()



	def getQUICServerCmd(self):
		s = "./server_main "
		s += " -www . -certpath " + MpExperienceQUIC.CERTPATH + " -bind 0.0.0.0:6121 &>"
		s += MpExperienceQUIC.SERVER_LOG + " &"
		print(s)
		return s
	
	def getDeepTreeQUICServerCmd(self):
		s = "./server_main"
		s += " -www /home/mininet/server -certpath " + MpExperienceQUIC.CERTPATH + " -bind 0.0.0.0:6121 &>"
		s += MpExperienceQUIC.SERVER_LOG + " &"
		print(s)
		return s

	def getQUICClientCmd(self):
		s = "./main"
		if int(self.multipath) > 0:
			s += " -m "

		for k, v in fileparam.items():
			if k != "randompre":
				s += " https://" + self.mpConfig.getServerIP() + ":6121/" + k + " " + str(v[1]) + " " + str(v[2])

		s += " &>" + MpExperienceQUIC.CLIENT_LOG
		print(s)
		return s

	def getDeepTreeQUICClientCmd(self):
		s = "./main"
		if int(self.multipath) > 0:
			s += " -m"
		s += " " + MpExperienceQUIC.DEPENDENCY_GRAPHS_FILE
		s += " &>" + MpExperienceQUIC.CLIENT_LOG
		print(s)
		return s
		
	def getQUICClientPreCmd(self):
		s = "./main"
		if int(self.multipath) > 0:
			s += " -m"
		s += " https://" + self.mpConfig.getServerIP() + ":6121/ugfiugizuegiugzeffg 10 0 &>quic_client_pre.log"
		print(s)
		return s

	def getQUICSwitchTCCmd(self):
		s = 'tc qdisc show >> ping.log'
		print(s)
		return s		

	def compileGoFiles(self):
		cmd = MpExperienceQUIC.GO_BIN + " build -a " + MpExperienceQUIC.SERVER_GO_FILE
		self.mpTopo.commandTo(self.mpConfig.server, cmd)
		self.mpTopo.commandTo(self.mpConfig.server, "mv main server_main")
		cmd = MpExperienceQUIC.GO_BIN + " build -a " + MpExperienceQUIC.CLIENT_GO_FILE
		self.mpTopo.commandTo(self.mpConfig.server, cmd)

	def compileDeepTreeGoFiles(self):
		cmd = MpExperienceQUIC.GO_BIN + " build -a " + MpExperienceQUIC.SERVER_GO_FILE
		self.mpTopo.commandTo(self.mpConfig.server, cmd)
		self.mpTopo.commandTo(self.mpConfig.server, "mv main server_main")
		cmd = MpExperienceQUIC.GO_BIN + " build -a " + MpExperienceQUIC.CLIENT_DEEPTREE_GO_FILE
		self.mpTopo.commandTo(self.mpConfig.server, cmd)

	def clean(self):
		MpExperience.clean(self)
		if self.file  == "random":
			self.mpTopo.commandTo(self.mpConfig.client, "rm random*")
	def handler(self):
		self.mpTopo.commandTo(self.mpConfig.client, "pkill -f " + MpExperienceQUIC.CLIENT_GO_FILE)

	def run(self):
		if deepTreeFlag == 0:
			self.compileGoFiles()
			cmd = self.getQUICServerCmd()
		elif deepTreeFlag == 1:
			self.compileDeepTreeGoFiles()
			cmd = self.getDeepTreeQUICServerCmd()
		self.mpTopo.commandTo(self.mpConfig.server, "netstat -sn > netstat_server_before")
		self.mpTopo.commandTo(self.mpConfig.server, cmd)

		self.mpTopo.commandTo(self.mpConfig.client, "sleep 2")

		self.mpTopo.commandTo(self.mpConfig.client, "netstat -sn > netstat_client_before")

		# cmd = "./client0jitter " + str(timetochangedelay) + " " + str(adddelay) + " " + str(addjitter) + " " + str(lasttime) + " &"
		# self.mpTopo.commandTo(self.mpConfig.client, cmd)
		self.ping()
		if changedelayflag == 1:
			cmd = "/home/mininet/switchChangeDelay.sh " + str(timetochange) + " " + str(startcount) + " " + str(totalround) + " " + str(sleeptime) + " " + str(slowdelay) + " " + str(delta) + " &"
			switch = self.mpConfig.getMidLeftName(1)
			nodeswitch = self.mpTopo.getHost(switch)
			self.mpTopo.commandTo(nodeswitch, cmd)	
		
		if changeDelaySuddenflag == 1:
			cmd = "/home/mininet/switchChangeDelaySudden.sh " + str(timeToChangeDelaySudden) + " " + str(slowDelaySudden) + " " + str(jitterSudden) + " &"
			switch = self.mpConfig.getMidLeftName(1)
			nodeswitch = self.mpTopo.getHost(switch)
			self.mpTopo.commandTo(nodeswitch, cmd)	
		# cmd = self.getQUICClientPreCmd()
		# self.mpTopo.commandTo(self.mpConfig.client, cmd)
		if deepTreeFlag == 0:
			cmd = self.getQUICClientCmd()
		elif deepTreeFlag == 1:
			cmd = self.getDeepTreeQUICClientCmd()
		signal.signal(signal.SIGALRM, self.handler)
		signal.alarm(360)
		self.mpTopo.commandTo(self.mpConfig.client, cmd)
		signal.alarm(0)
		self.mpTopo.commandTo(self.mpConfig.server, "netstat -sn > netstat_server_after")
		self.mpTopo.commandTo(self.mpConfig.client, "netstat -sn > netstat_client_after")
		self.ping()
		cmd = self.getQUICSwitchTCCmd()
		switch = self.mpConfig.getMidLeftName(1)
		nodeswitch = self.mpTopo.getHost(switch)
		self.mpTopo.commandTo(nodeswitch, cmd)
		self.mpTopo.commandTo(self.mpConfig.server, "pkill -f " + MpExperienceQUIC.SERVER_GO_FILE)

		self.mpTopo.commandTo(self.mpConfig.client, "sleep 2")
		# Need to delete the go-build directory in tmp; could lead to no more space left error
		self.mpTopo.commandTo(self.mpConfig.client, "rm -r /tmp/go-build*")
		# Remove cache data
		self.mpTopo.commandTo(self.mpConfig.client, "rm cache_*")

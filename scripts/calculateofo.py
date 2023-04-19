import os
import re
from collections import defaultdict

ofodict = defaultdict(list)
streamofodict = defaultdict(list)
averageofodict = defaultdict(list)
clientlog = r'quic_client.log'
ofolog = r'ofo.log'
totalofolog = r'totalofo.log'
averageofolog = r'averageofo.log'
file_dir = os.getcwd()
result = []


def findfiles(file_path, file_list):
	files = os.listdir(file_path)
	for s in files:
		if r'quic_client.log' in s:
			result.append(file_path)
		else:
			s_path = os.path.join(file_path, s)
			if os.path.isdir(s_path):
				findfiles(s_path, file_list)

def findmaxtime(streamofodict):
	maxtime = 0
	for name in streamofodict.keys():
		if len(streamofodict[name]) > 0:
			if streamofodict[name][-1][0] > maxtime:
				maxtime = streamofodict[name][-1][0]
	return maxtime

def takeFirst(elem):
	return elem[0]

def takeSecond(elem):
	return elem[1]
		
def findmintimeoffset(streamofodict, mintime):
	ofo = []
	lastofo = []
	resulttotalofo = []
	for name in streamofodict.keys():
		for i in range(len(streamofodict[name])):
			if streamofodict[name][i][0] <= mintime:
				continue
			else:
				sample = []
				sample.append(streamofodict[name][i][0])
				sample.append(streamofodict[name][i][1])
				ofo.append(sample)
				if i - 1 > 0:
					lastofo.append(streamofodict[name][i - 1][1])
				else:
					lastofo.append(0)
				break
	ofo.sort(key=takeFirst)
	# print(ofo)
	mintime = ofo[0][0]
	# print(mintime)
	for name in streamofodict.keys():
		if ofo[0] in streamofodict[name]:
			j = streamofodict[name].index(ofo[0])
			if j - 1 > 0:
				minusval = streamofodict[name][j-1][1]
			else:
				minusval = 0
	# print(lastofo, minusval, ofo[0][1])
	totalofosize = sum(lastofo) - minusval + ofo[0][1]
	resulttotalofo.append(mintime)
	resulttotalofo.append(totalofosize)
	return mintime, resulttotalofo

def initstreamofodict(streamofodict):
	for name in streamofodict.keys():
		streamofodict[name] = []			

def initofodict(ofodict):
	for name in ofodict.keys():
		ofodict[name] = []		

if __name__ == '__main__':
	findfiles(file_dir, result)
	for path in result:
		file_path = os.path.join(path, clientlog)
		if not os.path.isdir(file_path):
			stime = 0
			completealltime = 0
			f = open(file_path, 'r')
			initstreamofodict(streamofodict)
			finaltotal = []
			initofodict(ofodict)
			for line in f.readlines():
				validline = re.compile('receive\sframe\soffset')
				starttimeline = re.compile('GET\shttps://10.1.0.1:6121/random0,')
				completeall = re.compile('Completed\sall')
				if starttimeline.findall(line):
					# add minute to avoid 60s -> 00s
					startminute = re.findall(r'(?<=:)\d+(?=:\d+\.)',line)
					starttime = re.findall(r'(?<=:)\d+\.\d+',line)
					stime = list(map(float, starttime))[0] + list(map(float, startminute))[0] * 60
					print(minute, starttime, stime)
				#find completed all time
				if completeall.findall(line):
					c_time = re.findall(r'(?<=:\s)\d+\.\d+', line)
					completealltime = list(map(float, c_time))[0]
				if validline.findall(line):
					minute = re.findall(r'(?<=:)\d+(?=:\d+\.)',line)
					stream = re.findall(r'(?<=stream\s)\d+',line)
					offset = re.findall(r'(?<=offset\s)\d+',line)
					timestamp = re.findall(r'(?<=:)\d+\.\d+',line)
					ts_l = list(map(float, timestamp))
					ts_l[0] = ts_l[0] + list(map(float, minute))[0] * 60
					if stime > 0 and ts_l[0] > stime:
						offset_l = list(map(float, offset))
						if offset_l[0] not in ofodict[''.join(stream)]:
							x = ts_l + offset_l
							ofodict[''.join(stream)].append(x)
			if stime != 0 and list(map(float, startminute))[0] != 59:
				for name in ofodict.keys():
					beginofooffset = 0
					ofosize = 0
					streamofo = []
					queuelist = []
					for i in range(len(ofodict[name])):
						# first packet ofo
						if beginofooffset == 0 and ofodict[name][i][1] - 0 > 1340:
							queuelist.append(ofodict[name][i][1])
							queuelist.sort()
							ofosize += 1320
							sample = []
							sample.append(ofodict[name][i][0])
							sample.append(ofosize)
							streamofo.append(sample)
						elif beginofooffset == 0 and ofodict[name][i][1] - beginofooffset <= 1340:
							queuelist.append(ofodict[name][i][1])
							queuelist.sort()
							ofosize += 1320
							while len(queuelist) != 0 and queuelist[0] - beginofooffset <= 1340:
								beginofooffset = queuelist[0]
								if ofosize > 1320:
									ofosize -= 1320
								else:
									ofosize = 0
								queuelist.pop(0)
							sample = []
							sample.append(ofodict[name][i][0])
							sample.append(ofosize)
							streamofo.append(sample)							
						elif beginofooffset == 0 and ofodict[name][i][1] - ofodict[name][i - 1][1] > 1340 and len(queuelist) == 0:
							beginofooffset = ofodict[name][i - 1][1]
							queuelist.append(ofodict[name][i][1])
							queuelist.sort()
							sample = []
							sample.append(ofodict[name][i - 1][0])
							sample.append(0)
							streamofo.append(sample)
							ofosize += 1320
							sample = []
							sample.append(ofodict[name][i][0])
							sample.append(ofosize)
							streamofo.append(sample)
						elif beginofooffset != 0 and ofodict[name][i][1] - beginofooffset > 1340:
							queuelist.append(ofodict[name][i][1])
							queuelist.sort()
							ofosize += 1320
							sample = []
							sample.append(ofodict[name][i][0])
							sample.append(ofosize)
							streamofo.append(sample)
						elif beginofooffset != 0 and ofodict[name][i][1] - beginofooffset <= 1340:
							if ofodict[name][i][1] < beginofooffset:
								continue
							queuelist.append(ofodict[name][i][1])
							queuelist.sort()
							ofosize += 1320
							while len(queuelist) != 0 and queuelist[0] - beginofooffset <= 1340:
								beginofooffset = queuelist[0]
								if ofosize > 1320:
									ofosize -= 1320
								else:
									ofosize = 0
								queuelist.pop(0)
							sample = []
							sample.append(ofodict[name][i][0])
							sample.append(ofosize)
							streamofo.append(sample)							
					streamofodict[name] = streamofo
				path_new = os.path.join(path, ofolog)
				h = open(path_new, 'w+')
				for key, val in streamofodict.items():
					h.write(str(key) + "\n")
					for j in range(len(val)):
						h.write(str(val[j][0]) + "," + str(val[j][1]))
						h.write("\n")
				h.close()
			
				maxtime = findmaxtime(streamofodict)
				# print(maxtime)
				mintime = 0
				while mintime < maxtime:
					sample = []
					mintime, sample = findmintimeoffset(streamofodict, mintime)
					finaltotal.append(sample)
				ofocallist = []
				path_totalofo = os.path.join(path, totalofolog)
				h = open(path_totalofo, 'w+')
				h.write("total" + "\n")
				for i in range(len(finaltotal)):
					# ofo * lasttime
					if i >= 1:
						ofocallist.append((finaltotal[i][0] - finaltotal[i - 1][0]) * finaltotal[i - 1][1])
					h.write(str(finaltotal[i][0]) + "," + str(finaltotal[i][1]))
					h.write("\n")
				h.close()
				# print(ofocallist, completealltime)
				averageofo = sum(ofocallist) / completealltime
				print(averageofo, completealltime)
				recentdir = path.split("/")
				averageofodict[recentdir[-3]].append(averageofo)
	path_averageofo = os.path.join(file_dir, averageofolog)
	h = open(path_averageofo, 'w+')
	for key, val in averageofodict.items():
		h.write(str(key) + "\n")
		for i in range(len(val)):
			h.write(str(val[i]) + ",")
		h.write("\n")
	
				
						
				
				

							

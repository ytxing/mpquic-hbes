import os
import re
from collections import defaultdict
import shutil
filecomplete = defaultdict(float)
#filecomplete["randomhigh15"] = 0.0
#filecomplete["randomhighest361"] = 0.0
#filecomplete["randomlow2224"] = 0.0
#filecomplete["randomhigh59"] = 0.0
#filecomplete["randomhigh646"] = 0.0
#filecomplete["randomlow5"] = 0.0
#filecomplete["randomlow6"] = 0.0
#filecomplete["randommedium1"] = 0.0

#filecomplete["random0"] = 0.0
#filecomplete["random1"] = 0.0
#filecomplete["random2"] = 0.0
#filecomplete["random3"] = 0.0
#filecomplete["random4"] = 0.0
#filecomplete["random5"] = 0.0
#filecomplete["random6"] = 0.0
#filecomplete["random7"] = 0.0
#filecomplete["random8"] = 0.0
#filecomplete["random9"] = 0.0

clientlog = r'quic_client.log'
completelog = r'complete.log'
failedEXPLog = r'failed.log'
file_dir = os.getcwd()
failedEXP = []
result = []
resultdict = {}
thisexp = []
keyList = []
expList = []

def initfliecomplete(filecomplete):
	filecomplete["all"] = 0.0
	filecomplete["random0"] = 0.0
	filecomplete["random1"] = 0.0
	filecomplete["random2"] = 0.0
	filecomplete["random3"] = 0.0
	filecomplete["random4"] = 0.0
	filecomplete["random5"] = 0.0
	filecomplete["random6"] = 0.0


def findfiles(file_path, file_list):
	files = os.listdir(file_path)
	for s in files:
		if r'quic_client.log' in s:
			result.append(file_path)
		else:
			s_path = os.path.join(file_path, s)
			if os.path.isdir(s_path):
				findfiles(s_path, file_list)


if __name__ == '__main__':
	initfliecomplete(filecomplete)
	findfiles(file_dir, result)
	for key in filecomplete.keys():
		keyList.append(key)
	keyList.sort()
	toDel = []
	for path in result:
		file_path = os.path.join(path, clientlog)
		if not os.path.isdir(file_path):
			f = open(file_path, 'r')
			count = 0
			for line in f.readlines():
				for name, _ in filecomplete.items():
					if name != 'all':
						validline = re.compile('[0-9]\shttps://10.1.0.1:6121/' + name + ':\s')
						if validline.findall(line):
							count += 1
							s = re.findall(r'(?<=:\s)\d+\.\d+', line)
							filecomplete[name] = list(map(eval, s))[0]
					else:
						validline = re.compile('Completed\sall:\s')
						if validline.findall(line):
							count += 1
							s = re.findall(r'(?<=:\s)\d+\.\d+(?=ms)', line)
							#print(s)
							if len(s) != 0:
								filecomplete[name] = list(map(eval, s))[0]
							else:
								s = re.findall(r'(?<=:\s)\d+\.\d+(?=s)', line)
								filecomplete[name] = list(map(eval, s))[0] * 1000
							# print(name, filecomplete[name])
			#print(count)
			if count != 8:
				initfliecomplete(filecomplete)				
		thisexp = []
		recentdir = path.split("/")
		#print(keyList)
		for name in keyList:
			#print(name)
			value = filecomplete[name]
			if value == 0:
				break
			thisexp.append(value)
		if len(thisexp) > 0:
			if recentdir[-3] not in resultdict:
				resultdict.setdefault(recentdir[-3],[]).append(thisexp)
			else:
				resultdict[recentdir[-3]].append(thisexp)
		else:
			failedEXP.append(recentdir[-3])
			failedDir = os.path.join(recentdir[-4])
			toDel.append(failedDir + "/" + recentdir[-3])
			
	path_new = os.path.join(file_dir, completelog)
	h = open(path_new, 'w+')
	for key in resultdict.keys():
		expList.append(key)
	expList.sort()
	#print(expList)
	for key in expList:
		val = resultdict[key]
		h.write(str(key) + "\n")
		for i in range(len(val)):
			for j in range(len(val[i])):
				h.write(str(val[i][j]) + ",")
			h.write("\n")
	h.close()
	pathFailed = os.path.join(file_dir, failedEXPLog)
	if len(failedEXP) > 0:
		failedLog = open(pathFailed,'w+')
		for failedStr in failedEXP:
			path1 = defaultdict(float)
			path2 = defaultdict(float)
			path2Idx = failedStr.index("1_d")
			path1Info = failedStr[0:path2Idx]
			path2Info = failedStr[path2Idx:]
			s = path1Info[path1Info.index('d') + 1 : path1Info.index('j')]
			path1["delay"] = float(path1Info[path1Info.index('d') + 1 : path1Info.index('j')])
			path1["bandwidth"] = float(path1Info[path1Info.index('b') + 1 : -1])
			path1["queuingDelay"] = float(path1Info[path1Info.index('s') + 1 : path1Info.index('b')])
			path2["delay"] = float(path2Info[path2Info.index('d') + 1 : path2Info.index('j')])
			path2["bandwidth"] = float(path2Info[path2Info.index('b') + 1 : path2Info.index("_nt")])
			path2["queuingDelay"] = float(path2Info[path2Info.index('s') + 1 : path2Info.index('b')])	
			print("{'paths': [{", file=failedLog, end = "")
			print("'queuingDelay': '{0}', 'bandwidth': '{1}', 'delay': '{2}', 'jitter': '0'".format(path1["queuingDelay"], path1["bandwidth"], path1["delay"]), file = failedLog, end = "")
			print("},{", file = failedLog, end = "")
			print("'queuingDelay': '{0}', 'bandwidth': '{1}', 'delay': '{2}', 'jitter': '0'".format(path2["queuingDelay"], path2["bandwidth"], path2["delay"]), file = failedLog, end = "")
			print("}],'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]}", file = failedLog)
		failedLog.close()
	else:
		os.remove(pathFailed)	
	for dir in toDel:
		shutil.rmtree(dir)


	

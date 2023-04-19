import os
filePath = os.getcwd()
filePath += "/complete.log"
with open(filePath, "r", encoding = "utf-8") as f:
	lines = f.readlines()
num = 0
cwd = filePath.split('/')
evenLines = open("result.csv", 'w', encoding = "utf-8")
print(cwd[4] + " all,first,10KB_255,10KB_110,250KB_255,250KB_110,50KB_255,50KB_110", file=evenLines)
for line in lines:
	if (num % 2) == 1:
		print(line.strip(), file=evenLines)
	num += 1
evenLines.close()

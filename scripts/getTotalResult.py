import os

cwd = os.getcwd()
files = os.listdir(cwd)
f = open("total.csv","w", encoding = "utf-8")
for file in files:
	path = os.path.join(cwd, file)
	if (os.path.isdir(path)):
		print(path)
		files = os.listdir(path)
		if "result.csv" in files:
			with open(path + "/result.csv", 'r') as expResult:
				lines = expResult.readlines()
			for line in lines:
				print(line.strip(), file=f)
		print('\n', file = f)


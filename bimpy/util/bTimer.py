# 20200307

import time

class bTimer:
	def __init__(self, name=''):
		self.startTime = time.time()
		self.name = name

	def elapsed(self):
		now = time.time()
		if self.name is not None:
			#print('    ', self.name, 'took', round(now-self.startTime,2), 'seconds')
			#retStr = self.name + ' took ' + str() + ' seconds'
			numSeconds = now - self.startTime
			if numSeconds > 120:
				numMinutes = numSeconds / 60
				retStr = '{name} took {numMinutes} minutes'.format(name=self.name, numMinutes=round(numMinutes,2))
			else:
				retStr = '{name} took {numSeconds} seconds'.format(name=self.name, numSeconds=round(numSeconds,2))
			return retStr

if __name__ == '__main__':
	bt = bTimer('xxx')
	print(bt.elapsed())

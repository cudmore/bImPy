# 20200307

import time

class bTimer:
	def __init__(self, name=None):
		self.startTime = time.time()
		self.name = name
		
	def elapsed(self):
		now = time.time()
		if self.name is not None:
			print('    ', self.name, 'took', round(now-self.startTime,2), 'seconds')
		else:
			print('    took', round(now-self.startTime,2), 'seconds')

if __name__ == '__main__':
	bt = bTimer()
	bt.elapsed()

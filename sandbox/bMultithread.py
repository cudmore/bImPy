import time
from multiprocessing import Pool

def main():
	p = Pool(processes=5)
	result = p.map(some_func, range(5))
	print(result)

def some_func(i):
	print('in:', i)
	time.sleep(1)
	return(i)

if __name__ == '__main__':
	main()

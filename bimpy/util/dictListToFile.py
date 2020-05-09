import os, csv

def dictListToFile(myDictList, savePath, verbose=False):
	"""
	given a list of dict, save each dict as a row in a .csv text file
	dict values CANNOT HAVE ','
	"""
	if len(myDictList) == 0:
		return
		
	if verbose: print('dictListToFile() saving to ', savePath)
	# assuming each dict in list has same keys !!!!!!!
	csv_columns = []
	for k in myDictList[0].keys():
		csv_columns.append(k)
	
	if verbose: print('  csv_columns:', csv_columns)
	try:
		with open(savePath, 'w') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=csv_columns) #, delimiter='\t')
			writer.writeheader()
			for data in myDictList:
				if isinstance(data,tuple):
					data = str(data).replace(', ', ':')
				writer.writerow(data)
	except (IOError) as e:
		print('  IOError e:', e)

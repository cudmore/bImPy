"""
	https://osf.io/dashboard
	
	Project page
		Smooth-Muscle-Tubulin
		https://osf.io/48mq7/
		
	Install
		Using osf python client at https://github.com/osfclient/osfclient
		
		Don't install with pip (it is old) but install from clone
		
		git clone https://github.com/osfclient/osfclient.git
		cd osfclient
		pip install -e .
		
	Notes
		340 MB upload of 89 files took 22 min
		Same download took 130 seconds (2.2 min)
		
"""

import os, sys, time, requests
import osfclient

class myArgs():
	def __init__(self, myProject):
		#self.username = None
		#self.password = None
		
		# download a single file
		self.remote = 'tubulin_data/ko_male/13_5ADVMLEG1L1_ch2_dvSkel_1.tif' # could start with osfstorage/
		self.local = self.remote # will replicate folder structure
		self.force = True
		self.update = False # True does not work, file_ need md5 hash?
		self.project = myProject

		# download a remote folder
		# todo:
		
		# for upload
		
		# to upload local folder
		#self.source = 'tubulin_data/ko_male/'
		#self.source = '/Users/cudmore/Desktop/samiVolume/200108/WT_Female/'
		# remote folder test2/ will have WT_Female/
		#self.source = '/Users/cudmore/Desktop/samiVolume/200108/WT_Female'
		# remote folder test3/ will have 191230/
		self.source = '/Users/cudmore/Desktop/samiVolume/191230'
		self.destination = 'tubulin_data/test3'
		self.recursive = True
		
		'''
		# to upload one file
		self.source = 'tubulin_data/ko_male/13_5ADVMLEG1L1_ch2_dvSkel_1.tif'
		self.destination = 'tubulin_data/test/13_5ADVMLEG1L1_ch2_dvSkel_1.tif'
		self.recursive = False
		'''
		
		self.uploadForce = True # to replace existing remote
		self.uploadUpdate = True # to replace existing remote
		
def myList(osf, project):
	"""List all files from all storages for project."""
	project = osf.project(project)
	for store in project.storages:
		prefix = store.name # returns a string 'osfstorage'
		for file_ in store.files:
			path = file_.path # /tubulin_data/ko_male/13_5ADVMLEG1L1_ch2_dvSkel_1.tif
			if path.startswith('/'):
				path = path[1:]

			print(os.path.join(prefix, path))
			# osfstorage/tubulin_data/ko_male/12_5ADVMLEG1L1_ch2.tif

def myFetchFolder(osf, project, remoteFolderPath):
	print('myFetchFolder() remoteFolderPath:', remoteFolderPath)
	
	startTime = time.time()

	remoteRootPath = os.path.join('tubulin_data', remoteFolderPath)
	print('  remoteRootPath:', remoteRootPath)

	numDownloaded = 0
	downloadSize = 0
	project = osf.project(project)
	for store in project.storages:
		prefix = store.name # returns a string 'osfstorage'
		for file_ in store.files:
			filePath = file_.path # /tubulin_data/ko_male/13_5ADVMLEG1L1_ch2_dvSkel_1.tif
			if filePath.startswith('/'):
				filePath = filePath[1:]

			if filePath.startswith(remoteRootPath):
				
				localFolder, tmpLocalFile = os.path.split(filePath)
				
				if not os.path.isdir(localFolder):
					print('  making local folders:', localFolder)
					os.makedirs(localFolder)
					
				try:
					print('  downloading:', filePath)
					with open(filePath, 'wb') as fp:
						file_.write_to(fp)
				except (requests.exceptions.ConnectionError) as e:
					print('  my exception e:', e)
					raise
				numDownloaded += 1
				downloadSize += _localFileSize(filePath)

	stopTime = time.time()
	print('  done downloading', numDownloaded, 'files', downloadSize, 'MB in', round(stopTime-startTime,2), 'seconds')
			
def myFetch(osf, args):
	"""
	"""
	storage, remote_path = osfclient.utils.split_storage(args.remote)

	#print('storage:', storage)
	#print('remote_path:', remote_path)
	
	local_path = args.local
	if local_path is None:
		_, local_path = os.path.split(remote_path)

	local_path_exists = os.path.exists(local_path)
	if local_path_exists and not args.force and not args.update:
		sys.exit("Local file %s already exists, not overwriting." % local_path)

	directory, _ = os.path.split(local_path)
	if directory:
		print('local directory:', directory)
		osfclient.utils.makedirs(directory, exist_ok=True)

	#osf = _setup_osf(args)
	project = osf.project(args.project)
	print('fetching from project:', project)
	
	store = project.storage(storage)
	for file_ in store.files:
		print('file_.path:', file_.path)
		print('  ', osfclient.utils.norm_remote_path(file_.path))
		if osfclient.utils.norm_remote_path(file_.path) == remote_path:
			print('fetching remote:', remote_path)
			print('  to local:', local_path)
			if local_path_exists and not args.force and args.update:
				if file_.hashes.get('md5') == checksum(local_path):
					print("Local file %s already matches remote." % local_path)
					break
			try:
				with open(local_path, 'wb') as fp:
					file_.write_to(fp)
			except (requests.exceptions.ConnectionError) as e:
				print('my exception e:', e)
				
			# only fetching one file so we are done
			break

def myUpload(osf, args):
	"""
	Upload a new file to an existing project.
	The first part of the remote path is interpreted as the name of the
	storage provider. If there is no match the default (osfstorage) is
	used.
	If the project is private you need to specify a username.
	To upload a whole directory (and all its sub-directories) use the `-r`
	command-line option. If your source directory name ends in a / then
	files will be created directly in the remote directory. If it does not
	end in a slash an extra sub-directory with the name of the local directory
	will be created.
	To place contents of local directory `foo` in remote directory `bar/foo`:
	$ osf upload -r foo bar
	To place contents of local directory `foo` in remote directory `bar`:
	$ osf upload -r foo/ bar
	"""
	
	print('myUpload()')
	startTime = time.time()
	
	#osf = _setup_osf(args)
	if osf.username is None or osf.password is None:
		sys.exit('To upload a file you need to provide a username and'
				 ' password.')

	project = osf.project(args.project)
	storage, remote_path = osfclient.utils.split_storage(args.destination)

	store = project.storage(storage)
	if args.recursive:
		if not os.path.isdir(args.source):
			raise RuntimeError("Expected source ({}) to be a directory when "
							   "using recursive mode.".format(args.source))

		# count number of files
		numFiles = 0
		uploadSize = 0
		_, dir_name = os.path.split(args.source)
		for root, _, files in os.walk(args.source):
			subdir_path = os.path.relpath(root, args.source)
			for fname in files:
				numFiles += 1
				local_path = os.path.join(root, fname)
				uploadSize += _localFileSize(local_path)
		print('  num files:', numFiles, 'size:', uploadSize, 'MB')
		
		# local name of the directory that is being uploaded
		fileNum = 1
		uploadSize = 0
		for root, _, files in os.walk(args.source):
			subdir_path = os.path.relpath(root, args.source)
			for fname in files:
				local_path = os.path.join(root, fname)
				
				
				with open(local_path, 'rb') as fp:
					# build the remote path + fname
					name = os.path.join(remote_path, dir_name, subdir_path, fname)

					print('  .file', fileNum, 'of', numFiles)
					
					fileSize = _reportUpload(local_path, name, args.uploadUpdate)
					uploadSize += fileSize
					
					# To update an existing file set `update=True`.
					store.create_file(name, fp, force=args.uploadForce, update=args.uploadUpdate)

					fileNum += 1
	else:
		_reportUpload(args.source, remote_path, args.uploadUpdate)
		
		with open(args.source, 'rb') as fp:
			# To update an existing file set `update=True`.
			store.create_file(remote_path, fp, force=args.uploadForce, update=args.uploadUpdate)

	stopTime = time.time()
	print('  done uploading', uploadSize, 'MB in', round(stopTime-startTime,2), 'seconds')
	
def _localFileSize(path):
	fileSizeBytes = os.path.getsize(path)
	fileSizeMb = fileSizeBytes * 10 ** -6
	fileSizeMb = round(fileSizeMb,3)
	return fileSizeMb
	
def _reportUpload(srcFile, dstPath, doUpdate):
	fileSizeBytes = os.path.getsize(srcFile)
	fileSizeMb = fileSizeBytes * 10 ** -6
	fileSizeMb = round(fileSizeMb,3)
	print('  local file:', srcFile, fileSizeMb, 'MB')
	print('  to remote:', dstPath)
	print('  doUpdate:', doUpdate)
	return fileSizeMb
	
if __name__ == '__main__':
	myProject = '48mq7'

	args = myArgs(myProject)

	'''
	# fetch a file
	myOSF = osfclient.OSF(username=None, password=None, token=myProject) 
	#myList(myOSF, myProject)
	myFetch(myOSF, args)
	'''
	
	# fet a folder
	myOSF = osfclient.OSF(username=None, password=None, token=myProject) 
	remoteFolder = 'test3'
	myFetchFolder(myOSF, myProject, remoteFolder)
	
	# upload a folder
	'''
	myOSF = osfclient.OSF('rhcudmore@ucdavis.edu', 'poetry7D_', myProject) 
	myUpload(myOSF, args)
	'''

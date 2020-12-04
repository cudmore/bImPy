"""
After drawing line ROI on top of image in Fiji

Load both the .zip and .csv (measure)

we need both .zip and multimeasure

.zip gives us position in image (we can calculate length)
multimeasure .csv gives us group

install
	pip install read-roi
"""

import math, json
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib as mpl

import seaborn as sns

import read_roi # using read_roi.read_roi_zip

def defaultSeabornLayout(plotForTalk=False):
    if plotForTalk:
        plt.style.use('dark_background')
    else:
        plt.style.use('default')

    fontSize = 10
    if plotForTalk: fontSize = 14

    mpl.rcParams['figure.figsize'] = [4.0, 4.0]
    mpl.rcParams['lines.linewidth'] = 1.0
    mpl.rcParams['axes.spines.top'] = False
    mpl.rcParams['axes.spines.right'] = False
    mpl.rcParams['axes.labelsize'] = fontSize # font size of x/y axes labels (not ticks)
    mpl.rcParams['xtick.labelsize']=fontSize
    mpl.rcParams['ytick.labelsize']=fontSize

def loadRoiZip(roiSetPath, resultsPath):
	"""
	read both .zip and .csv and merge into one dataframe
	appending columns from zip

	roi zip does not have group, it is in csv

	return pandas dataframe after adding columns to .csv
		df['diam'] = diam_list
		df['x1'] = x1_list
		df['x2'] = x2_list
		df['y1'] = y1_list
		df['y2'] = y2_list
		df['xMid'] = xMid_list
		df['yMid'] = yMid_list
		df['color'] = color_list
		df['size'] = size_list
		df['area'] = area_list
	"""
	roiList = read_roi.read_roi_zip(roiSetPath) # return collections.OrderedDict
	nList = len(roiList)

	df = pd.read_csv(resultsPath)
	ndf = len(df.index)

	if nList != ndf:
		print('error: roiSet and results.csv need to be the same length')
		print(f'  roiSet {nList}, csv {ndf}')
		return None

	colorDict = {
		'1': 'r',
		'11': 'y',
		'2': 'g',
		'3': 'b',
		'4': 'm', #'y'
	}

	# these lists will be added as columns to df
	x1_list = [np.nan] * nList
	x2_list = [np.nan] * nList
	y1_list = [np.nan] * nList
	y2_list = [np.nan] * nList
	xMid_list = [np.nan] * nList
	yMid_list = [np.nan] * nList
	color_list = ['k'] * nList
	size_list = [10] * nList
	area_list = [10] * nList # for scatterplot, makrer is area, size ** 2
	diam_list = [np.nan] * nList
	for idx, roi in enumerate(roiList):
		# roi is like: ('0056-1250-1420', {'type': 'line', 'x1': 18.16666603088379, 'x2': 84.5, 'y1': 19.16666603088379, 'y2': 0.5, 'draw_offset': False, 'width': 0, 'name': '0056-1250-1420', 'position': 56})
		thisRoi = roiList[roi]
		# this roi is like: {'type': 'line', 'x1': 18.16666603088379, 'x2': 84.5, 'y1': 19.16666603088379, 'y2': 0.5, 'draw_offset': False, 'width': 0, 'name': '0056-1250-1420', 'position': 56}

		# x/y
		x1 = thisRoi['x1']
		x2 = thisRoi['x2']
		y1 = thisRoi['y1']
		y2 = thisRoi['y2']

		x1_list[idx] = x1
		x2_list[idx] = x2
		y1_list[idx] = y1
		x2_list[idx] = y2

		# x/y mid point
		xMid = min(x1,x2) + abs(x2-x1) / 2
		yMid = min(y1,y2) + abs(y2-y1) / 2

		xMid_list[idx] = xMid
		yMid_list[idx] = yMid

		# make new column with Length as diam
		diam_list[idx] = df.iloc[idx]['Length']

		# color based on group
		group = df.iloc[idx]['Group'] # np.float64
		group = int(group)
		groupStr = str(group)
		color = colorDict[groupStr]
		color_list[idx] = color

		# size/area for scatterplot based on length/diam
		length = df.iloc[idx]['Length'] # np.float64
		size_list[idx] = length
		area_list[idx] = length ** 2

	df['diam'] = diam_list
	df['x1'] = x1_list
	df['x2'] = x2_list
	df['y1'] = y1_list
	df['y2'] = y2_list
	df['xMid'] = xMid_list
	df['yMid'] = yMid_list
	df['color'] = color_list
	df['size'] = size_list
	df['area'] = area_list
	#
	return df

if __name__ == '__main__':

	maxPath = '/media/cudmore/data/san-density/SAN4/tracing/san4_max.tif'
	maxImg = plt.imread(maxPath)
	'''
	#plt.imshow(maxImg, cmap=plt.cm.reds)
	plt.imshow(maxImg)
	'''

	roiSetPath = '/media/cudmore/data/san-density/SAN4/tracing/RoiSet.zip'
	resultsPath = '/media/cudmore/data/san-density/SAN4/tracing/Results.csv'
	numRows = 7104 # original image size
	numCols = 3552
	df = loadRoiZip(roiSetPath, resultsPath)

	desc = df.groupby('Group')['Length'].describe()
	print(desc)

	defaultSeabornLayout(plotForTalk=False)

	if 1:
		# violin plot of Length for each group
		fig, ax = plt.subplots(1)
		#sns.pointplot(ax=ax, x='Group', y='Length', data=df) # this gives us mean
		palette=['r','g','b','m', 'y']
		sns.violinplot(ax=ax, x='Group', y='diam', palette=palette, data=df)
		# this should but does not work
		#sns.violinplot(ax=ax, y=df['Group'], x=df['diam'], palette=palette)
		ax.set_ylabel('Vessel Diameter ($\mu$m)')
		ax.set_xlabel('Branch Order')

	if 0:
		# histogram of Length for each group
		fig, ax = plt.subplots(1)
		binwidth = 1 # um

		#sns.histplot(ax=ax, x='diam', hue='Group', binwidth=binwidth, data=df)

		palette=['r','g','b','m', 'y'] # 'y' is for my strange 11 'in between' artery
		sns.histplot(ax=ax, x='diam', hue='Group', binwidth=binwidth, palette=palette, data=df)

		ax.set_xlabel('Vessel Diameter ($\mu$m)')
		ax.set_ylabel('Count')

	if 1:
		# scatter plot of spatial position, diameter (marker size), and group (color)
		fig, ax = plt.subplots(1)
		# s specifies, The marker size in points**2. Default is rcParams['lines.markersize'] ** 2.
		ax.imshow(maxImg, cmap='gray') # 'Reds'

		x = df['xMid'].tolist()
		y = df['yMid'].tolist()
		size = df['size'].tolist()
		#size = df['area'].tolist()
		color = df['color'].tolist()
		ax.scatter(x,y, s=size, c=color)
		ax.set_ylim(numRows, 0) #reversed
		ax.set_xlim(0, numCols)
		ax.axis('off')

	if 1:
		#
		# plot Group 1 length/diam as function of y
		fig, ax = plt.subplots(1)
		# s specifies, The marker size in points**2. Default is rcParams['lines.markersize'] ** 2.
		theseGroups = [1, 11]
		diamGroupOne = df[ df['Group'].isin(theseGroups) ]['diam'].tolist()
		yMidGroupOne = df[ df['Group'].isin(theseGroups) ]['yMid'].tolist()
		color = df[ df['Group'].isin(theseGroups) ]['color'].tolist()

		ax.scatter(diamGroupOne, yMidGroupOne, c=color) #, s=sizeList, c=colorList)
		ax.set_ylim(numRows, 0) #reversed
		ax.get_yaxis().set_visible(False)
		ax.set_xlabel('Arterial Diameter ($\mu$m)')

	#
	# todo: split group 2/3/4 based on y-position (superior/inferior)
	# for group 2 (first branch), plot hist of diameter in superior and inferior
	# plot diam hist for superior and inferior

	# seperate groups 2/3/4 green/blue/magenta in superior/inferior

	if 1:
		doViolin = False
		ySup = [1000, 3000]
		yInf = [5000, 8000]
		# plot diam of group 2 (first branches)
		theseGroups = [1, 2, 3, 4]
		palette=['r','g','b','m'] # 'y' is for my strange 11 'in between' artery
		binwidth = 1 # um
		xAxisRange = [2, 45] # share between sup/inf

		axs = [np.nan] * 2

		# superior
		sup_df = df [ (df['yMid']>ySup[0]) & (df['yMid']<ySup[1])]
		sup_df = sup_df[ sup_df['Group'].isin(theseGroups) ]

		desc = sup_df.groupby('Group')['Length'].describe()
		print('\nSuperior')
		print(desc)

		fig, ax = plt.subplots(1,1)
		axs[0] = ax

		if doViolin:
			sns.violinplot(ax=axs[0], x='Group', y='diam', palette=palette, data=sup_df)
			axs[0].set_ylim(xAxisRange) # share between sup/inf
		else:
			sns.histplot(ax=axs[0], x='diam', hue='Group', palette=palette, binwidth=binwidth, data=sup_df)
			axs[0].set_xlim(xAxisRange) # share between sup/inf
		axs[0].set_title('Superior')


		# inferior
		theseGroups = [1, 2, 3, 4, 11] # 11 is after primary branched into 2
		palette=['r','g','b', 'm', 'y'] # 'y' is for my strange 11 'in between' artery

		inf_df = df [ (df['yMid']>yInf[0]) & (df['yMid']<yInf[1])]
		inf_df = inf_df[ inf_df['Group'].isin(theseGroups) ]

		desc = inf_df.groupby('Group')['Length'].describe()
		print('Inferior')
		print(desc)

		fig, ax = plt.subplots(1,1)
		axs[1] = ax

		if doViolin:
			sns.violinplot(ax=axs[1], x='Group', y='diam', palette=palette, data=inf_df)
			axs[1].set_ylim(xAxisRange) # share between sup/inf
		else:
			sns.histplot(ax=axs[1], x='diam', hue='Group', palette=palette, binwidth=binwidth, data=inf_df)
			axs[1].set_xlim(xAxisRange) # share between sup/inf
		axs[1].set_title('Inferior')

	#
	plt.show()

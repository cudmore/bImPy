#Author: Robert Cudmore
#Date: 20190628

"""
Very simple video camera viewer. 
"""

import os, time
import cv2


#
# start a video stream that runs continuously in its own thread
vs = cv2.VideoCapture(0)

#
# get parameters from the video stream
width = vs.get(cv2.CAP_PROP_FRAME_WIDTH)
height = vs.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = vs.get(cv2.CAP_PROP_FPS)

print('width:', width)
print('height:', height)
print('fps:', fps)

#
# the window size to display
winWidth = int(width)
winHeight = int(height)

# an opencv window to display the video
cv2.namedWindow('myWindow',cv2.WINDOW_NORMAL)
cv2.moveWindow('myWindow', 50, 20)
cv2.resizeWindow('myWindow', winWidth, winHeight)

#
# we can play/pause video with 'space bar'
playing = True

# display 'paused' when paused
font                   = cv2.FONT_HERSHEY_SIMPLEX
#bottomLeftCornerOfText = (20,20)
fontScale              = 2
fontColor              = (0,255,255)
lineType               = 3

myText = ''

#
# save a file at an interval
myPath = os.path.dirname(os.path.abspath(__file__))
mySaveFilePath = os.path.join(myPath, 'onfile.tif')

saveIntervalSeconds = 1
lastSaveTimeSeconds = 0

#
# finally, just do it
while True:

	winHalfWidth = int(winWidth * 0.5)
	winHalfHeight = int(winHeight * 0.5)

	(grabbed, frame) = vs.read()
	
	if frame is not None:
		cv2.putText(frame,
			myText, 
			(winHalfWidth, winHalfHeight), 
			font, 
			fontScale,
			fontColor,
			lineType)

		if playing:
			cv2.imshow('myWindow',frame)
		
	# save a snapshop at an interval
	if playing:
		nowSeconds = time.time()
		if (nowSeconds-lastSaveTimeSeconds) > saveIntervalSeconds:
			cv2.imwrite(mySaveFilePath, frame)

	keyPress = cv2.waitKey(20) & 0xFF
	
	# 'q' to exit
	if keyPress == ord('q'):
	  break

	# 'space' to play/pause
	if keyPress == ord(' '):
		playing = not playing
		if playing:
			myText= ''
			#vs.playPause('play')
		else:
			myText='Paused'
			#vs.playPause('pause')
	
	# '+' or '=' to increase
	# '-' to decrease window size
	if keyPress == ord('-'):
		winWidth = int(winWidth * 0.8)
		winHeight = int(winHeight * 0.8)
		cv2.resizeWindow('myWindow', winWidth, winHeight)
	if keyPress in [ord('+'), ord('=')]:
		winWidth = int(winWidth * 1.2)
		winHeight = int(winHeight * 1.2)
		cv2.resizeWindow('myWindow', winWidth, winHeight)

	# keep this here
	time.sleep(0.001)
	
cv2.destroyWindow('myWindow')

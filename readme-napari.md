
Allow pan_zoom at same time as selection

I would like to be able to pan with mouse click/drag and zoom with mouse wheel while still being able to make a single click on a point annotation.


shapes

with solid arrow (e.g. move vertex tool), if user clicks in shape, not vertex, should drag shape around. like open arrow

if you add two images with different # images in 3rd dimension, e.g. video frames or z-slices. the shorter image should be set to empty when image/slice slider goes past its last image. currently, it just shows last image for all missing images/slices

can we programatically turn off some of the shapes buttons?

## multiprocessing pool directly on napari image data

having problems getting it to work

```
running line profile for all slices in PARALLEL, numImages: 1000
multiprocessing.cpu_count(): 12
WARNING: Traceback (most recent call last):
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/app/backends/_qt.py", line 495, in keyPressEvent
 self._keyEvent(self._vispy_canvas.events.key_press, ev)
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/app/backends/_qt.py", line 544, in _keyEvent
 func(native=ev, key=key, text=text_type(ev.text()), modifiers=mod)
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/util/event.py", line 455, in __call__
 self._invoke_callback(cb, event)
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/util/event.py", line 475, in _invoke_callback
 self, cb_event=(cb, event))
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/util/event.py", line 471, in _invoke_callback
 cb(event)
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/napari/_qt/qt_viewer.py", line 365, in on_key_press
 gen = func(parent)
File "bimpy/interface/bShapeAnalysisWidget.py", line 76, in user_keyboard_u
 self.updateStackLineProfile(src, dst)
File "bimpy/interface/bShapeAnalysisWidget.py", line 491, in updateStackLineProfile
 x, self.lineProfileImage, self.FWHM = self.analysis.stackLineProfile(src, dst)
File "/Users/cudmore/Sites/bImpPy/bimpy/bAnalysis2.py", line 275, in stackLineProfile
 xList, intensityProfileList, yFit, fwhmList, left_idx, right_idx = zip(*p.starmap(self.lineProfile, poolParams))
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/multiprocessing/pool.py", line 276, in starmap
 return self._map_async(func, iterable, starmapstar, chunksize).get()
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/multiprocessing/pool.py", line 657, in get
 raise self._value
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/multiprocessing/pool.py", line 431, in _handle_tasks
 put(task)
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/multiprocessing/connection.py", line 206, in send
 self._send_bytes(_ForkingPickler.dumps(obj))
File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/multiprocessing/connection.py", line 393, in _send_bytes
 header = struct.pack("!i", n)
struct.error: 'i' format requires -2147483648 <= number <= 2147483647
Abort trap: 6
```

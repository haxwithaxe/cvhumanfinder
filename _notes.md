# Notes

## Errors of note

### Traceback after delayed crash, after deleting `endcolor` and changing `startcolor`. Ran for a good 10-15mins before crashing.

'''
/bin/sh: 1: lsof: not found	# This appears before the X window appears, then script runs normally for a while, until...

ERROR: 
Traceback (most recent call last):
  File "cvdemo.py", line 93, in <module>
    hf.on_start()
  File "cvdemo.py", line 87, in on_start
    self.drawBlobs(blobs, color_map)
  File "cvdemo.py", line 58, in drawBlobs
    blob.draw(color_map[blob.area()])
  File "/usr/local/lib/python2.7/dist-packages/SimpleCV/Color.py", line 424, in __getitem__
    val = (value - self.startmap)/self.colordistance
ZeroDivisionError: float division by zero
Exception in thread Thread-1 (most likely raised during interpreter shutdown):
Traceback (most recent call last):
  File "/usr/lib/python2.7/threading.py", line 552, in __bootstrap_inner
  File "/usr/local/lib/python2.7/dist-packages/SimpleCV/Camera.py", line 35, in run
<type 'exceptions.TypeError'>: 'NoneType' object is not iterable
'''

Looks like `self.colordistance` is zero at some point.


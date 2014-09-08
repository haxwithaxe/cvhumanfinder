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

'''

class ColorMap:
    """
    **SUMMARY**

    A ColorMap takes in a tuple of colors along with the start and end points
    and it lets you map colors with a range of numbers.

    If only one Color is passed second color by default is set to White

    **PARAMETERS**

    * *color* - Tuple of colors which need to be mapped

    * *startmap* * - This is the starting of the range of number with which we map the colors

    * *endmap* * - This is the end of the range of the nmber with which we map the colors

    **EXAMPLE**

    This is useful for color coding elements by an attribute:

    >>> blobs = image.findBlobs()
    >>> cm = ColorMap(color = (Color.RED,Color.YELLOW,Color.BLUE),min(blobs.area()),max(blobs.area()))
    >>>  for b in blobs:
    >>>    b.draw(cm[b.area()])

    """
    color = ()
    endcolor = ()
    startmap = 0
    endmap = 0
    colordistance = 0
    valuerange = 0


    def __init__(self, color, startmap, endmap):
        self.color = np.array(color)
        if self.color.ndim == 1:  # To check if only one color was passed
            color = ((color[0],color[1],color[2]),Color.WHITE)
            self.color = np.array(color)
        self.startmap = float(startmap)
        self.endmap = float(endmap)
        self.valuerange = float(endmap - startmap) #delta
        self.colordistance = self.valuerange / float(len(self.color)-1) #gap between colors

    def __getitem__(self, value):
        if value > self.endmap:
            value = self.endmap
        elif value < self.startmap:
            value = self.startmap
        val = (value - self.startmap)/self.colordistance
        alpha = float(val - int(val))
        index = int(val)
        if index == len(self.color)-1:
            color = tuple(self.color[index])
            return (int(color[0]), int(color[1]), int(color[2]))
        color = tuple(self.color[index] * (1-alpha) + self.color[index+1] * (alpha))
        return (int(color[0]), int(color[1]), int(color[2]))
'''


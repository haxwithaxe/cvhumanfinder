from SimpleCV import *

cam = Camera(0, {'width':320, 'height':320})

img = cam.getImage()

print(img.save(temp=True))



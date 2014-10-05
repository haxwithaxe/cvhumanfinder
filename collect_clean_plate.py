from SimpleCV import *
import humanfinder

cam = Camera(*humanfinder.conf.camera_args)

img = cam.getImage()

img.save(humanfinder.conf.clean_plate,temp=False)



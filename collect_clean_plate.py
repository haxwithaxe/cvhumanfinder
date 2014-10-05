from SimpleCV import *
import humanfinder

cam = Camera(*humanfinder.conf.camera_args)

img = cam.getImage()

img.save(open(humanfinder.conf.clean_plate, 'w'), temp=False)



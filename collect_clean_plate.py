#!/usr/bin/env python
from SimpleCV import *
import humanfinder

cam = Camera(*humanfinder.Conf().camera_args)

img = cam.getImage()

img.save(open(humanfinder.Conf().clean_plate(), 'w'), temp=False)

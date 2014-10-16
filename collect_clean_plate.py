#!/usr/bin/env python
from SimpleCV import Camera
import humanfinder

ccp_cam = Camera(*humanfinder.Conf().camera_args)

ccp_img = ccp_cam.getImage()

ccp_img.save(open(humanfinder.Conf().clean_plate(), 'w'), temp=False)

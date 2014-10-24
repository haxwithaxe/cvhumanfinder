#!/usr/bin/env python
import sys
import time
import pykka
import collections
import logging
from SimpleCV import Camera, Image, Color

logger = logging
logger.basicConfig(level=logging.DEBUG)

# previous defaults: blob_min_radius=30; max_1_meatbag_area=11
class HumanFinder(pykka.ThreadingActor):
    def __init__(self, parent=None, cam=None, motion=False, clean_plate=None, show=False, blob_min_radius=150, motion_min_radius=30, min_motion_buffer_len=10, max_1_meatbag_area=11):
        '''
        @param  motion                  Boolean, recalibrate based on motion.
        @param  clean_plate             background image to remove the scene background from captured images Default:None
        @param  show                    Boolean, draw images on screen if True otherwise don't draw images. Default:False
        @param  blob_min_radius         Integer, minimum radius of a blob to qualify as big. Default: 30
        @param  motion_max_radius       Integer, minimum radius of a blob to qualify as not noise in motion detection. Default: 30
        @param  max_1_meatbag_area      Integer, maximum percentage of total image area expected per human.
        '''
        super(HumanFinder, self).__init__()
        self.parent = parent
        self.motion_update = motion # TODO: When does this become True?
        self._show = show
        self.blob_min_radius = blob_min_radius
        self.motion_min_radius = motion_min_radius
        self.max_1_meatbag_area = max_1_meatbag_area/100.0
        self.clean_plate = clean_plate
        self.min_motion_buffer_len = min_motion_buffer_len
        # print('Instantiating a camera object...')
        #try:
            # self.cam = Camera()
            # self.cam = Camera(0, {'width': 1600, 'height': 1200})
        #    self.cam = Camera(*Conf().camera_args)
            # print('Successfully instantiated camera object')
        #except Exception as e:
        #    print('Failed at instantiating the camera.')
        #    print(str(e))
        self.cam = cam
        self.img = None
        self.last_img = None
        self.cm_colors = (Color.RED,(128,0,0),(128,128,0),(0,255,0),(0,128,128),(0,0,128),Color.BLUE)
        self.recalibrate_interval = 60 # minutes
        self.recalibrated_last = int(time.time())
        self.motion_buffer = 0
        self._count_buffer = []
        self.thread_delay = 1
        logger.debug('initialized')

    def _pre_process_img(self, img):
        ''' do things to the image before sending it through the blob finders '''
        # print('clean_plate.jpg size: %s' % str(self.clean_plate.size()))
        # print ('About to diff greyscaled caps...')
        # logger.debug('pre-processing image: %s, %s' % (img, self.clean_plate))
        return (self.clean_plate.grayscale() - img.grayscale())

    def getImage(self):
        ''' Get the image from a camera '''
        logger.debug('in getImage()')
        # if self.motion_update is True, attempt to get a fresh clean_plate based on conditions
        if self.motion_update:
            self.last_img = self.img
            #self.recalibrate()
        # otherwise just grab an image from the camera
        i = self.cam.getImage()
        #self.img = self._pre_process_img(self.cam.getImage())
        self.show(i)
        self.img = self._pre_process_img(i)
        #logger.debug('Image i size: %s' % str(i.size()))

    def seesMotion(self):
        ''' Determine if any movement is visible between the last and current image and return True if there is.
        @returns        True if motion is detected, False if not.
        '''
        logger.debug('seesMotion')
        if (self.img is not None and self.last_img is not None):
            diff_blobs = (self.img - self.last_img).findBlobsFromWatershed()
            return len([x for x in diff_blobs if x.radius() > self.motion_min_radius]) == 0

    def getBlobs(self):
        ''' Get blobs from self.img
        @returns        List of blobs or None if no blobs.
        '''
        magic_threshold = 70
        magic_dialate = 3
        logger.debug('in getBlobs()')
        mask = self.img.threshold(magic_threshold).dilate(magic_dialate)
        blobs = self.img.findBlobsFromWatershed(mask)
        self.show(blobs)
        return blobs

    def drawBlobs(self, blobs, color_map):
        ''' Draw blobs over self.img for display purposes.
        @param  blobs       List of blobs
        @param  color_map   ColorMap object
        '''
        logger.debug('drawBlobs')
        # draw colorized blobs
        if self._show:
            logger.debug('show == True, drawing blobs, count %d' % len(blobs))
            for blob in blobs:
                ba = blob.area()
                if ba > color_map.startmap:
                    try:
                        cm = color_map[ba]
                        blob.draw(cm)
                    except DivideByZeroError as e:
                        pass

    def getColorMap(self, blobs):
        ''' Generate a ColorMap based on the blobs found
        @param  blobs       List of blobs
        @returns            ColorMap object or None if disabled
        '''
        logger.debug('getColorMap')
        if self._show:
            logger.debug('show == True, getting color map')
            color_map_end = max(blobs.area())
            color_map_start = min(blobs.area())
            return ColorMap(color=self.cm_colors, startmap=color_map_start, endmap=color_map_end)

    def drawImage(self):
        ''' Draw self.img on the screen. Disabled if show=False. '''
        logger.debug('drawImage')
        self.show(self.img)

    def on_start(self):
        ''' Main loop
            named with the intent of making this module a pykka.Actor
        '''
        logger.debug('main loop')
        while True:
            logger.debug('---------------------------------loop start')
            # throttle loop
            time.sleep(self.thread_delay)
            # get image
            self.getImage()
            # find blobs
            blobs = self.getBlobs()
            # Should 0.80 be max_1_meatbag_area?
            blobs_big = [x for x in blobs if x.radius() > self.blob_min_radius and x.area()/self.img.area() < 0.80]
            if blobs_big:
                # make color map
                if self._show:
                    color_map = self.getColorMap(blobs)
                    # draw colorized blobs
                    self.drawBlobs(blobs, color_map)
            if self._show:
                # make teh pretty pictures
                self.drawImage()
            logger.info('big blob count: %d of %d' % (len(blobs_big), len(blobs)))
            logger.debug('big blobs area %%: %s' % str([x.area()/self.img.area() for x in blobs_big]))
            count=0
            for blob in blobs_big:
                logger.debug('human count so far: %d' % count)
                if blob.area()/self.img.area() > self.max_1_meatbag_area:
                    count+=int((blob.area()/self.img.area())/self.max_1_meatbag_area)
                else:
                    count+=1
            logger.info('said "%d" to parent' % count)
            # Make sure a parent exists
            if self.parent is not None:
                self.parent.tell({'update':count})
                logger.debug('meatbags: %d' % count)

    def recalibrate(self):
        if int(time.time()) - self.recalibrated_last > 60*60:
            if self.seesMotion():
                # we see movement so we'll try again later
                self.motion_buffer = 0
                return None
            elif self.motion_buffer >= self.buffer_len:
                self.motion_buffer=0
                self.recalibrated_last = int(time.time())
                self.clean_plate = self.cam.getImage()
            else:
                self.motion_buffer+=1

    def show(self, img):
	    if self._show:
		img.show()
		print('press enter ...')
		raw_input()

class Conf(object):

    clean_plate_name = 'clean_plate'
    clean_plate_ext = '.jpg'
    # scale_y = 0
    # scale_x = 0
    # print('Hello, from Conf().')
    # if more than one cam device, perhaps set its index;
    # Firewire seems to take first index;
    # Perhaps also set w and h of webcam
    #camera_args = [0, {'width': 1600, 'height': 1200}]
    camera_args = []
    print('Init camera arguments list: %s' % camera_args)

    def clean_plate(self):
        # print('clean_plate() returning "clean_plate.jpg".')
        return '%s%s' % (self.clean_plate_name, self.clean_plate_ext)


class HFHandler(pykka.ThreadingActor):

    def __init__(self, **kwargs):
        super(HFHandler, self).__init__()
        self.kwargs = kwargs
        self.kwargs.update({'parent':self.actor_ref})
        self.buff_len = 10
        self.buff = collections.deque(maxlen=self.buff_len)

    def on_start(self):
        self.hf = HumanFinder.start(**self.kwargs)

    def on_receive(self, message):
        if 'update' in message:
            logger.info('heard "%d" from child' % message.get('update'))
            self.append(message.get('update'))
        else:
            return self.sample()

    def sample(self):
        if self.buff:
            avg = sum(self.buff)/len(self.buff)
            self.buff.clear()
            return avg
        else:
            return -1

    def append(self, value):
        if value:
            self.buff.append(value)


if __name__ == '__main__':
    camera = Camera()
    #hf = HumanFinder.start(cam=camera, show=False, clean_plate=Image(Conf().clean_plate()))
    # Original hf was HFHandler but froze on Camera object instantiation
    hf = HFHandler.start(cam=camera, show=False, clean_plate=Image(Conf().clean_plate()))
    # Hax doesn't know why this sleeps for 30s. Maybe to account for RPi (moot)
    #   shortening it to 5s
    time.sleep(5)
    # Giving it a dummy dict so it doesn't whine
    logger.info('sample: %s' % hf.ask({'a':'A'}))

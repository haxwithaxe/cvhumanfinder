from SimpleCV import *
import pykka
import time
import collections
import logging

logger = logging
logger.basicConfig(level=logging.INFO)

class HumanFinder(pykka.ThreadingActor):
    def __init__(self, parent=None, motion=False, clean_plate=None, show=False, blob_min_radius=30, motion_min_radius=30, min_motion_buffer_len=10, max_1_meatbag_area=11):
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
        self.motion_update = motion
        self._show = show
        self.blob_min_radius = blob_min_radius
        self.motion_min_radius = motion_min_radius
        self.max_1_meatbag_area = max_1_meatbag_area/100.0
        self.clean_plate = clean_plate
        self.min_motion_buffer_len = min_motion_buffer_len
	self.cam = Camera(*conf.camera_args)
        self.img = None
        self.last_img = None
        self.cm_colors = (Color.RED,(128,0,0),(128,128,0),(0,255,0),(0,128,128),(0,0,128),Color.BLUE)
        self.recalibrate_interval = 60 # minutes
        self.recalibrated_last = time.time()
        self.motion_buffer = 0
        self._count_buffer = []
        self.thread_delay = 1
        logger.debug('initialized')

    def _pre_process_img(self, img):
        ''' do things to the image before sending it through the blob finders '''
        logger.debug('pre-processing image: %s, %s' % (img, self.clean_plate))
        return (self.clean_plate.grayscale() - img.grayscale())

    def getImage(self):
        ''' Get the image from a camera '''
        logger.debug('getImage')
        # if self.motion_update is True, attempt to get a fresh clean_plate based on conditions
        if self.motion_update:
            # if self.motion_update
            self.last_img = self.img
            self.recalibrate()
        # otherwise just grab an image from the camera
	i=self.cam.getImage()
        #self.img = self._pre_process_img(self.cam.getImage())
        self.show(i)
	self.img = self._pre_process_img(i)
        logger.debug('getImage')

    def seesMotion(self):
        ''' Determine if any movement is visible between the last and current image and return True if there is.
        @returns        True if motion is detected, False if not.
        '''
        logger.debug('seesMotion')
        diff_blobs = (self.img-self.last_img).findBlobsFromWatershed()
        return len([x for x in diff_blobs if x.radius() > self.motion_min_radius]) == 0

    def getBlobs(self):
        ''' Get blobs from self.img
        @returns        List of blobs or None if no blobs.
        '''
        magic_threshold = 70
        magic_dialate = 3
        logger.debug('getBlobs')
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
               # This eventually throws a division by zero error in Color.py while calculating colordistance
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
                if blob.area() > self.max_1_meatbag_area:
                    count+=int((blob.area()/self.img.area())/self.max_1_meatbag_area)
                else:
                    count+=1
            logger.info('said "%d" to parent' % count)
            self.parent.tell({'update':count})
            logger.debug('meatbags: %d' % count)

    def recalibrate(self):
        if time.time() - self.recalibrated_last > 60*60:
            if self.seesMotion():
                # we see movement so we'll try again later
                self.motion_buffer = 0
                return None
            elif self.motion_buffer >= self.buffer_len:
                self.motion_buffer=0
                self.recalibrated_last = time.time()
                self.clean_plate = self.cam.getImage()
            else:
                self.motion_buffer+=1

    def show(self, img):
	    if self._show:
		img.show()
		print('press enter ...')
		raw_input()

class conf(object):

    clean_plate_name = u'clean_plate'
    clean_plate_ext = u'.jpg'
    scale_y = 0
    scale_x = 0
    camera_args = []

    @property
    def clean_plate(self):
        return u'%s%s' % (self.clean_plate_name,self.clean_plate_ext)


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
        self.buff.append(value)


if __name__ == '__main__':
    hf = HFHandler.start(show=True, clean_plate=Image(conf.clean_plate))
    time.sleep(30)
    logger.info('sample: %s' % hf.ask({'a':'A'}))

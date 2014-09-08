from SimpleCV import *
import time

class HumanFinder:
    def __init__(self, motion=False, motion_delay=0.50, color_map_start_color=Color.RED, color_map_end_color=Color.BLUE, color_map_start=None, color_map_end=None, background=None, show=False):
        ''' 
        @param  motion                  Boolean, if true use motion detection. Default:False
        @param  motion_delay            Float, number of seconds to wait inbetween capturing image pairs.
        @param  color_map_start_color   Default:Color.RED
        @param  color_map_end_color     Default:Color.BLUE
        @param  color_map_start         Default:None
        @param  color_map_end           Default:None
        @param  background              background image to remove the scene background from captured images Default:None
        @param  show                    Boolean, draw images on screen if True otherwise don't draw images. Default:False
        '''
        self.use_motion = motion
        self.motion_delay = motion_delay
        self.cam = Camera()
        self.img = None
        self.background = background
        self.color_map_start = color_map_start
        self.cm_start_color = Color.RED
        self.color_map_end = color_map_end
        self.cm_end_color = Color.BLUE
        self.show = show

    def getImage(self):
        ''' Get the image from a camera '''
        # if self.motion is True use a time seperated composite image
        if self.use_motion:
            # if self.motion is True use a time separated composite image
            self.getMotionImage()
        else:
            # otherwise just grab an image from the camera
            self.img = self.cam.getImage()

    def getMotionImage(self):
        ''' Get a time separated composite image that shows only things that are different between the two. '''
        img0 = self.cam.getImage()
        time.sleep(self.motion_delay)
        img1 = self.cam.getImage()
        self.img = img0-img1

    def getBlobs(self):
        ''' Get blobs from self.img 
        @returns        List of blobs or None if no blobs.
        '''
        return self.img.findBlobs()

    def drawBlobs(self, blobs, color_map):
        ''' Draw blobs over self.img for display purposes.
        @param  blobs       List of blobs
        @param  color_map   ColorMap object
        '''
        # draw colorized blobs
        if self.show:
            for blob in blobs:
               # This eventually throws a division by zero error in Color.py while calculating colordistance
               blob.draw(color_map[blob.area()])

    def getColorMap(self, blobs):
        ''' Generate a ColorMap based on the blobs found
        @param  blobs       List of blobs
        @returns            ColorMap object or None if disabled
        '''
        if self.show:
            if self.color_map_end == None: color_map_end = max(blobs.area())
            if self.color_map_start == None: color_map_start = min(blobs.area())
            #return ColorMap(startcolor=self.cm_start_color, endcolor=self.cm_end_color, startmap=min(blobs.area()), endmap=color_map_end)
            return ColorMap(color=self.cm_start_color, startmap=min(blobs.area()), endmap=color_map_end)

    def drawImage(self):
        ''' Draw self.img on the screen. Disabled if show=False. '''
        if self.show:
            self.img.show()

    def on_start(self):
        ''' Main loop '''
        while True:
            # get image
            self.getImage()
            # find blobs
            blobs = self.getBlobs()
            if blobs:
                # make color map
                color_map = self.getColorMap(blobs)
                # draw colorized blobs
                self.drawBlobs(blobs, color_map)
            # make teh pretty pictures
            self.drawImage()

if __name__ == '__main__':
    hf = HumanFinder(motion=True, show=True)
    hf.on_start()


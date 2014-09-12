from SimpleCV import *
import time

class HumanFinder:
    def __init__(self, motion=False, motion_delay=0.25, color_map_start_color=Color.RED, color_map_end_color=Color.BLUE, color_map_start=None, color_map_end=None, background=None, show=False):
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
        self.cm_colors = (Color.MAYBE_FOREGROUND) #(Color.RED,(128,0,0),(128,128,0),(0,255,0),(0,128,128),(0,0,128),Color.BLUE)
        self.color_map_end = color_map_end
        self.show = show
        self.mask = None

    def _pre_process_img(self, img):
        ''' do things to the image before sending it through the blob finders '''
        return img.grayscale()

    def getImage(self):
        ''' Get the image from a camera '''
        # if self.motion is True use a time seperated composite image
        if self.use_motion:
            # if self.motion is True use a time separated composite image
            self.img = self._pre_process_img(self.getMotionImage())
        else:
            # otherwise just grab an image from the camera
            self.img = self._pre_process_img(self.cam.getImage())
        #self.img.show()
        #raw_input()

    def getMotionImage(self):
        ''' Get a time separated composite image that shows only things that are different between the two. '''
        img0 = self.cam.getImage()
        time.sleep(self.motion_delay)
        img1 = self.cam.getImage()
        return img0-img1

    def getBlobs(self):
        ''' Get blobs from self.img
        @returns        List of blobs or None if no blobs.
        '''
        return self.img.findBlobs()

    def smartGetBlobs(self, dumb_blobs):
        ''' Get blobs from self.img 
        @returns        List of blobs or None if no blobs.
        '''
        self.getMaskFromBlobs(dumb_blobs)
        #self.img.show()
        #raw_input()
        #print(self.img.height, self.img.width)
        return self.mask.findBlobs()

    def drawBlobs(self, blobs, color_map):
        ''' Draw blobs over self.img for display purposes.
        @param  blobs       List of blobs
        @param  color_map   ColorMap object
        '''
        # draw colorized blobs
        if self.show:
            for blob in blobs:
               # This eventually throws a division by zero error in Color.py while calculating colordistance
                ba = blob.area()
                if ba > color_map.startmap:
                    try:
                        cm = color_map[ba]
                        blob.draw(cm)
                    except: #DivideByZeroError as e:
                        pass

    def getMaskFromBlobs(self, dumb_blobs):
        mask = Image((self.img.width, self.img.height))
        mask.drawRectangle(x=0, y=0, h=mask.height, w=mask.width, color=Color.BACKGROUND, alpha=0)
        #dumb_blobs.reassignImage(mask)
        for x in dumb_blobs:
            mask = mask.logicalOR(x.getFullHullMaskedImage(), grayscale=False)
        mask.applyLayers()
        mask.mergedLayers()
        #mask.show()
        #raw_input()
        self.mask = mask
 
    def getColorMap(self, blobs):
        ''' Generate a ColorMap based on the blobs found
        @param  blobs       List of blobs
        @returns            ColorMap object or None if disabled
        '''
        if self.show:
            if self.color_map_end == None:
                color_map_end = max(blobs.area())
            else:
                color_map_end = self.color_map_end
            if self.color_map_start == None:
                color_map_start = min(blobs.area())
            else:
                color_map_start = self.color_map_start
            return ColorMap(color=self.cm_colors, startmap=color_map_start, endmap=color_map_end)

    def drawImage(self):
        ''' Draw self.img on the screen. Disabled if show=False. '''
        if self.show:
            self.mask.show()

    def on_start(self):
        ''' Main loop '''
        while True:
            # get image
            self.getImage()
            # find blobs
            dumb_blobs = self.getBlobs()
            dumb_blobs.draw()
            #self.img.show()
            #raw_input()
            blobs = self.smartGetBlobs(dumb_blobs)
            if blobs:
                print(len(blobs)) #,[int(x.radius()) for x in blobs])
                # make color map
                if self.show:
                    color_map = self.getColorMap(blobs)
                    # draw colorized blobs
                    self.drawBlobs(blobs, color_map)
            if self.show:
                # make teh pretty pictures
                self.drawImage()

if __name__ == '__main__':
    hf = HumanFinder(motion=False, show=True)
    hf.on_start()

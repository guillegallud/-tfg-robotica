
import random
import numpy as np
import cv2

import tensorflow as tf
from tensorflow import keras

class EmotionRecognizer:

    def __init__(self, modelPath, length, height):
        #Load model
        self.model = keras.models.load_model(modelPath)
        self.length = length
        self.height = height

    def detect(self, image, sature=False):
        #Resize images
        dim = (self.height, self.length)
        # Perform the actual resizing of the image
        resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        #Convert into rgb format
        #inputImg = resized[...,::-1].astype(np.float32)
        inputImg = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
		
		#Perform the prediction
        prediction = self.model.predict(np.array([inputImg]).reshape(1,self.length,self.height,1))[0]
		
		#Get the index of the hightest value
        #v = prediction.index(max(prediction))

        if sature == True:
            satured = [0]*prediction.shape[0]
            satured[prediction.argmax()] = 1
            prediction = satured
            
        v = prediction
        return v

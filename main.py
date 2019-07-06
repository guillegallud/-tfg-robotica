#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Cosas relacionadas con el robot, sobre poner en marcha la camara, desactivar la
vida autonoma y otras.

La conexion entre python y JS es con las funciones callbackJS(event) y
self.tabletProxy.onJSEvent.connect(callbackJS). La segunda ejecuta la primera
cada vez que en JS se ejecuta sendToPython.
De esa forma tu codigo JS se comunica con el codigo python.

Al reves tambien es posible mediante la funcion
self.tabletProxy.executeJS("setTimeOutGlobal(100);").
Eso lo que hace es ejecutar la funcion que se pasa por parametro en JS.
Evidentemente la funcion tiene que estar definida en el codigo JS.
Esto solo le ordena al motor de JS que se ejecute esa funcion.

'''

import naoqi
from naoqi import ALProxy
from naoqi import ALModule
from naoqi import ALBroker
import vision_definitions
from PIL import Image
import qi
import math
import cv2
import time
from threading import Thread
from time import sleep
import numpy as np
from datetime import datetime, timedelta


'''importar clase de codigo de las emociones'''
from EmotionRecognizer import *
from FaceDetector import *

import random
import tensorflow as tf
from tensorflow import keras
import sys
import dlib
''''''''''''''''''''''''''''''''''''''''''''''''

print "Init broker... ",
myBroker = ALBroker("myBroker", "0.0.0.0", 0, "172.18.33.122", 9559)
#yBroker = ALBroker("myBroker", "0.0.0.0", 0, "localhost", 38553)
print "done"



class Pepper(ALModule):

	def __init__(self, name):
		ALModule.__init__(self, name)
		self.name = name
		self.PEPPER_IP = "172.18.33.122"
		self.state = 0
		self.fps = 30

		self.resolution = vision_definitions.kVGA
		self.colorSpace = vision_definitions.kRGBColorSpace

		self.session = None
		self.autonomousLifeProxy = None
		self.memoryProxy = None
		self.tabletProxy = None
		self.tabletResolution = (1280, 800)

		self.cameraProxy = None
		self.cameraClient = None
		self.lastImage = None

		self.emotionsArray = []
		self.classes = ['angry','disgusted','fearful','happy','sad','surprised','neutral']

		self.tts = None


		self.faceService = None
		self.trackingEnabled = True


	def init(self):

		print "init qi session...",
		self.session = qi.Session()
		self.session.connect("tcp://"+self.PEPPER_IP+":9559")
		print "done"


		print "disabling autonomous abilities..."
		self.autonomousLifeProxy = self.session.service("ALAutonomousLife")
		# self.autonomousLifeProxy.setAutonomousAbilityEnabled("BasicAwareness", False)
		# self.autonomousLifeProxy.setAutonomousAbilityEnabled("BackgroundMovement", False)
		# self.autonomousLifeProxy.setAutonomousAbilityEnabled("SpeakingMovement", False)
		self.autonomousLifeProxy.setAutonomousAbilityEnabled("ListeningMovement", False)
		# self.setTrackingEnabled
		print "basic ok"


		self.memoryProxy = ALProxy("ALMemory")
		print "memory ok"

		self.tts = ALProxy("ALTextToSpeech")
		print "tts ok"
		#tts es un proxy (al módulo ALTextToSpeech), say es el método
		self.tts.say("Hola")

		self.cameraProxy = self.session.service("ALVideoDevice")
		self.cameraClient = self.cameraProxy.subscribe("python_GVM", self.resolution, self.colorSpace, self.fps)
		print "internal camera setup ok"

		# Get the service ALFaceDetection.
		self.faceService = self.session.service("ALFaceDetection")
		# Enable or disable tracking.

		self.faceService.setTrackingEnabled(self.trackingEnabled)
		# Just to make sure correct option is set.
		print "Is tracking now enabled on the robot?", self.faceService.isTrackingEnabled()

		self.toggleCamera(0)
		self.startCameraService()
		print "internal camera ok"


		self.tabletProxy = self.session.service("ALTabletService")
		print "tablet ok"



		self.tabletProxy.showWebview()



		# function called when the signal onJSEvent is triggered
		# by the javascript function ALTabletBinding.raiseEvent(name)
		# interrupcion llamada al darse el evento de JS
		def callbackJS(event):



			emotionsRecord = self.emotionsArray;
			print "emotionsRecord es" + str(emotionsRecord)
			#work with it
			# https://stackoverflow.com/questions/6252280/find-the-most-frequent-number-in-a-numpy-vector/6252400
			if len(emotionsRecord) > 0:
				# https://docs.scipy.org/doc/numpy/reference/generated/numpy.pad.html
				emotionsRepetitions = [0] * 7
				# print "emotionsRepetitions antes" + str(emotionsRepetitions)
				# https://stackoverflow.com/questions/35751306/python-how-to-pad-numpy-array-with-zeros
				# va de 0 a 6 (se excluye el 7)  --> https://docs.python.org/2/tutorial/introduction.html
				emotionsRepetitions[:len(np.bincount(emotionsRecord))] = np.bincount(emotionsRecord)
				print "contenido de emotionsRepetitions es: " + str(emotionsRepetitions)
				emotionsMostFrequent = np.argmax(emotionsRepetitions)
				print "la emocion mas frecuente es " + self.classes[emotionsMostFrequent] + "\n"
				# problemas
				positiveEmotions = emotionsRepetitions[3] + emotionsRepetitions[5] + emotionsRepetitions[6]
				negativeEmotions = emotionsRepetitions[0] + emotionsRepetitions[1] + emotionsRepetitions[2] + emotionsRepetitions[4]
			else:
				positiveEmotions = 0
				negativeEmotions = 0

			print "received an event", event
			toks = event.split(":")

			#esto hara salir de spin y apagar el robot
			if toks[0] == "exit" and toks[1] == "true":
				self.state = -1

			elif toks[0] == "readText":
				text = toks[1]
				self.tts.say(text)

			elif toks[0] == "finishedPage":

				currentPage = toks[1]

				if len(toks) == 2:
					#selection en funcion de las emociones
					#if emocion positiva, cambiamos a tal; else, a la otra
					# self.emotionsArray.clear()
					print "emociones positivas = " + str(positiveEmotions)
					print "emociones negativas = " + str(negativeEmotions)


					if negativeEmotions > positiveEmotions:
						selection = "B"
					else:
						selection = "A"

					# del self.emotionsArray [:]

				elif len(toks) == 3:
					selection = toks[2]

				# toks[1] ser la pagina que abandonamos. nextPage la opcion que tomamos, y juntos forman el nombre
				# de la siguiente pagina a visitar

				script = "window.location.href = 'http://172.18.33.108/" + currentPage + selection + ".html'"
				self.tabletProxy.executeJS(script)
				sleep(5)


			# self.emotionsArray.clear()
			# clear es en python 3.3
			# https://stackoverflow.com/questions/39944586/clear-for-list-not-working-python/39944686
			del self.emotionsArray [:]


		self.tabletProxy.onJSEvent.connect(callbackJS)

		#FUNCION QUE LLAMA AL PROGRAMA JS QUE ESTA EN EL SERVIDOR, EN SIMPLE-GAME Y LO EJECUTA EN LA TABLET DE PEPPER
		script = "window.location.href = 'http://172.18.33.108/'"
		self.tabletProxy.executeJS(script)
		sleep(5)
		

		self.recognizeEmotions()
		print "emotion recognition ok"

		print "all robot services are ok"


	def toggleCamera(self, id):
		self.cameraProxy.setParam(vision_definitions.kCameraSelectID, id)


	def getImageFromCamera(self):
		return self.lastImage


	def startCameraService(self):

		def t():

			while self.state > -1:
				img = self.cameraProxy.getImageRemote(self.cameraClient)
				imageWidth = img[0]
				imageHeight = img[1]
				array = img[6]
				image_string = str(bytearray(array))

				im = Image.frombytes("RGB", (imageWidth, imageHeight), image_string) # Create a PIL Image from our pixel array.
				self.lastImage = im


		thread = Thread(target=t)
		thread.start()

	def recognizeEmotions(self):
		# se supone que puede llamarse igual que antes t() pq estan en ambitos distintos
	 	def t():
			#SACAR CONSTRUCTORES DEL HILO
			fd = FaceDetector()

			# classes = ['angry','disgusted','fearful','happy','sad','surprised','neutral']
			er = EmotionRecognizer("models/simple_fer2013_named/model.h5", 48, 48)

			while self.state > -1:
				'''llamar clase reconocimiento emociones con las imgs grabadas
				 	en un array'''
				# img = cv2.resize(self.lastImage, None, fx=0.5, fy=0.5)
				# pasamos de imagen PIL a array
				# print self.lastImage
				img = cv2.resize(np.array(self.lastImage), None, fx=0.5, fy=0.5)

				faces = fd.detect([img])

				# print faces
				# print len(faces)

				# faces seria [[]] pq es un vector preparado para recibir un batch de imgs
				# con caras detectadas y, por cada cara, 4 esquinas. si recibe una imagen por
				# instante y ninguna cara detectada, len(faces) sera 1, pero len(faces[0]) si sera 0
				if faces != [[]]:
					faceAoi = img[faces[0][0][1]:faces[0][0][3],faces[0][0][0]:faces[0][0][2]]
					# cv2.imshow("viz", faceAoi)
					# cv2.waitKey(0)

			### PROBAR A PONER getOnlyTheBiggest = True
					emotion = er.detect(faceAoi)
					# devuelve un vector con la probabilidad de que la imagen de entrada muestre cada una de las emociones anteriores
					print self.classes[np.argmax(emotion)]
					# print emotion
					self.emotionsArray.append(np.argmax(emotion))
					# no pasamos el nombre de la emocion sino el indice, logicamente

		thread = Thread(target=t)
		thread.start()


	def destroy(self):
		self.state = -1
		self.basicAwarenessProxy = self.session.service("ALBasicAwareness")
		self.basicAwarenessProxy.setEnabled(True)
		self.cameraProxy.unsubscribe(self.cameraClient)
		self.tabletProxy.resetTablet()


	def spin(self):

		def spinForever():
			while self.state > -1:
				sleep(0.1)
				pass

		spinForever()



if __name__ == "__main__":


	# https://stackoverflow.com/questions/21120947/catching-keyboardinterrupt-in-python-during-program-shutdown
	try:
		pepperControl = Pepper("pepperControl") # must have the same name!
		pepperControl.init()
		pepperControl.spin()
		pepperControl.destroy()

	except KeyboardInterrupt:
		print('Interrupted')
		pepperControl.destroy()

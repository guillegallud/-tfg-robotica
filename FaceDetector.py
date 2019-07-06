#!/usr/bin/python
# The contents of this file are in the public domain. See LICENSE_FOR_EXAMPLE_PROGRAMS.txt
#
#   This example shows how to run a CNN based face detector using dlib.  The
#   example loads a pretrained model and uses it to find faces in images.  The
#   CNN model is much more accurate than the HOG based model shown in the
#   face_detector.py example, but takes much more computational power to
#   run, and is meant to be executed on a GPU to attain reasonable speed.
#
#   You can download the pre-trained model from:
#       http://dlib.net/files/mmod_human_face_detector.dat.bz2


import sys
import dlib
import cv2
import numpy as np

class FaceDetector():

	def __init__(self):

		self.cnn_fd = dlib.cnn_face_detection_model_v1("mmod_human_face_detector.dat")


	def detect(self, img_list, getOnlyTheBiggest = False):

		dets = self.cnn_fd(img_list, 1, batch_size = len(img_list))

		detections_per_image = []
		for d in dets:
			detections = []
			for r in d:
				r = r.rect
				detections.append([int(r.left()), int(r.top()), int(r.right()), int(r.bottom())])

			detections_per_image.append(detections)

		# filtrar si hay mas de 1 bbox
		if getOnlyTheBiggest:
			detections_per_image_filtered = []
			for d in detections_per_image:
				if len(d) > 0:
					face = self.getTheBiggestFace(d)
					detections_per_image_filtered.append([face])
			return detections_per_image_filtered

		return detections_per_image

	def getTheBiggestFace(self, faces):

		biggestArea = 0
		biggestIdx = 0

		for i in range(len(faces)):
			r = faces[i]
			h = int(r[1]) - int(r[3])
			b = int(r[0]) - int(r[2])
			a = h*b

			if a > biggestArea:
				biggestArea = a
				biggestIdx = i

		return faces[biggestIdx]



if __name__ == "__main__":

	video = "/media/fran/3TB/electronics_facedetector/test_videos/sergio_alu_der.mp4"

	cap = cv2.VideoCapture(video)
	fd = FaceDetector()


	while(True):
		ret, frame = cap.read()

		listOfImages_bgr = [frame[...,::-1], frame[...,::-1]]# it works better with RGB frames instead of BGR
		listOfImages_rgb = [frame, frame]

		faces = fd.detect(listOfImages_bgr)
		print "--------"
		for i in range(len(listOfImages_bgr)):
			print "Frame",i
			for rect in faces[i]:
				print rect
				cv2.rectangle(listOfImages_rgb[i], (rect[0],rect[1]), (rect[2],rect[3]), (0,255,0), 5)



		# Display the resulting frame
		for i in range(len(listOfImages_rgb)):
			frame = cv2.resize(listOfImages_rgb[i], None, fx=0.3, fy=0.3)
			cv2.imshow('frame'+str(i),frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	# When everything done, release the capture
	cap.release()
	cv2.destroyAllWindows()

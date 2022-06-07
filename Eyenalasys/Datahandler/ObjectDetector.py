import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

class Detector:

	def __init__(self, detector) -> None:
		
		if detector == 'resnet':
			module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"
			self.__detector = hub.load(module_handle).signatures['default']
		else:
			self.__detector = cv2.dnn.readNet('models\yolo\yolov3.weights', 'models\yolo\yolo.cfg')

			self.__classes = []
			with open('models\yolo\coco.names', 'r') as f:
				self.__classes = f.read().splitlines()

		self.detector = detector
			
	def set_detector(self, detector):
		
		if detector == 'resnet':
			module_handle = 'models\\resnet_v2'
			self.__detector = hub.load(module_handle).signatures['default']
		else:
			self.__detector = cv2.dnn.readNet('models\yolo\yolov3.weights', 'models\yolo\yolo.cfg')

		self.detector = detector

	def detect(self, img):

		if self.detector == 'resnet':

			converted_img  = tf.image.convert_image_dtype(img, tf.float32)[tf.newaxis, ...]
			result = self.__detector(converted_img)

			return {key:value.numpy() for key, value in result.items()}

		else:

			blob = cv2.dnn.blobFromImage(np.array(img), 1/255, (608, 608), (0, 0, 0), swapRB=True, crop=False)
			self.__detector.setInput(blob)
			outputlayer = self.__detector.getUnconnectedOutLayersNames()
			results = self.__detector.forward(outputlayer)	


			boxes = []
			confidences = []
			classes = []

			for result in results:
				
				for detection in result:

					score = detection[5:]
					class_id = np.argmax(score)
					confidence = score[class_id]

					if confidence > 0.1:

						w = detection[2]
						h = detection[3]
						x = detection[0]
						y = detection[1]

						boxes.append([x, y, w, h])
						confidences.append(float(confidence))
						classes.append(self.__classes[class_id])

			return {'detection_class_entities': classes, 'detection_boxes': boxes, 'detection_scores': confidences}
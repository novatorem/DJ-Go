import os
import numpy as np
import cv2 as opencv
import tensorflow as tf
from statistics import mode

# File to write to for Golang
emotionFile = open("emotion.txt","w")

# Clears logging info
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

USE_WEBCAM = True # If false, loads video file source

def draw_bounding_box(face_coordinates, image_array, color):
    x, y, w, h = face_coordinates
    opencv.rectangle(image_array, (x, y), (x + w, y + h), color, 2)

def apply_offsets(face_coordinates, offsets):
    x, y, width, height = face_coordinates
    x_off, y_off = offsets
    return (x - x_off, x + width + x_off, y - y_off, y + height + y_off)

def draw_text(coordinates, image_array, text, color, x_offset=0, y_offset=0,
                                                font_scale=2, thickness=2):
    x, y = coordinates[:2]
    opencv.putText(image_array, text, (x + x_offset, y + y_offset),
                opencv.FONT_HERSHEY_SIMPLEX,
                font_scale, color, thickness, opencv.LINE_AA)

def preprocess_input(x, v2=True):
    x = x.astype('float32')
    x = x / 255.0
    if v2:
        x = x - 0.5
        x = x * 2.0
    return x

# parameters for loading data and images
emotion_model_path = './models/emotion_model.hdf5'
emotion_labels = {0:'angry',1:'disgust',2:'fear',3:'happy',
                4:'sad',5:'surprise',6:'neutral'}

# hyper-parameters for bounding boxes shape
frame_window = 10
emotion_offsets = (20, 40)

# loading models
face_cascade = opencv.CascadeClassifier('./models/haarcascade_frontalface_default.xml')
emotion_classifier = tf.keras.models.load_model(emotion_model_path)

# getting input model shapes for inference
emotion_target_size = emotion_classifier.input_shape[1:3]

# starting lists for calculating modes
emotion_window = []

# starting video streaming
opencv.namedWindow('window_frame')
video_capture = opencv.VideoCapture(0)

# Select video or webcam feed
cap = None
if (USE_WEBCAM == True):
    cap = opencv.VideoCapture(0) # Webcam source
else:
    cap = opencv.VideoCapture('./demo/FILE.mp4') # Video file source

while cap.isOpened(): # True:
    ret, bgr_image = cap.read()

    gray_image = opencv.cvtColor(bgr_image, opencv.COLOR_BGR2GRAY)
    rgb_image = opencv.cvtColor(bgr_image, opencv.COLOR_BGR2RGB)

    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5,
			minSize=(30, 30), flags=opencv.CASCADE_SCALE_IMAGE)

    sumEmotions = []
    for face_coordinates in faces:

        x1, x2, y1, y2 = apply_offsets(face_coordinates, emotion_offsets)
        gray_face = gray_image[y1:y2, x1:x2]
        try:
            gray_face = opencv.resize(gray_face, (emotion_target_size))
        except:
            continue

        gray_face = preprocess_input(gray_face, True)
        gray_face = np.expand_dims(gray_face, 0)
        gray_face = np.expand_dims(gray_face, -1)
        emotion_prediction = emotion_classifier.predict(gray_face)
        emotion_probability = np.max(emotion_prediction)
        emotion_label_arg = np.argmax(emotion_prediction)
        emotion_text = emotion_labels[emotion_label_arg]
        emotion_window.append(emotion_text)

        sumEmotions.append(emotion_text)

        if len(emotion_window) > frame_window:
            emotion_window.pop(0)
        try:
            emotion_mode = mode(emotion_window)
        except:
            continue

        if emotion_text == 'angry':
            color = emotion_probability * np.asarray((255, 0, 0))
        elif emotion_text == 'sad':
            color = emotion_probability * np.asarray((0, 0, 255))
        elif emotion_text == 'happy':
            color = emotion_probability * np.asarray((255, 255, 0))
        elif emotion_text == 'surprise':
            color = emotion_probability * np.asarray((0, 255, 255))
        else:
            color = emotion_probability * np.asarray((0, 255, 0))

        color = color.astype(int)
        color = color.tolist()

        draw_bounding_box(face_coordinates, rgb_image, color)
        draw_text(face_coordinates, rgb_image, emotion_mode,
                  color, 0, -45, 1, 1)

    if len(sumEmotions) > 0:
        emotionFile.seek(0)
        emotionFile.write(max(set(sumEmotions), key=sumEmotions.count))
        emotionFile.truncate()

    bgr_image = opencv.cvtColor(rgb_image, opencv.COLOR_RGB2BGR)
    opencv.imshow('window_frame', bgr_image)
    if opencv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
opencv.destroyAllWindows()

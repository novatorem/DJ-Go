from ctypes import *

import subprocess
import numpy as np
import os
import cv2
import time

os.system('go build -o djgo.so -buildmode=c-shared djgo.go')
pigo = cdll.LoadLibrary('./djgo.so')
os.system('rm djgo.so')

MAX_NDETS = 2024
ARRAY_DIM = 5

# define class GoPixelSlice to map to:
# C type struct { void *data; GoInt len; GoInt cap; }


class GoPixelSlice(Structure):
    _fields_ = [
        ("pixels", POINTER(c_ubyte)), ("len", c_longlong), ("cap", c_longlong),
    ]

# Obtain the camera pixels and transfer them to Go trough Ctypes.


def process_frame(pixs):
    dets = np.zeros(ARRAY_DIM * MAX_NDETS, dtype=np.float32)
    pixels = cast((c_ubyte * len(pixs))(*pixs), POINTER(c_ubyte))

    # call FindFaces
    faces = GoPixelSlice(pixels, len(pixs), len(pixs))
    pigo.FindFaces.argtypes = [GoPixelSlice]
    pigo.FindFaces.restype = c_void_p

    # Call the exported FindFaces function from Go.
    ndets = pigo.FindFaces(faces)
    data_pointer = cast(ndets, POINTER((c_longlong * ARRAY_DIM) * MAX_NDETS))

    if data_pointer:
        buffarr = ((c_longlong * ARRAY_DIM) *
                   MAX_NDETS).from_address(addressof(data_pointer.contents))
        res = np.ndarray(buffer=buffarr, dtype=c_longlong,
                         shape=(MAX_NDETS, ARRAY_DIM,))

        # The first value of the buffer aray represents the buffer length.
        dets_len = res[0][0]
        res = np.delete(res, 0, 0)  # delete the first element from the array

        # We have to multiply the detection length with the total
        # detection points(face, pupils and facial lendmark points), in total 18
        dets = list(res.reshape(-1, ARRAY_DIM))[0:dets_len*18]
        return dets


# initialize the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Changing the camera resolution introduce a short delay in the camera initialization.
# For this reason we should delay the object detection process with a few milliseconds.
time.sleep(0.4)

showPupil = True
showEyes = False
showLandmarkPoints = True

while(True):
    ret, frame = cap.read()
    pixs = np.ascontiguousarray(
        frame[:, :, 1].reshape((frame.shape[0], frame.shape[1])))
    pixs = pixs.flatten()

    # Verify if camera is intialized by checking if pixel array is not empty.
    if np.any(pixs):
        dets = process_frame(pixs)  # pixs needs to be numpy.uint8 array

        if dets is not None:
            # We know that the detected faces are taking place in the first positions of the multidimensional array.
            for det in dets:
                # det[3] = confidence
                # det[4] = landmark
                if det[3] > 30 and det[4] == 2:  
                        if showLandmarkPoints:
                            # Landmark Points
                            cv2.circle(frame, (int(det[1]), int(det[0])), 4, (255, 200, 50), -1, 8, 0)
                            
            print(dets)
    cv2.imshow('', frame)

    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break
    elif key & 0xFF == ord('a'):
        showLandmarkPoints = not showLandmarkPoints

cap.release()
cv2.destroyAllWindows()

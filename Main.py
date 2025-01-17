from encode_faces import encodeFaces
from manageData import *
from imutils.video import VideoStream
from imutils.video import FPS
import requests
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2
import os
import time
import sys

global name
global result
global exitFlag
exitFlag = False

def facialRecognition():
    global name
    global exitFlag
    name = "Unknown"
    # construct the argument parser and parse the arguments
    #ap = argparse.ArgumentParser()
    #ap.add_argument("-c", "--cascade", required=True,
    #        help = "path to where the face cascade resides")
    #ap.add_argument("-e", "--encodings", required=True,
    #        help="path to serialized db of facial encodings")
    #args = vars(ap.parse_args())

    # load the known faces and embeddings along with OpenCV's Haar
    # cascade for face detection
    print("[INFO] loading encodings + face detector...")
    #data = pickle.loads(open(args["encodings"], "rb").read())
    #detector = cv2.CascadeClassifier(args["cascade"])
    data = pickle.loads(open("encodings.pickle", "rb").read())
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    # initialize the video stream and allow the camera sensor to warm up
    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    # vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)

    # start the FPS counter
    fps = FPS().start()
    
    sendStatus('complete')

    # loop over frames from the video file stream
    while True:
        name = "Unknown"
        #print('Looping...')
        # grab the frame from the threaded video stream and resize it
        # to 500px (to speedup processing)
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
            
        # convert the input frame from (1) BGR to grayscale (for face
        # detection) and (2) from BGR to RGB (for face recognition)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # detect faces in the grayscale frame
        rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
                minNeighbors=5, minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE)

        # OpenCV returns bounding box coordinates in (x, y, w, h) order
        # but we need them in (top, right, bottom, left) order, so we
        # need to do a bit of reordering
        boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []

        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(data["encodings"],
                            encoding)

            # check to see if we have found a match
            if True in matches:
                    # find the indexes of all matched faces then initialize a
                    # dictionary to count the total number of times each face
                    # was matched
                    matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                    counts = {}

                    # loop over the matched indexes and maintain a count for
                    # each recognized face face
                    for i in matchedIdxs:
                            name = data["names"][i]
                            counts[name] = counts.get(name, 0) + 1

                    # determine the recognized face with the largest number
                    # of votes (note: in the event of an unlikely tie Python
                    # will select first entry in the dictionary)
                    name = max(counts, key=counts.get)
                    
                    print(name)
            # update the list of names
            names.append(name)

            # loop over the recognized faces
            for ((top, right, bottom, left), name) in zip(boxes, names):
                    # draw the predicted face name on the image
                    cv2.rectangle(frame, (left, top), (right, bottom),
                            (0, 255, 0), 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                            0.75, (0, 255, 0), 2)

        if adminInput() == True:
            exitFlag = True
            break

            # if the `q` key was pressed, break from the loop
        if picButton() == True:
            print('Pic Button Pressed')
            sendName(name)
            sendStatus('complete')
            
            break
        #else:
            # send current name to database
            #sendName(name)

        # update the FPS counter
        fps.update()
        
        # display the image to our screen
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
            
        #break

    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()
    return name;

def buildFaceData():
    global result
    
    #prompt for username
    while(isSubmit()==False):
       time.sleep(1)
        
    userName = getName()
    print(userName)

    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cascade", required=False, default="haarcascade_frontalface_default.xml",
        help = "path to where the face cascade resides")
    ap.add_argument("-o", "--output", required=False, default=os.path.expanduser('~') + "database/" + userName)
    args = vars(ap.parse_args())


    # load OpenCV's Haar cascade for face detection from disk
    detector = cv2.CascadeClassifier(args["cascade"])

    # initialize the video stream, allow the camera sensor to warm up,
    # and initialize the total number of example faces written to disk
    # thus far
    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    #vs = VideoStream(usePiCamera=True).start()
    time.sleep(0.5)
    total = 0
    sendStatus('ready')

    # loop over the frames from the video stream
    while True:
        # grab the frame from the threaded video stream, clone it, (just
        # in case we want to write it to disk), and then resize the frame
        # so we can apply face detection faster
        frame = vs.read()
        orig = frame.copy()
        frame = imutils.resize(frame, width=500)

        # detect faces in the grayscale frame
        rects = detector.detectMultiScale(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), scaleFactor=1.1, 
            minNeighbors=5, minSize=(30, 30))

        #boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
        # loop over the face detections and draw them on the frame
        for (x, y, w, h) in rects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
        # show the output frame
        cv2.imshow("Frame", frame)
        #cv2.imshow("orig", orig)
        key = cv2.waitKey(1) & 0xFF
     
        # if the `k` key was pressed, write the *original* frame to disk
        # so we can later process it and use it for face recognition
            #print('Waiting for button press....')
        if picButton(): 
            print('Button Pressed')
            
            #p = os.path.sep.join([args["output"], "{}.png".format(
            #    str(total).zfill(5))])
            newPath = "/home/pi/ece3552-finalProject/dataset/" + userName
            if not os.path.exists(newPath):
                os.makedirs(newPath)
            
            p = os.path.sep.join([os.path.expanduser('~') + "/ece3552-finalProject/dataset/" + userName, "{}.png".format(
                str(total).zfill(5))])
            print(p)
            if not cv2.imwrite(p, orig):
                result = False
                print('False')
            else:
                result = True
                print('True')
                
            break
            time.sleep(2)
            # Break from loop after picture taken
        #time.sleep(2)
        #break

    # do a bit of cleanup
    if result == True:
        print("[INFO] {} face images stored".format(total))
        print("[INFO] cleaning up...")
        sendStatus('complete')
    else:
        print("[WARNING] Could not save images.... Closing Windows")
        sendStatus('error')
    cv2.destroyAllWindows()
    vs.stop()


#vs = VideoStream(src=0).start()
#encodeFaces()
#time.sleep(2)
while True:
    facialRecognition()
    if exitFlag == True:
        break
    if name == 'Unknown':
        sendStatus('new')
        buildFaceData()
    else:
        sendStatus('old')
        #time.sleep(1)
        
encodeFaces()
print('Faces Encoded')

sys.exit('Exit-Success')

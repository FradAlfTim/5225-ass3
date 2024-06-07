import boto3
import json
import cv2
import numpy as np
import uuid
import time

s3_client = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

TABLE_NAME = 'database'
DETECTION_BUCKET = '5225-a3-detection-files'
YOLO_FILES = ['coco.names', 'yolov3-tiny.cfg', 'yolov3-tiny.weights']

# construct the argument parse and parse the arguments
confthres = 0.3
nmsthres = 0.1

def load_model(configpath, weightspath):
    # load our YOLO object detector trained on COCO dataset (80 classes)
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net


def do_prediction(image, net, LABELS):
    (H, W) = image.shape[:2]
    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    # print(layerOutputs)
    end = time.time()

    # show timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            # print(scores)
            classID = np.argmax(scores)
            # print(classID)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > confthres:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])

                confidences.append(float(confidence))
                classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres, nmsthres)

    results = {"tags": []}
    # TODO Prepare the output as required to the assignment specification
    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # ignore detected objects with an accuracy of detection below 0.5
            if(confidences[i] < 0.5):
                continue
            results["tags"].append(LABELS[classIDs[i]])
            
    return results

def download_yolo_files():
    for file_name in YOLO_FILES:
        s3_client.download_file(DETECTION_BUCKET, file_name, f'/tmp/{file_name}')

def lambda_handler(event, context):

    try:
        download_yolo_files()

        ## Yolov3-tiny versrion
        labelsPath = "/tmp/coco.names"
        Lables = open(labelsPath).read().strip().split("\n")
        CFG = "/tmp/yolov3-tiny.cfg"
        Weights = "/tmp/yolov3-tiny.weights"
        # load the neural net.
        nets = load_model(CFG, Weights)
    except Exception as e:
        print("Fail to load yolo_tiny_configs......")
        print(f"Error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps('Error loading yolo_tiny_configs')
        }

    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        object_key = message['object_key']
        
        bucket = '5225-a3-image'
        thumbnail_bucket = '5225-a3-thumbnails'
        thumbnail_key = "thumb-" + object_key 
        
        try:
            # Retrieve original image
            img_response = s3_client.get_object(Bucket=bucket, Key=object_key)
            img_data = img_response['Body'].read()
            np_array = np.fromstring(img_data, np.uint8)
            image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            
            # Perform object detection using YOLO
            tags = do_prediction(image, nets, Lables)
            
            # Generate unique ID for the image
            id = str(uuid.uuid4())
            
            # Store metadata in DynamoDB
            item = {
                'id': {'S': id},
                's3_url': {'S': f'https://{bucket}.s3.ap-southeast-2.amazonaws.com/{object_key}'},
                'thumbnail_url': {'S': f'https://{thumbnail_bucket}.s3.ap-southeast-2.amazonaws.com/{thumbnail_key}'},
                'tags': {'S': json.dumps(tags)}
            }

            dynamodb.put_item(TableName=TABLE_NAME, Item=item)
            print(f"Putting {item} into {TABLE_NAME} sucess.")
            return {
                'statusCode': 200,
                'body': json.dumps('Image metadata stored successfully')
            }
        
        except Exception as e:
            print(e)
            return {
                'statusCode': 400,
                'body': json.dumps('Error processing image')
            }

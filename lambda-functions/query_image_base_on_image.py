import boto3
import json
import cv2
import numpy as np
import time
from boto3.dynamodb.conditions import Attr
from base64 import b64decode

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = 'database' 
table = dynamodb.Table(table_name)

DETECTION_BUCKET = '5225-a3-detection-files'
YOLO_FILES = ['coco.names', 'yolov3-tiny.cfg', 'yolov3-tiny.weights']

confthres = 0.3
nmsthres = 0.1

def load_model(configpath, weightspath):
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net

def do_prediction(image, net, LABELS):
    (H, W) = image.shape[:2]
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    end = time.time()

    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    boxes = []
    confidences = []
    classIDs = []

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > confthres:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres, nmsthres)

    results = {"tags": []}
    if len(idxs) > 0:
        for i in idxs.flatten():
            if confidences[i] < 0.5:
                continue
            results["tags"].append(LABELS[classIDs[i]])
            
    return results

def download_yolo_files():
    for file_name in YOLO_FILES:
        s3_client.download_file(DETECTION_BUCKET, file_name, f'/tmp/{file_name}')

def lambda_handler(event, context):
    status_code = 200
    response_body = {}
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': '*',
        'Access-Control-Allow-Headers': '*',
    }
    
    # Handle CORS preflight request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps('CORS preflight response')
        }
    
    try:
        download_yolo_files()
        labelsPath = "/tmp/coco.names"
        with open(labelsPath, 'r') as file:
            LABELS = file.read().strip().split("\n")
        CFG = "/tmp/yolov3-tiny.cfg"
        Weights = "/tmp/yolov3-tiny.weights"
        nets = load_model(CFG, Weights)
    except Exception as e:
        print("Fail to load yolo_tiny_configs......")
        print(f"Error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps('Error loading yolo_tiny_configs'),
            'headers': headers
        }

    try:
        print("[INFO] Parsing event body...")
        body = json.loads(event.get('body', '{}'))
        encoded_image = body.get('image')
        
        if not encoded_image:
            raise ValueError("Missing image data in request body")

        print("[INFO] Decoding image...")
        decoded_image_data = b64decode(encoded_image)
        np_array = np.frombuffer(decoded_image_data, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image")

        print("[INFO] Running prediction...")
        tags = do_prediction(image, nets, LABELS)
        print(tags)

        if tags['tags']:
            print("[INFO] Detected tags: ", tags['tags'])
            print("[INFO] Building filter expression...")
            filter_expression = None
            for tag in tags['tags']:
                if filter_expression is None:
                    filter_expression = Attr('tags').contains(tag)
                else:
                    filter_expression = filter
                    filter_expression & Attr('tags').contains(tag)

            print("[INFO] Scanning DynamoDB table...")
            response = table.scan(
                FilterExpression=filter_expression
            )
            items = response.get('Items', [])
            print(f"[INFO] Found {len(items)} items in DynamoDB matching tags.")

            response_body = {
                'tags': tags['tags'],
                'items': items
            }
        else:
            print("[INFO] No tags detected in the image.")
            response_body = {
                'tags': [],
                'items': []
            }

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        status_code = 500
        response_body = {
            'error': str(e)
        }
    
    return {
        'statusCode': status_code,
        'body': json.dumps(response_body),
        'headers': headers
    }
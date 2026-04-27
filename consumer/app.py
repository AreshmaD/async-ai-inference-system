import os
import json
import time
from datetime import datetime, timezone

import boto3
import joblib
import numpy as np

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("BUCKET_NAME")
MODEL_KEY = os.getenv("MODEL_KEY", "models/model.pkl")
QUEUE_URL = os.getenv("QUEUE_URL")

LOCAL_MODEL_PATH = "/tmp/model.pkl"

s3 = boto3.client("s3", region_name=AWS_REGION)
sqs = boto3.client("sqs", region_name=AWS_REGION)

def load_model():
    print("Downloading model from S3...")
    s3.download_file(BUCKET_NAME, MODEL_KEY, LOCAL_MODEL_PATH)
    model = joblib.load(LOCAL_MODEL_PATH)
    print("Model loaded successfully.")
    return model

def write_prediction(record_id, prediction):
    result = {
        "record_id": record_id,
        "prediction": int(prediction),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    key = f"predictions/{record_id}.json"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(result).encode("utf-8"),
        ContentType="application/json"
    )
    print(f"Wrote prediction to s3://{BUCKET_NAME}/{key}")

def process_message(model, message):
    body = json.loads(message["Body"])
    record_id = body["record_id"]
    features = body["features"]

    X = np.array(features).reshape(1, -1)
    prediction = model.predict(X)[0]

    write_prediction(record_id, prediction)

    sqs.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=message["ReceiptHandle"]
    )
    print(f"Deleted message for {record_id}")

def poll():
    model = load_model()

    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,
            VisibilityTimeout=30
        )

        messages = response.get("Messages", [])
        if not messages:
            print("No messages found. Sleeping...")
            time.sleep(2)
            continue

        for message in messages:
            try:
                process_message(model, message)
            except Exception as e:
                print(f"Error processing message: {e}")

if __name__ == "__main__":
    poll()
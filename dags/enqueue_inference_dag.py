from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import json
import boto3

BUCKET_NAME = "reshma-async-ml-project-2026"
TEST_KEY = "artifacts/test_records.jsonl"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/394757036844/ml-inference-queue"

def enqueue_messages():
    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")

    obj = s3.get_object(Bucket=BUCKET_NAME, Key=TEST_KEY)
    lines = obj["Body"].read().decode("utf-8").splitlines()

    for line in lines:
        record = json.loads(line)
        message_body = {
            "record_id": record["record_id"],
            "features": record["features"]
        }

        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )

default_args = {
    "owner": "airflow",
    "start_date": datetime(2026, 4, 1),
}

with DAG(
    dag_id="enqueue_inference_jobs",
    default_args=default_args,
    schedule=None,
    catchup=False,
) as dag:

    enqueue_task = PythonOperator(
        task_id="send_test_records_to_sqs",
        python_callable=enqueue_messages
    )
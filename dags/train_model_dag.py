from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import json
import joblib
import boto3

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

BUCKET_NAME = "reshma-async-ml-project-2026"
MODEL_KEY = "models/model.pkl"
TEST_KEY = "artifacts/test_records.jsonl"

def train_and_upload():
    s3 = boto3.client("s3")

    data = load_breast_cancer()
    X = data.data
    y = data.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=10000)
    model.fit(X_train, y_train)

    local_model_path = "/tmp/model.pkl"
    joblib.dump(model, local_model_path)
    s3.upload_file(local_model_path, BUCKET_NAME, MODEL_KEY)

    local_test_path = "/tmp/test_records.jsonl"
    with open(local_test_path, "w") as f:
        for i, features in enumerate(X_test):
            record = {
                "record_id": f"sample_{i:03d}",
                "features": features.tolist(),
                "label": int(y_test[i])
            }
            f.write(json.dumps(record) + "\n")

    s3.upload_file(local_test_path, BUCKET_NAME, TEST_KEY)

default_args = {
    "owner": "airflow",
    "start_date": datetime(2026, 4, 1),
}

with DAG(
    dag_id="train_model_to_s3",
    default_args=default_args,
    schedule=None,
    catchup=False,
) as dag:

    train_task = PythonOperator(
        task_id="train_and_upload_model",
        python_callable=train_and_upload
    )
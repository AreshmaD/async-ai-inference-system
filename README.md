# Final Project: Asynchronous AI Inference System

## Overview
This project builds a simple asynchronous machine learning inference pipeline using Airflow, S3, SQS, Docker, Amazon ECR, and Kubernetes Deployment YAML.

The system trains a breast cancer classification model, stores it in S3, sends inference jobs to SQS, and processes them asynchronously with a containerized consumer.

## Architecture

### Training Flow
1. Airflow loads the sklearn breast cancer dataset
2. Splits data into train and test sets
3. Trains a Logistic Regression model
4. Saves `model.pkl` to Amazon S3
5. Saves test records to S3 as `artifacts/test_records.jsonl`

### Inference Flow
1. Airflow reads `test_records.jsonl` from S3
2. Sends one SQS message per record
3. Consumer polls SQS
4. Consumer loads model from S3 on startup
5. Consumer performs inference
6. Consumer writes one prediction file per record back to S3

## S3 Structure
- `models/model.pkl`
- `artifacts/test_records.jsonl`
- `predictions/sample_000.json`

## Message Format

```json
{
  "record_id": "sample_001",
  "features": [...]
}
```
## Prediction Output Format
``` json
{
  "record_id": "sample_001",
  "prediction": 1,
  "timestamp": "2026-04-15T12:00:00Z"
}
```
## Files Included

	•	dags/train_model_dag.py
	•	dags/enqueue_inference_dag.py
	•	consumer/app.py
	•	consumer/requirements.txt
	•	consumer/Dockerfile
	•	k8s/consumer-deployment.yaml

## How to Run

1. Train the model

Run the Airflow training DAG:

	•	train_model_to_s3

This stores:

	•	models/model.pkl
	•	artifacts/test_records.jsonl

2. Enqueue inference jobs

Run the Airflow queue population DAG:

	•	enqueue_inference_jobs

This sends one SQS message per test record.

3. Build the consumer container
``` 
docker build -t ml-consumer:latest .
```
4. Run consumer locally
```
docker run --rm \
  -e AWS_REGION=us-east-1 \
  -e BUCKET_NAME=reshma-async-ml-project-2026 \
  -e MODEL_KEY=models/model.pkl \
  -e QUEUE_URL=https://sqs.us-east-1.amazonaws.com/394757036844/ml-inference-queue \
  -v ~/.aws:/root/.aws \
  ml-consumer:latest
```
5. Push image to ECR
```
docker tag ml-consumer:latest 394757036844.dkr.ecr.us-east-1.amazonaws.com/ml-consumer:latest
docker push 394757036844.dkr.ecr.us-east-1.amazonaws.com/ml-consumer:latest
```

6. Kubernetes deployment

The Kubernetes deployment YAML is included in:
	•	k8s/consumer-deployment.yaml

## Results

The system successfully:

	•	trained a model
	•	saved the model to S3
	•	stored the test dataset in S3
	•	sent one message per record to SQS
	•	processed messages with the consumer
	•	wrote prediction files to S3

Example prediction files:

	•	predictions/sample_000.json
	•	predictions/sample_001.json

## Kubernetes Limitation

A Kubernetes Deployment YAML was created and the Docker image was pushed to Amazon ECR.

However, full EKS cluster creation in the provided AWS lab environment was blocked by IAM restrictions. The account did not allow iam:CreateRole, which is required to create the EKS cluster and its service roles.

Because of this environment restriction, live Kubernetes deployment could not be completed in the lab account, even though the application container and deployment YAML were fully prepared.

## Production Improvement

One production improvement would be to add a Dead Letter Queue (DLQ) so that messages that fail repeatedly can be isolated instead of being retried forever.

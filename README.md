# Final Project: Asynchronous AI Inference System

## Overview
This project builds a simple asynchronous machine learning inference pipeline using Airflow, S3, SQS, Docker, Amazon ECR, Amazon ECS and Kubernetes Deployment YAML.

The system trains a breast cancer classification model, stores it in S3, sends inference jobs to SQS, and processes them asynchronously with a containerized consumer.

## System Architecture

### Training Flow
1. Airflow loads the sklearn breast cancer dataset
2. Splits the data into train and test sets
3. Trains a Logistic Regression model
4. Saves the trained model (`model.pkl`) to Amazon S3
5. Saves the test records to S3 as `artifacts/test_records.jsonl`

### Inference Flow
1. Airflow reads the saved test records (`test_records.jsonl`) from S3
2. Sends one SQS message per record
3. The Consumer application polls the SQS queue
4. The Consumer loads the trained model from S3 on startup
5. The Consumer performs inference on each message
6. The Consumer writes one prediction file per record back to S3
7. The SQS message is deleted only after successful processing

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
    AirFlow DAGs
	•	dags/train_model_dag.py
	•	dags/enqueue_inference_dag.py
	
    Consumer Application
	•	consumer/app.py
	•	consumer/requirements.txt
	
	Containerization
	•	consumer/Dockerfile
	
	Deployment
	•	k8s/consumer-deployment.yaml
	
	Documentation 
	•   README.md
	 

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

## Deployment Approach

Amazon ECS was used for the live deployment of the consumer application. The container image was pushed to Amazon ECR, and the ECS service was configured to run the consumer with the required environment variables for S3 and SQS access. The service continuously polled the SQS queue, loaded the trained model from S3, performed inference, and wrote prediction results back to S3.

A Kubernetes deployment YAML file was also prepared and included in the project as part of the required deliverables:

* k8s/consumer-deployment.yaml

## Scaling Demonstration

To demonstrate scalability, the ECS service was first launched with 1 running task. After confirming that the consumer was working correctly, the service was updated to run multiple tasks. This showed that the system could scale horizontally and process queue messages in parallel using more than one worker.

## Results

The system successfully:

* trained a model with Airflow
* stored the model in S3
* stored the test dataset in S3
* sent one message per record to SQS
* processed messages with the consumer
* wrote prediction results to S3 as separate JSON files
* pushed the container image to ECR
* demonstrated scalable deployment using ECS

## Production Improvement

One production improvement would be to add a Dead Letter Queue (DLQ) so that  If a message fails multiple times, it should be moved to a DLQ instead of being retried forever. This would make the system easier to monitor, debug, and operate more reliably at scale.

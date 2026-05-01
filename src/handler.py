import boto3
import json

# boto3 is the AWS SDK for Python, I need this to talk to DynamoDB
dynamodb = boto3.resource("dynamodb")

# pointing to my specific table, I created this in the AWS console
table = dynamodb.Table("notes-table")

def handler(event, context):
    # every request hits this function first
    # I will add GET, POST, DELETE logic here in the next step
    return {
        "statusCode": 200,
        "headers": { "Content-Type": "application/json" },
        "body": json.dumps({ "message": "Notes API is running" })
    }
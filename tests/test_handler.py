import json
import sys
import os

# I need this so Python can find my handler file inside src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import handler

def test_handler_returns_200():
    # I am simulating what API Gateway would send to my Lambda
    fake_event = {
        "httpMethod": "GET",
        "queryStringParameters": None,
        "body": None,
        "headers": {}
    }

    # context can be empty for now, I am not using it yet
    fake_context = {}

    # call my handler the same way AWS would
    response = handler.handler(fake_event, fake_context)

    # check that it returned a 200 status code
    assert response["statusCode"] == 200

    # check that the body contains the expected message
    body = json.loads(response["body"])
    assert body["message"] == "Notes API is running"
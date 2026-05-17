import json
import sys
import os
from unittest.mock import MagicMock, patch

# I need this so Python can find my handler file inside src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# I am setting a fake table name before importing handler
# because handler reads TABLE_NAME when it loads
os.environ["TABLE_NAME"] = "notes-table"

import handler

# POST tests

def test_create_note_success():
    # I am simulating a POST request with all required fields
    fake_event = {
        "httpMethod": "POST",
        "queryStringParameters": None,
        "body": json.dumps({
            "id": "001",
            "title": "Grocery list",
            "content": "Milk, eggs"
        }),
        "headers": {}
    }

    # I am faking the DynamoDB put_item call so I dont need a real database
    with patch.object(handler.table, "put_item", return_value={}) as mock_put:
        response = handler.handler(fake_event, {})

        # confirm put_item was actually called once
        mock_put.assert_called_once()

    # a successful creation should return 201
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["message"] == "note created"


def test_create_note_missing_fields():
    # I am simulating a POST request with missing content field
    fake_event = {
        "httpMethod": "POST",
        "queryStringParameters": None,
        "body": json.dumps({
            "id": "001",
            "title": "Grocery list"
            # content is missing on purpose
        }),
        "headers": {}
    }

    response = handler.handler(fake_event, {})

    # missing fields should return 400
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body


# GET tests
def test_get_note_success():
    # I am simulating a GET request for a specific note by id
    fake_event = {
        "httpMethod": "GET",
        "queryStringParameters": {"id": "001"},
        "body": None,
        "headers": {}
    }

    # I am faking what DynamoDB would return for this note
    fake_note = {"id": "001", "title": "Grocery list", "content": "Milk, eggs"}

    with patch.object(handler.table, "get_item", return_value={"Item": fake_note}):
        response = handler.handler(fake_event, {})

    # found the note so should return 200
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["title"] == "Grocery list"


def test_get_note_not_found():
    # I am simulating a GET request for a note that doesnt exist
    fake_event = {
        "httpMethod": "GET",
        "queryStringParameters": {"id": "999"},
        "body": None,
        "headers": {}
    }

    # DynamoDB returns no Item when the note doesnt exist
    with patch.object(handler.table, "get_item", return_value={}):
        response = handler.handler(fake_event, {})

    # note not found should return 404
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert body["error"] == "note not found"


def test_get_all_notes():
    # I am simulating a GET request with no id which triggers a scan
    fake_event = {
        "httpMethod": "GET",
        "queryStringParameters": None,
        "body": None,
        "headers": {}
    }

    # I am faking what DynamoDB scan would return
    fake_notes = [
        {"id": "001", "title": "Grocery list", "content": "Milk"},
        {"id": "002", "title": "Meeting notes", "content": "Discuss Q3"}
    ]

    with patch.object(handler.table, "scan", return_value={"Items": fake_notes}):
        response = handler.handler(fake_event, {})

    # should return 200 with all notes
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 2


# DELETE tests

def test_delete_note_success():
    # I am simulating a DELETE request for a specific note
    fake_event = {
        "httpMethod": "DELETE",
        "queryStringParameters": {"id": "001"},
        "body": None,
        "headers": {}
    }

    with patch.object(handler.table, "delete_item", return_value={}) as mock_delete:
        response = handler.handler(fake_event, {})

        # confirm delete_item was actually called
        mock_delete.assert_called_once()

    # successful deletion should return 200
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "note deleted"


def test_delete_note_missing_id():
    # I am simulating a DELETE request with no id provided
    fake_event = {
        "httpMethod": "DELETE",
        "queryStringParameters": None,
        "body": None,
        "headers": {}
    }

    response = handler.handler(fake_event, {})

    # missing id should return 400
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body


# unsupported method test

def test_unsupported_method():
    # I am simulating a PUT request which my API doesnt support
    fake_event = {
        "httpMethod": "PUT",
        "queryStringParameters": None,
        "body": None,
        "headers": {}
    }

    response = handler.handler(fake_event, {})

    # unsupported method should return 405
    assert response["statusCode"] == 405
import boto3
import json
import os

# boto3 is the AWS SDK, I need this to talk to DynamoDB
dynamodb = boto3.resource("dynamodb")

# I am reading the table name from environment variables
# I set this in template.yaml so I dont hardcode it here
table = dynamodb.Table(os.environ.get("TABLE_NAME", "notes-table"))

def handler(event, context):
    # every request comes through here first
    # I check which HTTP method was used and route accordingly
    method = event["httpMethod"]

    print("Received method:", method)

    if method == "POST":
        return create_note(event)

    elif method == "GET":
        return get_note(event)

    elif method == "DELETE":
        return delete_note(event)

    else:
        # if someone sends a method I dont support, return 405
        return response(405, {"error": "method not supported"})


def create_note(event):
    # if the body is missing or empty, return 400
    # without this check, json.loads(None) would crash the Lambda
    if not event.get("body"):
        return response(400, {"error": "request body is required"})

    # the body arrives as a raw JSON string so I have to parse it first
    # if the JSON is malformed, json.loads raises an exception
    # I catch it and return a clean 400 instead of crashing
    try:
        body = json.loads(event["body"])
    except json.JSONDecodeError:
        return response(400, {"error": "invalid JSON in request body"})

    print("Creating note with title:", body.get("title"))

    # make sure the required fields were actually sent
    if "id" not in body or "title" not in body or "content" not in body:
        return response(400, {"error": "id, title and content are required"})

    # save the note to DynamoDB
    # if DynamoDB has any issue I catch it and return 500 so the user
    # gets a clear error instead of a cryptic crash
    try:
        table.put_item(
            Item={
                "id": body["id"],
                "title": body["title"],
                "content": body["content"]
            }
        )
    except Exception as e:
        print("DynamoDB error in create_note:", str(e))
        return response(500, {"error": "could not save note"})

    print("Note created successfully")

    # 201 means something new was created
    return response(201, {"message": "note created", "id": body["id"]})


def get_note(event):
    params = event.get("queryStringParameters")

    # if no id was sent, return all notes using scan
    if not params or "id" not in params:
        print("No id provided, fetching all notes")

        try:
            result = table.scan()
        except Exception as e:
            print("DynamoDB error in scan:", str(e))
            return response(500, {"error": "could not fetch notes"})

        notes = result["Items"]

        print("Found", len(notes), "notes")

        return response(200, notes)

    # if id was sent, fetch that specific note
    note_id = params["id"]
    print("Fetching note with id:", note_id)

    try:
        result = table.get_item(Key={"id": note_id})
    except Exception as e:
        print("DynamoDB error in get_note:", str(e))
        return response(500, {"error": "could not fetch note"})

    # .get() returns None safely if the note doesnt exist
    note = result.get("Item")

    if not note:
        print("Note not found:", note_id)
        return response(404, {"error": "note not found"})

    print("Note found, returning it")
    return response(200, note)


def delete_note(event):
    params = event.get("queryStringParameters")

    # id is required to delete — cant delete without knowing which one
    if not params or "id" not in params:
        return response(400, {"error": "id is required to delete a note"})

    note_id = params["id"]
    print("Deleting note with id:", note_id)

    try:
        table.delete_item(Key={"id": note_id})
    except Exception as e:
        print("DynamoDB error in delete_note:", str(e))
        return response(500, {"error": "could not delete note"})

    print("Note deleted successfully")
    return response(200, {"message": "note deleted", "id": note_id})


def response(status_code, body):
    # I built this helper so I dont repeat the same return structure everywhere
    # every response needs statusCode, headers, and body as a string
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
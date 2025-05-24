from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from fastapi.requests import Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.errors import SlackApiError

from config.env import env

from utils.drive import handle_drive_notification
from utils.rag import user_input
from utils.rag import user_input

app = FastAPI()
slack_app = App(token=env.SLACK_TOKEN) 
app_handler = SlackRequestHandler(slack_app) 

class UserBody(BaseModel):
  query: str

# Slack Event Handlers
@slack_app.event("app_home_opened")
def handle_home_opened(payload, client):
    history = client.conversations_history(channel=payload["channel"])

    for message in history["messages"]:
        try:
            client.chat_delete(channel=payload["channel"], ts=message["ts"])
        except SlackApiError as e:
            print("Error deleting message: {}".format(e.response["error"]))
            continue

    client.chat_postMessage(
        channel=payload["channel"], 
        text="Welcome to the Policy Chatbot!",
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Welcome to the *Policy Chatbot*"
            }
        }]    
    )

@slack_app.event("app_mention")
def handle_mention(payload, client):
    channel_id = payload["channel"]
    user_query = payload["text"]

    query_response = user_input(user_query, [])
    response = query_response[0][1]

    print(response)
    if user_query:
        try:
            client.chat_postMessage(
                channel=channel_id,
                text=response,
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response
                    }
                }]  
            )
        except SlackApiError as e:
            print("Error sending message: {}".format(e.response["error"]))
    else:
        client.chat_postMessage(
            channel=channel_id, 
            text="Ask any question!"
        )

@slack_app.event("message")
def hadle_message(payload, client):
    channel_id = payload["channel"]
    user_query = payload["text"]

    query_response = user_input(user_query, [])
    response = query_response[0][1]

    print(response)
    if user_query:
        try:
            client.chat_postMessage(
                channel=channel_id,
                text=response,
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response
                    }
                }]  
            )
        except SlackApiError as e:
            print("Error sending message: {}".format(e.response["error"]))
    else:
        client.chat_postMessage(
            channel=channel_id, 
            text="Ask any question!"
        )

@app.post("/slack/events")
async def slack_events(req: Request):
    return await app_handler.handle(req)

# Domain Verification Handler
@app.get("/{file_name}")
def read_root(file_name: str):
    try:
        with open(file_name, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return JSONResponse(content={"error": "File not found"})
    
# Chat API Handler
@app.post("/chat")
def handle_chat(user_body: UserBody):
    response = user_input(user_body.query, [])
    return {
        "query_response": response[0][1]
    }

# Drive Watch Webhook Handler
@app.post("/drive/callback")
async def read_headers(request: Request):
    headers = dict(request.headers)
    try:
      handle_drive_notification()
    except Exception as e:
        print(f"Error handling drive notification: {e}")
    return JSONResponse(content={"headers": headers})
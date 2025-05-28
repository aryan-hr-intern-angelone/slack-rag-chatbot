import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi.requests import Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.errors import SlackApiError

from utils.drive import generate_file_index, handle_drive_notification
from utils.rag import user_input

app = FastAPI()

slack_app = App(token=os.environ["SLACK_TOKEN"]) 
app_handler = SlackRequestHandler(slack_app) 

class UserBody(BaseModel):
  query: str

@slack_app.event("app_home_opened")
def handle_home_opened(payload, client):
    user_id = payload["user"]
    history = client.conversations_history(channel=payload["channel"])

    for message in history["messages"]:
        try:
            client.chat_delete(channel=payload["channel"], ts=message["ts"])
        except SlackApiError as e:
            print("Error deleting message: {}".format(e.response["error"]))
            continue
    user_info = client.users_info(user=user_id)
    user_name = user_info["user"]["real_name"]

    client.chat_postMessage(
        channel=payload["channel"], 
        text="Welcome to the Policy Chatbot!",
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Welcome to AskHR Bot, your personal assistant for HR queries. Ask any question and get the answer in a few seconds!"
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

    if user_query:
        query_response = user_input(user_query, [])
        response = query_response[0][1]
        quoted_response = "\n".join(f"> {line}" for line in response.splitlines())
        
        print(response)

        is_null_context = "NULLCONTEXT" in quoted_response 
        print(is_null_context)
        quoted_response = quoted_response.replace("NULLCONTEXT", "").strip()

        response_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": quoted_response        
            }
        }]

        if is_null_context:
            response_blocks.extend([
                {
                    "type": "section",
                    "text": {
                    "type": "mrkdwn",
                    "text": "Hi, the chatbot is still learning and was unable to answer your question. Please raise the ticket using the button below and reach out to you designated HRBP."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                    {
                        "type": "button",
                        "text": {
                        "type": "plain_text",
                        "text": "Raise Ticket",
                        "emoji": True 
                        },
                        "url": "https://hrsupport.angelone.in/hc/en-us/requests/new?ticket_form_id=5893162753309"
                    }
                    ]
                }
            ])

        else:
            response_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Please share your feedback on the above response for improving the chatbot."
                }
            })

            response_blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👍"
                        },
                        "value": "thumbs_up",
                        # for future handling
                        "action_id": "feedback_thumbs_up"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👎"
                        },
                        "value": "thumbs_down",
                        # for future handling
                        "action_id": "feedback_thumbs_down"
                    }
                ]
            })

        try:
            client.chat_postMessage(
                channel=channel_id,
                text=response,
                blocks=response_blocks
            )
        except SlackApiError as e:
            print("Error sending message: {}".format(e.response["error"]))
    else:
        client.chat_postMessage(
            channel=channel_id,
            text="Ask any question!"
        )

@slack_app.action("feedback_thumbs_up")
@slack_app.action("feedback_thumbs_down")
def handle_thumbs_down(ack, body, client):
    ack()
    user = body["user"]["id"]
    client.chat_postMessage(
        channel=body["channel"]["id"],
        text="Thank you for sharing your feedback."
    )

@app.post("/slack/events")
async def slack_events(req: Request):
    return await app_handler.handle(req)

@app.get("/{file_name}")
def read_root(file_name: str):
    try:
        with open(file_name, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return JSONResponse(content={"error": "File not found"})
    
@app.post("/chat")
def handle_chat(user_body: UserBody):
    response = user_input(user_body.query, [])
    return {
        "query_response": response[0][1]
    }

@app.post("/drive/callback")
async def read_headers(request: Request):
    headers = dict(request.headers)
    try:
      handle_drive_notification()
    except Exception as e:
        print(f"Error handling drive notification: {e}")
    return JSONResponse(content={"headers": headers})
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from database.db import User, ChatHistory
from database.db_session import get_session
from utils.rag import user_input
from utils.semantics import rl
from config.env import env

app = App(token=env.SLACK_TOKEN)
handler = SocketModeHandler(app, env.SLACK_SOCKET_TOKEN)

session = get_session()
chat_history = []

@app.event("app_home_opened")
def handle_home_opened(payload, client):
    user_id = payload["user"]
    channel_id = payload["channel"]
    user_details = client.users_info(user=user_id)
    user = session.get(User, user_id)

    if not user:
        fname = user_details["user"]["profile"]["first_name"]
        lname = user_details["user"]["profile"]["last_name"]
        slack_username = user_details["user"]["name"]
    
        try:
            user = User(
                id=user_id,
                fname=fname,
                lname=lname,
                slack_username=slack_username
            )
            
            session.add(user)
            session.commit()
        except Exception as e:
            print(f"Error creating user: {e}")
        
        client.chat_postMessage(
            channel=channel_id,
            text="Welcome to the Policy Chatbot!",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hi {fname}, Welcome to AskAngela, your personal assistant for HR queries. Ask any question and get the answer in a few seconds!"
                }
            }]
        )

@app.event("message")
def handle_message(payload, client):
    channel_id = payload["channel"]
    user_query = payload["text"]
    
    print(payload)

    if user_query:
        query_response, sources, hits = user_input(user_query, chat_history)
        response = query_response["response"]
        quoted_response = "\n".join(f"> {line}" for line in response.splitlines())
        source_str = ", ".join(str(source.replace(".txt", "")) for source in sources)

        response_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": quoted_response        
            }
        }]
        
        detect_query = rl(user_query).name
        detect_response = rl(response).name
        
        print(detect_query, detect_response)
        
        try:
            user_role = ChatHistory(
                channel_id=channel_id,
                user_id=payload["user"],
                role="user",
                content=user_query
            )
            
            assistant_role = ChatHistory(
                channel_id=channel_id,
                user_id=payload["user"],
                role="assistant",
                content=response,
                docs_reffered=source_str
            )
            
            session.add_all([user_role, assistant_role])
            session.commit()
        except Exception as e:
            print(f"Error saving chat history: {e}")
        
        if detect_query != 'chitchat' and detect_response != 'nocontext':
            response_blocks.extend([{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Please share your feedback on the above response for improving the chatbot."
                }
            }, {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👍"
                        },
                        "value": "thumbs_up",
                        "action_id": "feedback_thumbs_up"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👎"
                        },
                        "value": "thumbs_down",
                        "action_id": "feedback_thumbs_down"
                    }
                ]
            }])
        elif detect_response == 'nocontext' and detect_query != 'chitchat':
            response_blocks.extend([
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Looks like AskAngela missed the mark 😅 We will imporve on it. Meanwhile, feel free to drop a ticket or hit up your HRBP!"
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
                ]
            )
        else: 
            pass 

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

@app.action("feedback_thumbs_down")
def handle_thumbs_up(ack, body, client):
    ack()
    channel_id = body["channel"]["id"]
    
    try:
        chat_history = session.query(ChatHistory).filter(
            ChatHistory.channel_id == channel_id,
            ChatHistory.role == "assistant"
        ).first()
        chat_history.pos_feedback = True
        session.commit()
    except Exception as e:
        print(f"Error updating chat history: {e}")
    
    client.chat_postMessage(
        channel=channel_id,
        text="",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Looks like AskAngela missed the mark 😅 We got your feedback and we’re on it. Meanwhile, feel free to drop a ticket or hit up your HRBP!"
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
        ]
    )

@app.action("feedback_thumbs_up")
def handle_thumbs_down(ack, body, client):
    ack()
    channel_id = body["channel"]["id"]
    
    try:
        chat_history = session.query(ChatHistory).filter(
            ChatHistory.channel_id == channel_id,
            ChatHistory.role == "assistant"
        ).first()

        chat_history.pos_ = True
        session.commit()
    except Exception as e:
        print(f"Error updating chat history: {e}")
    
    client.chat_postMessage(
        channel=channel_id,
        text="👍 Thank you for your feedback!",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Thank you so much for your positive feedback."
                }
            }
        ]
    ) 

handler.start()
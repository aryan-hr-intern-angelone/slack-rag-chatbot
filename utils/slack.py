import re

def format_to_slack_markdwn(text):
    text = re.sub(r'\*(.*?)\*', r'\*\1\*', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(\s?)', r"-\1", text)
    return text



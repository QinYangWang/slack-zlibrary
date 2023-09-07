import logging

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from utils.ylibrary import search, download
from urllib.parse import parse_qs


app = App(process_before_response=True)


@app.command("/find")
def command_find(ack, command):
    ack( search(command['text']))

@app.action("prev_page")
@app.action("next_page")
def action_prev_page(ack, action, respond):
    parsed_data = parse_qs(action['value'])
    ack()
    respond(search(parsed_data['keyword'][0], int(parsed_data['page'][0])))

def lazy_action_download_book(body, respond):
    parsed_data = parse_qs(body['actions'][0]['value'])
    respond(download(int(parsed_data['id'][0]), parsed_data['source'][0], body['user']['id']))


def action_download_book(ack, action, respond):
    ack()
    parsed_data = parse_qs(action['value'])
    respond(f'Your book: {parsed_data["title"]} is in download process.')

app.action("download_book")(
    ack=action_download_book,
    lazy=[lazy_action_download_book]
)

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

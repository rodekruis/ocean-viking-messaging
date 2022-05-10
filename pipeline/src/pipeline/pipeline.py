import datetime
import requests
import pandas as pd
import os
import time
from twilio.rest import Client
from dotenv import load_dotenv
from twilio.base.exceptions import TwilioRestException
import click
import json
import logging
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG, filename='ex.log')
# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
twilio_logger = logging.getLogger('twilio.http_client')
twilio_logger.setLevel(logging.WARNING)
# load credentials
load_dotenv(dotenv_path="../credentials/.env")


def get_kobo_data():
    # get data from kobo
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    data_request = requests.get(
        f'https://kobonew.ifrc.org/api/v2/assets/{os.getenv("ASSET")}/data.json',
        headers=headers)
    data = data_request.json()
    if 'results' in data.keys():
        df_form = pd.DataFrame(data['results'])
    else:
        df_form = pd.DataFrame(columns=['name', 'language', 'telephone', 'message_status'])
    return df_form


def update_kobo_data(submission_id, field, status):
    """update message_status of one submission"""

    # update submission in kobo
    url = f'https://kobonew.ifrc.org/api/v2/assets/{os.getenv("ASSET")}/data/bulk/'
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    params = {'format': 'json'}
    payload = {
        "submission_ids": [str(submission_id)],
        "data": {field: status}
    }
    print(payload)
    r = requests.patch(
        url=url,
        data={'payload': json.dumps(payload)},
        params=params,
        headers=headers
    )
    return r


@click.command()
def main():
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    df_to_send = get_kobo_data()
    logging.info(f"Processing {len(df_to_send)} kobo submissions")
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)
    df_message_text = pd.read_excel('../data/message-text.xlsx')

    for ix, row in df_to_send.iterrows():
        if row['message_status'] == 'new':
            logging.info(f"New submission found, sending message")
            name = row['name']
            lang = row['language']
            phone = row['telephone']

            message_text = df_message_text.loc[df_message_text['language'] == lang]['message'].values[0]
            message_text = message_text.replace('123', name)
            sid = ""
            error = ""

            try:
                message = client.messages.create(
                    body=str(message_text),
                    from_=os.environ['MESSAGING_SERVICE'],
                    to='+' + str(phone),
                    status_callback=os.environ['STATUS_CALLBACK_URL']
                )
                sid = message.sid
            except TwilioRestException as e:
                logging.error(e)
                error = e

            submission_id = row['_id']
            update_kobo_data(submission_id, 'message_status', 'processed')
            if sid != "":
                update_kobo_data(submission_id, 'message_sid', sid)
            else:
                update_kobo_data(submission_id, 'error_code', str(error))

    logging.info('Python timer trigger function ran at %s', utc_timestamp)


if __name__ == "__main__":
    main()
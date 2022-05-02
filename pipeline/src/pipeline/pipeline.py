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
load_dotenv(dotenv_path="credentials/.env")
# set valid message statuses
VALID_MESSAGE_STATUS = ['delivered',
                        'not_delivered']


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


def update_kobo_data(submission_id, status):
    """update message_status of one submission"""
    if status not in VALID_MESSAGE_STATUS:
        raise ValueError("update_kobo_data: status must be one of %r." % VALID_MESSAGE_STATUS)

    # update submission in kobo
    url = f'https://kobonew.ifrc.org/api/v2/assets/{os.getenv("ASSET")}/data/bulk/'
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    params = {'format': 'json'}
    payload = {
        "submission_ids": [str(submission_id)],
        "data": {'message_status': status}
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
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)
    df_message_text = pd.read_excel('../data/message-text.xlsx')

    for ix, row in df_to_send.iterrows():
        if row['message_status'] == 'new':
            name = row['name']
            lang = row['language']
            phone = row['telephone']

            message_text = df_message_text.loc[df_message_text['language'] == lang]['message'].values[0]
            message_text = message_text.replace('123', name)
            from_text = df_message_text.loc[df_message_text['language'] == lang]['from'].values[0]
            is_sender_alphanumeric = True
            sid = 0
            delivered = False

            try:
                message = client.messages.create(
                    body=str(message_text),
                    from_=str(from_text),
                    to='+' + str(phone)
                )
                sid = message.sid
            except TwilioRestException as e:
                logging.error(e)
                is_sender_alphanumeric = False
                try:
                    message = client.messages.create(
                        body=str(message_text),
                        from_='+' + os.environ['TWILIO_PHONE_NUMBER'],
                        to='+' + str(phone)
                    )
                    sid = message.sid
                except TwilioRestException as e:
                    logging.error(e)

            # wait 30 seconds and check message status;
            time.sleep(30)
            try:
                message = client.messages(sid).fetch()
                error_code = message.error_code
                if error_code is None:
                    delivered = True
                # if failed with error 30008 (unknown error), try without alphanumeric sender
                if error_code == 30008 and is_sender_alphanumeric:
                    try:
                        client.messages.create(
                            body=str(message_text),
                            from_='+' + os.environ['TWILIO_PHONE_NUMBER'],
                            to='+' + str(phone)
                        )
                        time.sleep(30)
                        message = client.messages(sid).fetch()
                        error_code = message.error_code
                        if error_code is None:
                            delivered = True
                    except TwilioRestException as e:
                        logging.error(e)
            except TwilioRestException as e:
                logging.error(e)

            submission_id = row['_id']
            if delivered:
                update_kobo_data(submission_id, 'delivered')
            else:
                update_kobo_data(submission_id, 'not_delivered')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)


if __name__ == "__main__":
    main()
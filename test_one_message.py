import datetime
import requests
import pandas as pd
import os
from twilio.rest import Client
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from twilio.base.exceptions import TwilioRestException
import click
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
load_dotenv(dotenv_path="credentials/.env")


@click.command()
def main():
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    df_message_text = pd.read_excel('data/message-text.xlsx')
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    name = "Bob"
    lang = "arabic"
    phone = "XXXXX"

    message_text = df_message_text.loc[df_message_text['language'] == lang]['message'].values[0]
    message_text = message_text.replace('123', name)
    from_text = df_message_text.loc[df_message_text['language'] == lang]['from'].values[0]

    try:
        message = client.messages.create(
            body=str(message_text),
            from_=str(from_text),
            to='+'+str(phone)
        )
    except TwilioRestException as e:
        logging.error(e)
        try:
            message = client.messages.create(
                body=str(message_text),
                from_='+'+os.environ['TWILIO_PHONE_NUMBER'],
                to='+'+str(phone)
            )
        except TwilioRestException as e:
            logging.error(e)

    print(message.status)
    logging.info('Python timer trigger function ran at %s', utc_timestamp)


if __name__ == "__main__":
    main()
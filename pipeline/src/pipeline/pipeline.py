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
load_dotenv(dotenv_path="../credentials/.env")


def get_blob_service_client(blob_path):
    blob_service_client = BlobServiceClient.from_connection_string(os.getenv("CONNECTION"))
    return blob_service_client.get_blob_client(container='messaging', blob=blob_path)


def upload_data(data_path='messages.csv', blob_path='messages.csv'):
    # upload data to azure blob storage
    blob_client = get_blob_service_client(blob_path)
    with open(data_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)


def download_data(data_path='messages.csv', blob_path='messages.csv'):
    # download data from azure blob storage
    blob_client = get_blob_service_client(blob_path)
    with open(data_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())


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
        df_form = pd.DataFrame(columns=['rescue_number', 'gender', 'age', 'accompanied',
                                        'accompanied_by_who', 'pregnant', 'country'])
    return df_form


@click.command()
def main():
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    df = get_kobo_data()

    download_data('messages-sent.csv', 'messages-sent.csv')
    df_historical = pd.read_csv('messages-sent.csv')

    df_to_send = df[~df['_uuid'].isin(df_historical['_uuid'])]
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    df_message_text = pd.read_excel('../data/message-text.xlsx')

    for ix, row in df_to_send.iterrows():

        name = row['name']
        lang = row['language']
        phone = row['telephone']

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

    df_historical = df_historical.append(df_to_send, ignore_index=True)
    df_historical.to_csv('messages-sent.csv', index=False)
    upload_data('messages-sent.csv', 'messages-sent.csv')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)


if __name__ == "__main__":
    main()
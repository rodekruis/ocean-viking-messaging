import datetime
import requests
import pandas as pd
import os
from dotenv import load_dotenv
import click
import json
import logging
import numpy as np
from googleapiclient.discovery import build
from google.oauth2 import service_account
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG, filename='ex.log')
# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
# load credentials
load_dotenv(dotenv_path="../../../credentials/.env")


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
        df_form = pd.DataFrame(columns=['bracelet_number',
                                        'name',
                                        'recipient_name',
                                        'family_connection',
                                        'telephone',
                                        'message_status'
                                        ]
                               )
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

    # get rotation info
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SAMPLE_SPREADSHEET_ID = '1L-d0lT2s7QjxlXbvYkcBWdSPFkKsYEtD52J_H4VK8dA'
    SAMPLE_RANGE_NAME = 'Rotations!A:C'
    sa_file = '../../../google-service-account-hspatsea-ocean-viking.json'
    creds = service_account.Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])
    # Create dataframe of rotations
    df_rotations = pd.DataFrame.from_records(values[1:], columns=values[0])
    df_rotations['Start date'] = pd.to_datetime(df_rotations['Start date'], dayfirst=True)
    df_rotations['End date'] = pd.to_datetime(df_rotations['End date'], dayfirst=True)
    df_rotations['Rotation No'] = df_rotations['Rotation No'].astype(float)
    rotation_no = max(df_rotations['Rotation No'])
    start_date_ = datetime.date.today()
    end_date_ = datetime.date.today()

    # Get Kobo data
    df_to_send = get_kobo_data()

    if df_to_send.empty:
        return

    # Filter out data of current rotation
    df_to_send['_submission_time'] = pd.to_datetime(df_to_send['_submission_time'])

    for ix, row in df_rotations.iterrows():
        if row['Start date'] <= pd.to_datetime(datetime.date.today()) <= row['End date']:
            rotation_no = row['Rotation No']
            start_date_ = row['Start date']
            end_date_ = row['End date']

    df_to_send = df_to_send[(df_to_send['_submission_time'] >= start_date_) &
                            (df_to_send['_submission_time'] <= end_date_)]

    # Create Salamat info sheet
    logging.info(f"Processing {len(df_to_send)} kobo submissions")

    columns_to_keep = ['bracelet_number',
                       'name',
                       'name_recipient_1',
                       'family_connection_1',
                       'family_connection_other_1',
                       'telephone_1',
                       'message_status',
                       '_id']

    for col in df_to_send.columns:
        if col not in columns_to_keep:
            df_to_send = df_to_send.drop(columns=[col])

    # Get new entries
    df_to_send = df_to_send[df_to_send['message_status'] == 'new']

    # Determine family connections
    if 'family_connection_other_1' in df_to_send.columns:
        df_to_send['family_connection_1'] = np.where(
            df_to_send['family_connection_1'] == 'other',
            df_to_send['family_connection_other_1'],
            df_to_send['family_connection_1']
        )

        df_to_send = df_to_send.drop(columns=['family_connection_other_1'])

    # Update message status
    for ix, row in df_to_send.iterrows():
        submission_id = row['_id']
        update_kobo_data(submission_id, 'message_status', 'processed')

    df_to_send = df_to_send.drop(columns=['message_status', '_id'])

    # Save Salamat sheet
    df_to_send.to_excel(f'../../../Salamat_r{rotation_no}_{datetime.date.today()}.xlsx', index=False)

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

if __name__ == "__main__":
    main()
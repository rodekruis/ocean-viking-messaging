# ocean-viking-messaging
Help rescued people inform their loved ones that they're safe and well. 

Developed for the [rescue ship "Ocean Viking"](https://sosmediterranee.com/about-us/) in support of the [HSP@Sea operation](https://go.ifrc.org/emergencies/5425).

## Description

Synopsis: a [dockerized](https://www.docker.com/) [python app](https://packaging.python.org/en/latest/tutorials/packaging-projects/) that connects [Kobo](https://www.kobotoolbox.org/) (data collection tool) and [Twilio](https://www.twilio.com/) (messaging service).

Worflow: a kobo form registers the name of the rescued person, the number that he/she wants to contact and his/her preferred language. When the kobo form is uploaded, an SMS is automatically sent through Twilio to the input number, in the preferred language, informing that the person has been rescued and is alive.

## Setup

1. [Create an account on Kobo](https://kf.kobotoolbox.org/accounts/register/#/)
2. Set up the form in Kobo. It should contain the fields 'name', 'telephone' and 'language'. See an example [here](https://docs.google.com/spreadsheets/d/1LVxKnWFMr_x7DczDL-wvKCPbntnZ1tjx/edit?usp=sharing&ouid=110480065025740210638&rtpof=true&sd=true).
3. [Create an account on Twilio](https://www.twilio.com/try-twilio)
4. [Set up a Twilio Messaging Service](https://www.twilio.com/docs/sms/quickstart/python)
5. Add the Kobo and Twilio credentials in credentials/.env
6. Deploy the docker image, e.g. [using Azure Logic App](https://docs.google.com/document/d/182aQPVRZkXifHDNjmE66tj5L1l4IvAt99rxBzpmISPU/edit?usp=sharing)

Optional: the message and the language can be customized in data/message-text.xlsx

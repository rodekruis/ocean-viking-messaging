# ocean-viking-messaging
This system offers a simple way for rescued people to inform their loved ones that they're safe and well. Developed for the [rescue ship "Ocean Viking"](https://sosmediterranee.com/about-us/) in support of the [HSP@Sea operation](https://go.ifrc.org/emergencies/5425).

Based on [Kobo](https://www.kobotoolbox.org/) and [Twilio](https://www.twilio.com/).

## Description

A kobo form registers the name of the rescued person, the number that he/she wants to contact and his/her preferred language. When the kobo form is uploaded, an SMS is automatically sent to the input number, in the preferred language, informing that the person has been rescued and is alive.

## Setup

1. [Create an account on Kobo](https://kf.kobotoolbox.org/accounts/register/#/)
2. Set up the form in Kobo. It should contain the fields 'name', 'telephone' and 'language'
3. [Create an account on Twilio](https://www.twilio.com/try-twilio)
4. [Set up a Twilio Messaging Service](https://www.twilio.com/docs/sms/quickstart/python)
5. Add the Kobo and Twilio credentials in credentials/.env
6. Deploy the docker image, e.g. [using Azure Logic App](https://docs.google.com/document/d/182aQPVRZkXifHDNjmE66tj5L1l4IvAt99rxBzpmISPU/edit?usp=sharing)

Optional: the message and the language can be customized in data/message-text.xlsx

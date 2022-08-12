# ocean-viking-salamat
Help rescued people inform their loved ones that they're safe and well. 

Developed for the [rescue ship "Ocean Viking"](https://sosmediterranee.com/about-us/) in support of the [HSP@Sea operation](https://go.ifrc.org/emergencies/5425).

## Description

Synopsis: a [python script](https://packaging.python.org/en/latest/tutorials/packaging-projects/) that gets data from [Kobo](https://www.kobotoolbox.org/) (data collection tool) and transform them in the ICRC Salamat format.

Worflow: a kobo form registers the name of the rescued person, the number that he/she wants to contact and his/her preferred language. After all kobo forms are uploaded, run the script, get the output and send to ICRC.

## Setup

1. [Create an account on Kobo](https://kf.kobotoolbox.org/accounts/register/#/)
2. Set up the form in Kobo. It should contain the fields 'name', 'telephone' and 'language'. See an example [here](https://docs.google.com/spreadsheets/d/1LVxKnWFMr_x7DczDL-wvKCPbntnZ1tjx/edit?usp=sharing&ouid=110480065025740210638&rtpof=true&sd=true).
3. Add the Kobo credentials in credentials/.env
4. Run the script

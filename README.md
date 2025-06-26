# vlbg_wasser
Unofficial/Inoffizielle VOWIS Add-On. I apologize for the English - I want to get this done and my German is _slow_. I will translate it at some point (or you can help 😘)

This project started with the question "where can I go swimming" and me being too lazy to open the [Water Map](https://vowis.vorarlberg.at/stationswrapper/abfluss) on my phone to check which river had a good balance of distance vs being too cold. I hope to eventually expand to groundwater (for example, to control sprinklers or [pool filling](https://vorarlberg.orf.at/stories/3303202/) based on supply) but that's a #TODO.




# Disclaimer and Gotcha's
Quellennachweis „Amt der Vorarlberger Landesregierung, Abt. VIId – Wasserwirtschaft“

Seite https://www.vorarlberg.at/abfluss

Es wird keinerlei Gewährleistung für die zur Verfügung gestellten Messwerte übernommen. Alle Daten sind ungeprüft und haben den Status von Rohdaten.

Wir weisen  ausdrücklich darauf hin, dass wir hinsichtlich  Verfügbarkeit, Performance oder Kontinuität des Dienstes keine Garantie übernehmen können.

## Data Accuracy
As the warning above states, this is raw data. While the data from the API includes timestamps, Home Assistant cannot use them; according to Petro it's [not possible](https://community.home-assistant.io/t/rest-sensor-with-timestamp-and-value/535999/9) to write a timestamp. The VOWIS API updates sensor values _roughly_ every 5 minutes, starting on the hour, and needs _roughly_ 10 minutes to post to the API. There will be considerable shift between measurements, and HA ingesting the data:

![timeline shift](/doc/img/timeframe.drawio.svg "Time is a magical thing")

All that to say - please do not use this data for reference/as reasearch! If you need the bulk data, check the website, they have a lot of cool tools (or contact them).
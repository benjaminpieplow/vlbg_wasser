# Right, what's all this then?
The best practice seems to be isolating the part of your code that polls the API, from that which returns data. The VOWIS API is pretty basic, it has 3 useful functions.

## `get_river_data`(station_id: str, measurement_type: str)
Accepts a station id, and "Messwerte" (measurement type). Doing some light poking, these are the potential values I got (and the data they returned):
- w - Water Depth
- wt - Water Temperature
- q - Water Flow Rate
- lt - (no data)
- n - (400 error)
- n5 - (no data)
- lf - (no data)
- gws_t_mw - (no data)

Note that not all stations support the same parameters; I've tried mapping them but aired on the side of "get it working".

Returns a JSON dump of https://vowis.vorarlberg.at/api/messwerte/w?hzbnr=200014 (station_id: "200014", measurement_type: "w"):

```
{
  "Stationen": {
    "200014": {
      "Parameter": "W",
      "Einheit": "cm",
      "Zeit": "MEZ",
      "Messwerte": {
        "2025-06-25T22:00:00": 627.8,
        "2025-06-25T22:05:00": 627.8,
        "2025-06-25T22:10:00": 627.8,
        "2025-06-25T22:15:00": 627.8,
        [ output removed ]
        "2025-06-26T21:15:00": 632.5,
        "2025-06-26T21:20:00": 632.4,
        "2025-06-26T21:25:00": 632.2
      }
    }
  }
}
```

## `get_bodensee_data()`
This one is much simpler, as there is only one bodensee; it just returns a JSON dump of https://vowis.vorarlberg.at/api/see:

```
[
  {
    "pegelnullpunkt": 392.14,
    "pnpGueltigSeit": "2018-12-13T00:00:00",
    "hW2": 460,
    "hW10": 512,
    "hW20": 531,
    "hW30": 540,
    "hW50": 553,
    "hW100": 568,
    "hW2abs": 396.74,
    "hW10abs": 397.26,
    "hW20abs": 397.45,
    "hW30abs": 397.54,
    "hW50abs": 397.67,
    "hW100abs": 397.82,
    "wMessungSeit": "1855-01-01T00:00:00",
    "wtMessungSeit": "1895-01-01T00:00:00",
    "luftfeuchte": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 76.6
    },
    "lufttemperatur": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 21.5
    },
    "wasserstand": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 356.8
    },
    "wTemperatur": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 24.4
    },
    "wtMilli05": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 24.7
    },
    "wtMilli25": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 24.7
    },
    "windgeschwindigkeit": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 4.8
    },
    "windrichtung": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 161.5
    },
    "windboe": {
      "datum": "2025-06-26T16:00:00Z",
      "wert": 8.8
    },
    "seeArchiv": [
      {
        "datum": "2025-06-26T00:00:00",
        "w": 356,
        "wtHafen": 24.9,
        "wtMilli05": 24.9,
        "wtMilli25": 24.2,
        "tag": 26,
        "monat": 6,
        "ZRBereich": "1864 - 2024",
        "Min": 335,
        "Mit": 431.43125,
        "Max": 563,
        "tagMonat": "26.06."
      },
      {
        "datum": "2025-06-25T00:00:00",
        "w": 357,
        "wtHafen": 25,
        "wtMilli05": 25.2,
        "wtMilli25": 24.5,
        "tag": 25,
        "monat": 6,
        "ZRBereich": "1864 - 2024",
        "Min": 335,
        "Mit": 431.19375,
        "Max": 563,
        "tagMonat": "25.06."
      },
      {
        "datum": "2025-06-19T00:00:00",
        "w": 368,
        "wtHafen": 22,
        "wtMilli05": 22.7,
        "wtMilli25": 22,
        "tag": 19,
        "monat": 6,
        "ZRBereich": "1864 - 2024",
        "Min": 331,
        "Mit": 427.3,
        "Max": 568,
        "tagMonat": "19.06."
      },
      {
        "datum": "2024-06-26T00:00:00",
        "w": 507,
        "wtHafen": 19.6,
        "wtMilli05": 20.7,
        "wtMilli25": 18.1,
        "tag": 26,
        "monat": 6,
        "ZRBereich": "1864 - 2024",
        "Min": 335,
        "Mit": 431.43125,
        "Max": 563,
        "tagMonat": "26.06."
      }
    ],
    "history": null,
    "nnw": {
      "datum": "2006-02-14T23:00:00Z",
      "wert": 231
    },
    "hhw": {
      "datum": "1890-09-02T23:00:00Z",
      "wert": 581
    },
    "flaechennR_1_BIS_8_ORDNG_TXT": "Bodensee",
    "Hzbnr": "200337",
    "Name": "Bregenz (Seepegel), 200337",
    "rechtswert": -44116,
    "hochwert": 263409,
    "Flussgebiet": null,
    "hoehe": 0,
    "Betreiber": "Wasserwirtschaft Vorarlberg"
  }
]
```

Yes, I know, it's an array. Yes, that's [allowed](https://stackoverflow.com/questions/5034444/can-json-start-with). Yes, I _really_ hope they don't add more elements, because I _really_ think that will break my code :)

## `test_connection()`
Calls `get_bodensee_data()` and returns `True` if it worked.
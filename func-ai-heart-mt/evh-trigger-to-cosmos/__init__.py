import logging
import json
import numpy as np
import requests
import azure.functions as func


# def main(eventMobile: func.EventHubEvent, cosmosECG: func.Out[func.DocumentList]): "Esto se utiliza cuando quieres insertar más de un documento en la función// func.DocumentList // "
def main(eventMobile: func.EventHubEvent, cosmosECG: func.Out[func.Document]):

    event_data = eventMobile.get_body().decode("utf-8")
    logging.info('Python EventHub trigger processed an event: %s', event_data)

    event_data_json = json.loads(
        eventMobile.get_body().decode("utf-8").replace("'", '"'))

    subECGclean = formatDataECG(event_data_json)
    logging.info(type(subECGclean))
    results = obtainResultsIA(subECGclean)

    temp = {}
    temp["userID"] = event_data_json["user"]
    temp["readDate"] = event_data_json["readDate"]
    temp["data"] = []

    countNSR = 0
    countARR = 0
    countCHF = 0

    for i in range(len(subECGclean)):
        if results[i] == 'NSR':
            countNSR = countNSR + 1
        if results[i] == 'ARR':
            countARR = countARR + 1
        if results[i] == 'CHF':
            countCHF = countCHF + 1

        temp["data"].append({
            "dataECG": subECGclean[i].tolist(),
            "order": i+1,
            "result": results[i],
            "labelResult": 'Normal' if (results[i] == 'NSR') else 'Anormal'
        })

    temp["countNSR"] = countNSR
    temp["countARR"] = countARR
    temp["countCHF"] = countCHF
    temp["countWindow"] = len(results)

    # Plan 1
    temp = json.dumps(temp)
    cosmosECG.set(func.Document.from_json(temp))

    # Plan 2
    # messages.append(func.Document.from_dict(temp))
    # cosmosECG.set(messages)

    # logging.info("CosmosDB updated!; Value: %s", temp)


def formatDataECG(event_data_json):

    DIV = 256
    # logging.info(type(event_data_json))
    ecg = event_data_json["listDataECG"]
    ecg = [data for data in ecg]
    ecg = ecg[584:]
    # logging.info(len(ecg))

    subECGraw = np.array([np.array(ecg[i:i+DIV])
                         for i in range(0, len(ecg), DIV)])

    subECGclean = []

    for i in range(len(subECGraw)):
        if len(subECGraw[i]) == DIV:
            subECGclean.append(subECGraw[i])

    return subECGclean


def obtainResultsIA(subECGclean):

    subECGFormat = []

    for i in range(len(subECGclean)):
        subECGFormat.append(subECGclean[i].tolist())

    url = "http://8d516c58-5deb-420a-b634-adbe3d3fa449.southcentralus.azurecontainer.io/score"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {}
    data["data"] = {}
    data["data"]["listECG"] = subECGFormat

    logging.info("Aqui estoy")
    logging.info(type(subECGclean[0]))

    response = requests.post(url, headers=headers, data=json.dumps(data))

    transdict = {0: 'ARR',
                 1: 'CHF',
                 2: 'NSR'}

    print(response.content)

    results = json.loads(response.content)["results"]

    print(type(results))
    print(results)

    results = [transdict[item] for item in results]

    return results

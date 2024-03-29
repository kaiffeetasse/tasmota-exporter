import time
from dotenv import load_dotenv
import requests
from prometheus_client import Gauge, start_http_server
import os
import logging
from bs4 import BeautifulSoup


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

EXPORT_INTERVAL_SECONDS = int(os.environ.get("EXPORT_INTERVAL_SECONDS"))
TASMOTA_URL = os.environ.get("TASMOTA_URL")
ERROR_SLEEP_MINUTES = 1

start_http_server(8001)


def get_metrics():
    while True:

        try:

            metrics = []

            url = TASMOTA_URL + "/?m=1"

            response = requests.request("GET", url)
            soup = BeautifulSoup(response.text, features="html.parser")
            text = soup.get_text()

            metrics_text = text.split("{e}{s}")[1:]

            for metric in metrics_text:
                metric = metric \
                    .replace("{t}{s}", "") \
                    .replace("{e}", "") \
                    .strip()

                metric_splitted = metric.split("{m}")

                metric_key = metric_splitted[0].strip()
                metric_value_with_unit = metric_splitted[1].strip()
                metric_value = metric_value_with_unit.split(" ")[0].strip()
                metric_unit = ""

                try:
                    metric_unit = metric_value_with_unit.split(" ")[1]
                except:
                    pass

                # print(metric_key + " = " + metric_value + " " + metric_unit)

                metrics.append(
                    {
                        'metric_key': metric_key,
                        'metric_value': metric_value,
                        'metric_unit': metric_unit
                    }
                )

            return metrics

        except Exception as e:
            logger.error("Error while getting metrics:")
            logger.exception(e)
            logger.info("sleeping for " + str(ERROR_SLEEP_MINUTES) + " minutes")
            time.sleep(ERROR_SLEEP_MINUTES)


def get_formatted_metric_key(metric_key):
    return metric_key \
        .lower() \
        .replace("ü", "ue") \
        .replace("ö", "oe") \
        .replace("ä", "ae") \
        .replace(" ", "_") \
        .replace("ß", "ss")


def export_metrics():
    metrics = get_metrics()

    gauges = {}

    for metric in metrics:
        metric_key_formatted = get_formatted_metric_key(metric['metric_key'])
        help_text = metric['metric_key']

        metric_unit = metric['metric_unit']

        if metric_unit != "":
            help_text = help_text + " in " + metric_unit

        metric_gauge = Gauge('tasmota_' + metric_key_formatted, help_text)
        gauges[metric_key_formatted] = metric_gauge

    while True:
        try:

            for metric in metrics:
                metric_key_formatted = get_formatted_metric_key(metric['metric_key'])

                gauge = gauges[metric_key_formatted]

                metric_value = metric['metric_value']

                gauge.set(metric_value)

            metrics = get_metrics()

        except Exception as e:
            logger.exception(e)

        time.sleep(EXPORT_INTERVAL_SECONDS)


if __name__ == '__main__':
    export_metrics()

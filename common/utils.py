import json
import pprint
from datetime import datetime


def read_config(path_to_file):
    # TODO: catch exceptions
    with open(path_to_file) as jsonin:
        loaded_config = json.loads(jsonin.read())

    return loaded_config


pp = pprint.PrettyPrinter()


def pretty_print(data):
    pp.pprint(data)


def pretty_print_into_string(data):
    return pprint.pformat(data)


DATEFORMAT = "%Y-%m-%d"


def datetime_to_date_str(dt):
    return dt.strftime(DATEFORMAT)


def date_str_to_datetime(str):
    return datetime.strptime(str, DATEFORMAT)


def dates_to_timeframe_str(start_date, end_date):
    return start_date + " - " + end_date


def timeframe_str_to_timeframe(timeframe_str):
    return timeframe_str.split(" - ")


def timeframe_str_to_datetime(timeframe_str):
    timeframe = timeframe_str_to_timeframe(timeframe_str)
    start_date_obj = date_str_to_datetime(timeframe[0])
    end_date_obj = date_str_to_datetime(timeframe[1])

    return start_date_obj, end_date_obj

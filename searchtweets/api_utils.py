# -*- coding: utf-8 -*-
# Copyright 2018 Twitter, Inc.
# Licensed under the MIT License
# https://opensource.org/licenses/MIT
"""
Module containing the various functions that are used for API calls,
rule generation, and related.
"""

import re
import datetime
import logging
try:
    import ujson as json
except ImportError:
    import json

__all__ = ["gen_request_parameters", "gen_params_from_config",
           "infer_endpoint", "convert_utc_time",
           "validate_count_api", "change_to_count_endpoint"]

logger = logging.getLogger(__name__)


#TODO: NEED TO CONVERT TO ISO FROM GNIP

def convert_utc_time(datetime_str):
    """
    Handles datetime argument conversion to the Labs API format, which is
    `YYYY-MM-DDTHH:mm:ssZ`.
    Flexible passing of date formats in the following types::

        - YYYYmmDDHHMM
        - YYYY-mm-DD
        - YYYY-mm-DD HH:MM
        - YYYY-mm-DDTHH:MM
        #Coming soon:
        - 3d
        -12h

    Args:
        datetime_str (str): valid formats are listed above.

    Returns:
        string of GNIP API formatted date.

    Example:
        >>> from searchtweets.utils import convert_utc_time
        >>> convert_utc_time("201708020000")
        '201708020000'
        >>> convert_utc_time("2017-08-02")
        '201708020000'
        >>> convert_utc_time("2017-08-02 00:00")
        '201708020000'
        >>> convert_utc_time("2017-08-02T00:00")
        '201708020000'
    """
    if not datetime_str:
        return None
    if not set(['-', ':']) & set(datetime_str):
        _date = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M")
    else:
        try:
            if "T" in datetime_str:
                # command line with 'T'
                datetime_str = datetime_str.replace('T', ' ')
            _date = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            _date = datetime.datetime.strptime(datetime_str, "%Y-%m-%d")
    return _date.strftime("%Y-%m-%dT%H:%M:%SZ")


def change_to_count_endpoint(endpoint):
    """Utility function to change a normal endpoint to a ``count`` api
    endpoint. Returns the same endpoint if it's already a valid count endpoint.
    Args:
        endpoint (str): your api endpoint

    Returns:
        str: the modified endpoint for a count endpoint.
    """

    tokens = filter(lambda x: x != '', re.split("[/:]", endpoint))
    filt_tokens = list(filter(lambda x: x != "https", tokens))
    last = filt_tokens[-1].split('.')[0]  # removes .json on the endpoint
    filt_tokens[-1] = last  # changes from *.json -> '' for changing input
    if last == 'counts':
        return endpoint
    else:
        return "https://" + '/'.join(filt_tokens) + '/' + "counts.json"


def gen_request_parameters(query, results_per_call=None,
                           start_time=None, end_time=None, since_id=None, until_id=None,
                           stringify=True):

    """
    Generates the dict or json payload for a PowerTrack rule.

    Args:
        query (str): The string version of a powertrack rule,
            e.g., "beyonce has:geo". Accepts multi-line strings
            for ease of entry.
        results_per_call (int): number of tweets or counts returned per API
        call. This maps to the `max_results`` search API parameter.
            Defaults to 100 to reduce API call usage.
        start_time (str or None): Date format as specified by
            `convert_utc_time` for the starting time of your search.
        end_time (str or None): date format as specified by `convert_utc_time`
            for the end time of your search.
        stringify (bool): specifies the return type, `dict`
            or json-formatted `str`.

    Example:

        >>> from searchtweets.utils import gen_request_parameters
        >>> gen_request_parameters("beyonce has:geo",
            ...              from_date="2020-02-18",
            ...              to_date="2020-02-21")
        '{"query":"beyonce has:geo","max_results":100,"start_time":"202002180000","end_time":"202002210000"}'
    """

    query = ' '.join(query.split())  # allows multi-line strings
    payload = {"query": query}
    if results_per_call is not None and isinstance(results_per_call, int) is True:
        payload["max_results"] = results_per_call
    if start_time:
        payload["start_time"] = convert_utc_time(start_time)
    if end_time:
        payload["end_time"] = convert_utc_time(end_time)
    if since_id:
        payload["since_id"] = since_id
    if until_id:
        payload["until_id"] = until_id
    #TODO: Not needed for Labs, but useful for vNext.
    # if count_bucket:
    #     if set(["day", "hour", "minute"]) & set([count_bucket]):
    #         payload["bucket"] = count_bucket
    #         del payload["max_results"]
    #     else:
    #         logger.error("invalid count bucket: provided {}"
    #                      .format(count_bucket))
    #         raise ValueError
    # if tag:
    #     payload["tag"] = tag

    return json.dumps(payload) if stringify else payload


def gen_params_from_config(config_dict):
    """
    Generates parameters for a ResultStream from a dictionary.
    """

    # if config_dict.get("count_bucket"):
    #     logger.warning("change your endpoint to the count endpoint; this is "
    #                    "default behavior when the count bucket "
    #                    "field is defined")
    #     endpoint = change_to_count_endpoint(config_dict.get("endpoint"))
    # else:
    endpoint = config_dict.get("endpoint")


    def intify(arg):
        if not isinstance(arg, int) and arg is not None:
            return int(arg)
        else:
            return arg

    # this parameter comes in as a string when it's parsed
    results_per_call = intify(config_dict.get("results_per_call", None))

    query = gen_request_parameters(query=config_dict["query"],
                            start_time=config_dict.get("start_time", None),
                            end_time=config_dict.get("end_time", None),
                            since_id=config_dict.get("since_id", None),
                            until_id=config_dict.get("until_id", None),
                            results_per_call=results_per_call)
                            #count_bucket=config_dict.get("count_bucket", None))

    _dict = {"endpoint": endpoint,
             "bearer_token": config_dict.get("bearer_token"),
             "extra_headers_dict": config_dict.get("extra_headers_dict",None),
             "request_parameters": query,
             "results_per_file": intify(config_dict.get("results_per_file")),
             "max_tweets": intify(config_dict.get("max_tweets")),
             "max_pages": intify(config_dict.get("max_pages", None))}

    return _dict


def infer_endpoint(request_parameters):
    """
    Infer which endpoint should be used for a given rule payload.
    TODO: Not needed for Labs, but useful for vNext.
    """
    bucket = (request_parameters if isinstance(request_parameters, dict)
              else json.loads(request_parameters)).get("bucket")
    return "counts" if bucket else "search"


def validate_count_api(request_parameters, endpoint):
    """
    Ensures that the counts api is set correctly in a payload.
    TODO: Not needed for Labs, but useful for vNext.
    """
    rule = (request_parameters if isinstance(request_parameters, dict)
            else json.loads(request_parameters))
    bucket = rule.get('bucket')
    counts = set(endpoint.split("/")) & {"counts.json"}
    if len(counts) == 0:
        if bucket is not None:
            msg = ("""There is a count bucket present in your payload,
                   but you are using not using the counts API.
                   Please check your endpoints and try again""")
            logger.error(msg)
            raise ValueError


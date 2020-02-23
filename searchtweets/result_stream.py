# -*- coding: utf-8 -*-
# Copyright 2018 Twitter, Inc.
# Licensed under the MIT License
# https://opensource.org/licenses/MIT
"""
This module contains the request handing and actual API wrapping functionality.

Its core method is the ``ResultStream`` object, which takes the API call
arguments and returns a stream of results to the user.
"""

import time
import re
import logging
import requests
from urllib.parse import urlencode
try:
    import ujson as json
except ImportError:
    import json
from tweet_parser.tweet import Tweet

from .utils import merge_dicts

from .api_utils import infer_endpoint, change_to_count_endpoint

from ._version import VERSION

logger = logging.getLogger(__name__)


def make_session(bearer_token=None, extra_headers_dict=None):
    """Creates a Requests Session for use. Accepts a bearer token
    for Labs.

    Args:
        bearer_token (str): token for a Labs user.
    """

    if bearer_token is None:
        logger.error("No authentication information provided; "
                     "please check your object")
        raise KeyError

    session = requests.Session()
    session.trust_env = False
    headers = {'Accept-encoding': 'gzip',
               'User-Agent': 'twitterdev-search-tweets-python-labs/' + VERSION}
    if bearer_token:
        logger.info("using bearer token for authentication")
        headers['Authorization'] = "Bearer {}".format(bearer_token)
        session.headers = headers

    if extra_headers_dict:
        headers.update(extra_headers_dict) 
    return session

def retry(func):
    """
    Decorator to handle API retries and exceptions. Defaults to three retries.

    Args:
        func (function): function for decoration

    Returns:
        decorated function

    """
    def retried_func(*args, **kwargs):
        max_tries = 3
        tries = 0
        while True:
            try:
                resp = func(*args, **kwargs)

            except requests.exceptions.ConnectionError as exc:
                exc.msg = "Connection error for session; exiting"
                raise exc

            except requests.exceptions.HTTPError as exc:
                exc.msg = "HTTP error for session; exiting"
                raise exc

            if resp.status_code != 200 and tries < max_tries:
                logger.warning("retrying request; current status code: {}"
                               .format(resp.status_code))
                tries += 1
                # mini exponential backoff here.
                time.sleep(tries ** 2)
                continue

            break

        #TODO: Need to update to Labs error messages.
        if resp.status_code != 200:

            if resp.status_code == 429:
                print( "Request rate limit hit...")
            else:
                print(f"Error code: {resp.status_code}")
                error_message = resp.json()["error"]["message"]
                logger.error("HTTP Error code: {}: {}".format(resp.status_code, error_message))
                logger.error("Rule payload: {}".format(kwargs["request_parameters"]))
                raise requests.exceptions.HTTPError

        return resp

    return retried_func


@retry
def request(session, url, request_parameters, **kwargs):
    """
    Executes a request with the given payload and arguments.

    Args:
        session (requests.Session): the valid session object
        url (str): Valid API endpoint
        request_parameters (str or dict): rule package for the POST. If you pass a
            dictionary, it will be converted into JSON.
    """

    if isinstance(request_parameters, dict):
        request_parameters = json.dumps(request_parameters)
    logger.debug("sending request")
    #result = session.post(url, data=request_parameters, **kwargs)
    request_json = json.loads(request_parameters)


    #HANDLE LABS REQUEST PARAMETERS --> GET URL
    #print(urlencode(request_json))

    #TODO: new Labs-specific code in support of GET requests. Will need to URL encode too.
    url = f"{url}?query={request_json['query']}"

    result = session.get(url, **kwargs)
    return result


class ResultStream:
    """
    Class to represent an API query that handles two major functionality
    pieces: wrapping metadata around a specific API call and automatic
    pagination of results.

    Args:
        bearer_token (str): bearer token for premium users
        endpoint (str): API endpoint; see your console at developer.twitter.com
        request_parameters (json or dict): payload for the post request
        max_tweets (int): max number results that will be returned from this
        instance. Note that this can be slightly lower than the total returned
        from the API call  - e.g., setting ``max_tweets = 10`` would return
        ten results, but an API call will return at minimum 100 results by defaule.
        tweetify (bool): If you are grabbing tweets and not counts, use the
            tweet parser library to convert each raw tweet package to a Tweet
            with lazy properties.
        max_requests (int): A hard cutoff for the number of API calls this
        instance will make. Good for testing in sandbox premium environments. 
        extra_headers_dict (dict): custom headers to add


    Example:
        >>> rs = ResultStream(**search_args, request_parameters=rule, max_pages=1)
        >>> results = list(rs.stream())

    """
    # leaving this here to have an API call counter for ALL objects in your
    # session, helping with usage of the convenience functions in the library.
    session_request_counter = 0

    def __init__(self, endpoint, request_parameters, bearer_token=None, extra_headers_dict=None, max_tweets=500,
                 tweetify=True, max_requests=None, **kwargs):

        self.bearer_token = bearer_token
        self.extra_headers_dict = extra_headers_dict
        if isinstance(request_parameters, str):
            request_parameters = json.loads(request_parameters)
        self.request_parameters = request_parameters
        self.tweetify = tweetify
        # magic number of max tweets if you pass a non_int
        self.max_tweets = (max_tweets if isinstance(max_tweets, int)
                            else 10 ** 15)

        self.total_results = 0
        self.n_requests = 0
        self.session = None
        self.current_tweets = None
        self.next_token = None
        self.stream_started = False
        self._tweet_func = Tweet if tweetify else lambda x: x
        # magic number of requests!
        self.max_requests = (max_requests if max_requests is not None
                             else 10 ** 9)
        self.endpoint = (change_to_count_endpoint(endpoint)
                         if infer_endpoint(request_parameters) == "counts"
                         else endpoint)
        #TODO: Labs does not support counts.
        # validate_count_api(self.request_parameters, self.endpoint)

    def stream(self):
        """
        Main entry point for the data from the API. Will automatically paginate
        through the results via the ``next`` token and return up to ``max_tweets``
        tweets or up to ``max_requests`` API calls, whichever is lower.

        Usage:
            >>> result_stream = ResultStream(**kwargs)
            >>> stream = result_stream.stream()
            >>> results = list(stream)
            >>> # or for faster usage...
            >>> results = list(ResultStream(**kwargs).stream())
        """
        self.init_session()

        self.execute_request()
        self.stream_started = True
        while True:
            for tweet in self.current_tweets:
                if self.total_results >= self.max_tweets:
                    break
                yield self._tweet_func(tweet)
                self.total_results += 1

            if self.next_token and self.total_results < self.max_tweets and self.n_requests <= self.max_requests:
                self.request_parameters = merge_dicts(self.request_parameters,
                                                {"next_token": self.next_token})
                logger.info("paging; total requests read so far: {}"
                            .format(self.n_requests))
                self.execute_request()
            else:
                break
        logger.info("ending stream at {} tweets".format(self.total_results))
        self.current_tweets = None
        self.session.close()

    def init_session(self):
        """
        Defines a session object for passing requests.
        """
        if self.session:
            self.session.close()
        self.session = make_session(self.bearer_token,
                                    self.extra_headers_dict)

    # def check_counts(self):
    #     """
    #     Disables tweet parsing if the count API is used.
    #     """
    #     if "counts" in re.split("[/.]", self.endpoint):
    #         logger.info("disabling tweet parsing due to counts API usage")
    #         self._tweet_func = lambda x: x

    def execute_request(self):
        """
        Sends the request to the API and parses the json response.
        Makes some assumptions about the session length and sets the presence
        of a "next" token.
        """
        if self.n_requests % 20 == 0 and self.n_requests > 1:
            logger.info("refreshing session")
            self.init_session()

        resp = request(session=self.session,
                       url=self.endpoint,
                       request_parameters=self.request_parameters)
        self.n_requests += 1
        ResultStream.session_request_counter += 1
        try:
            resp = json.loads(resp.content.decode(resp.encoding))

            #TODO: Migration. Labs details/changes.
            meta = resp.get("meta", None)
            self.next_token = meta.get("next_token", None)
            self.current_tweets = resp["data"]

        except:
            print("Error parsing content as JSON.")



    def __repr__(self):
        repr_keys = ["endpoint", "request_parameters",
                     "tweetify", "max_tweets"]
        str_ = json.dumps(dict([(k, self.__dict__.get(k)) for k in repr_keys]),
                          indent=4)
        str_ = "ResultStream: \n\t" + str_
        return str_


def collect_results(query, max_tweets=500, result_stream_args=None):
    """
    Utility function to quickly get a list of tweets from a ``ResultStream``
    without keeping the object around. Requires your args to be configured
    prior to using.

    Args:
        query (str): valid powertrack rule for your account, preferably
        generated by the `gen_request_parameters` function.
        max_tweets (int): maximum number of tweets or counts to return from
        the API / underlying ``ResultStream`` object.
        result_stream_args (dict): configuration dict that has connection
        information for a ``ResultStream`` object.

    Returns:
        list of results

    Example:
        >>> from searchtweets import collect_results
        >>> tweets = collect_results(query,
                                     max_tweets=500,
                                     result_stream_args=search_args)

    """
    if result_stream_args is None:
        logger.error("This function requires a configuration dict for the "
                     "inner ResultStream object.")
        raise KeyError

    rs = ResultStream(request_parameters=query,
                      max_tweets=max_tweets,
                      **result_stream_args)
    return list(rs.stream())

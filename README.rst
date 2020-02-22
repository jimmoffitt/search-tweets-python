TODO:
[] https://twitterdev.github.io/search-tweets-python-labs
[]


Python Twitter Search API
=========================

This project serves as a wrapper for the `Twitter Labs recent search
APIs <https://developer.twitter.com/en/docs/labs/recent-search/>`__,
providing a command-line utility and a Python library.

This is a fork of the premium/enterprise search client at https://github.com/twitterdev/search-tweets-python


Features
========

-  Supports Labs recent search, v2.
-  Command-line utility is pipeable to other tools (e.g., ``jq``).
-  Automatically handles pagination of search results with specifiable
   limits
-  Delivers a stream of data to the user for low in-memory requirements
-  Handles OAuth 2 authentication.
-  Flexible usage within a python program
-  Compatible with our group's `Tweet
   Parser <https://github.com/twitterdev/tweet_parser>`__ for rapid
   extraction of relevant data fields from each tweet payload
-  Supports the Search Counts endpoint, which can reduce API call usage
   and provide rapid insights if you only need Tweet volumes and not
   Tweet payloads

Installation
============

The ``searchtweets`` library is on Pypi:

.. code:: bash

   pip install searchtweets

Or you can install the development version locally via

.. code:: bash

   git clone https://github.com/twitterdev/search-tweets-python
   cd search-tweets-python
   pip install -e .

--------------


------------------------------
See https://github.com/twitterdev/search-tweets-python for more documentation.

Below are excerpts of details that have changed:



Credential Handling
===================



Labs clients will require the ``bearer_token`` and ``endpoint``
fields; 

For Labs search, we are using app-only authentication and
the bearer tokens are not delivered with an expiration time. You can
provide either: - your application key and secret (the library will
handle bearer-token authentication) - a bearer token that you get
yourself

Many developers might find providing your application key and secret
more straightforward and letting this library manage your bearer token
generation for you. Please see
`here <https://developer.twitter.com/en/docs/basics/authentication/overview/application-only>`__
for an overview of the OAuth2 authentication method.

We support both YAML-file based methods and environment variables for
storing credentials, and provide flexible handling with sensible
defaults.

YAML method
-----------

For premium customers, the simplest credential file should look like
this:

.. code:: yaml

   search_tweets_api:
     endpoint: <FULL_URL_OF_ENDPOINT>
     consumer_key: <CONSUMER_KEY>
     consumer_secret: <CONSUMER_SECRET>

For enterprise customers, the simplest credential file should look like
this:

.. code:: yaml

   search_tweets_api:
     endpoint: <FULL_URL_OF_ENDPOINT>
     username: <USERNAME>
     password: <PW>

By default, this library expects this file at
``"~/.twitter_keys.yaml"``, but you can pass the relevant location as
needed, either with the ``--credential-file`` flag for the command-line
app or as demonstrated below in a Python program.

Both above examples require no special command-line arguments or
in-program arguments. The credential parsing methods, unless otherwise
specified, will look for a YAML key called ``search_tweets_api``.


Environment Variables
---------------------

If you want or need to pass credentials via environment variables, you
can set the appropriate variables for your product of the following:

::

   export SEARCHTWEETS_ENDPOINT=
   export SEARCHTWEETS_BEARER_TOKEN=
   export SEARCHTWEETS_CONSUMER_KEY=
   export SEARCHTWEETS_CONSUMER_SECRET=



Using the Comand Line Application
=================================

The library includes an application, ``search_tweets.py``, that provides
rapid access to Tweets. When you use ``pip`` to install this package,
``search_tweets.py`` is installed globally. The file is located in the
``tools/`` directory for those who want to run it locally.

Note that the ``--results-per-call`` flag specifies an argument to the
API ( ``max_results``, results returned per CALL), not as a hard max to
number of results returned from this program. The argument
``--max-results`` defines the maximum number of results to return from a
given call. All examples assume that your credentials are set up
correctly in the default location - ``.twitter_keys.yaml`` or in
environment variables.

**Stream json results to stdout without saving**

.. code:: bash

   search_tweets.py \
     --max-tweets 1000 \
     --results-per-call 100 \
     --query "beyonce has:hashtags" \
     --print-stream

**Stream json results to stdout and save to a file**

.. code:: bash

   search_tweets.py \
     --max-tweets 1000 \
     --results-per-call 100 \
     --query "beyonce has:hashtags" \
     --filename-prefix beyonce_geo \
     --print-stream

**Save to file without output**

.. code:: bash

   search_tweets.py \
     --max-tweets 1000 \
     --results-per-call 100 \
     --query "beyonce has:hashtags" \
     --filename-prefix beyonce_geo \
     --no-print-stream

One or more custom headers can be specified from the command line, using
the ``--extra-headers`` argument and a JSON-formatted string
representing a dictionary of extra headers:

.. code:: bash

   search_tweets.py \
     --query "beyonce has:hashtags" \
     --extra-headers '{"<MY_HEADER_KEY>":"<MY_HEADER_VALUE>"}'

Options can be passed via a configuration file (either ini or YAML).
Example files can be found in the ``tools/api_config_example.config`` or
``./tools/api_yaml_example.yaml`` files, which might look like this:

.. code:: bash

   [search_rules]
   start_time = 2017-06-01
   end_time = 2017-09-01
   query = beyonce has:geo

   [search_params]
   results_per_call = 100
   max_tweets = 5000

   [output_params]
   save_file = True
   filename_prefix = beyonce
   results_per_file = 100000

Or this:

.. code:: yaml

   search_rules:
       start-time: 2017-06-01
       end-time: 2017-09-01 01:01
       query: kanye

   search_params:
       results-per-call: 500
       max-results: 500

   output_params:
       save_file: True
       filename_prefix: kanye
       results_per_file: 10000000

Custom headers can be specified in a config file, under a specific
credentials key:

.. code:: yaml

   search_tweets_api:
     endpoint: <FULL_URL_OF_ENDPOINT>
     extra_headers:
       <MY_HEADER_KEY>: <MY_HEADER_VALUE>

When using a config file in conjunction with the command-line utility,
you need to specify your config file via the ``--config-file``
parameter. Additional command-line arguments will either be *added* to
the config file args or **overwrite** the config file args if both are
specified and present.

Example:

::

   search_tweets.py \
     --config-file myapiconfig.config \
     --no-print-stream

--------------

Full options are listed below:

::

   $ search_tweets.py -h
   usage: search_tweets.py [-h] [--credential-file CREDENTIAL_FILE]
                         [--credential-file-key CREDENTIAL_YAML_KEY]
                         [--env-overwrite ENV_OVERWRITE]
                         [--config-file CONFIG_FILENAME]
                         [--start-time START_TIME] [--end-time END_TIME]
                         [--query QUERY]
                         [--results-per-call RESULTS_PER_CALL]
                         [--max-tweets MAX_TWEETS] [--max-pages MAX_PAGES]
                         [--results-per-file RESULTS_PER_FILE]
                         [--filename-prefix FILENAME_PREFIX]
                         [--no-print-stream] [--print-stream]
                         [--extra-headers EXTRA_HEADERS] [--debug]

   optional arguments:
     -h, --help            show this help message and exit
     --credential-file CREDENTIAL_FILE
                           Location of the yaml file used to hold your
                           credentials.
     --credential-file-key CREDENTIAL_YAML_KEY
                           the key in the credential file used for this session's
                           credentials. Defaults to search_tweets_api
     --env-overwrite ENV_OVERWRITE
                           Overwrite YAML-parsed credentials with any set
                           environment variables. See API docs or readme for
                           details.
     --config-file CONFIG_FILENAME
                           configuration file with all parameters. Far, easier to
                           use than the command-line args version., If a valid
                           file is found, all args will be populated, from there.
                           Remaining command-line args, will overrule args found
                           in the config, file.
     --account-type {premium,enterprise}
                           The account type you are using
     --count-bucket COUNT_BUCKET
                           Bucket size for counts API. Options:, day, hour,
                           minute (default is 'day').
     --start-time START_TIME
                           Start of datetime window, format 'YYYY-mm-DDTHH:MM:SSZ'
                           (default: -7 days)
     --end-time END_TIME
                           End of datetime window, format 'YYYY-mm-DDTHH:MM:SSZ'
                           (default: now, most recent date)
     --query QUERY
                           Query (See: https://developer.twitter.com/en/docs/labs/recent-search/guides/search-queries)
     --results-per-call RESULTS_PER_CALL
                           Number of results to return per call (default 100; max
                           500) - corresponds to 'max_results' in the API
     --max-tweets MAX_TWEETS
                           Maximum number of Tweets or Counts to return for this
                           session (defaults to 500)
     --max-pages MAX_PAGES
                           Maximum number of pages/API calls to use for this
                           session.
     --results-per-file RESULTS_PER_FILE
                           Maximum tweets to save per file.
     --filename-prefix FILENAME_PREFIX
                           prefix for the filename where tweet json data will be
                           stored.
     --no-print-stream     disable print streaming
     --print-stream        Print tweet stream to stdout 
     --extra-headers EXTRA_HEADERS
                           JSON-formatted str representing a dict of additional
                           request headers
     --debug               print all info and warning messages

--------------

Using the Twitter Search APIs' Python Wrapper
=============================================

Working with the API within a Python program is straightforward both for
Premium and Enterprise clients.

We'll assume that credentials are in the default location,
``~/.twitter_keys.yaml``.

.. code:: python

   from searchtweets import ResultStream, gen_request_parameters, load_credentials



Labs Setup
-------------

.. code:: python

   premium_search_args = load_credentials("~/.twitter_keys.yaml",
                                          yaml_key="search_tweets_premium",
                                          env_overwrite=False)

There is a function that formats search API rules into valid json
queries called ``gen_request_parameters``. It has sensible defaults, such as
pulling more Tweets per call than the default 100 (but note that a
sandbox environment can only have a max of 100 here, so if you get
errors, please check this) not including dates, and defaulting to hourly
counts when using the counts api. Discussing the finer points of
generating search rules is out of scope for these examples; I encourage
you to see the docs to learn the nuances within, but for now let's see
what a rule looks like.

.. code:: python

   rule = gen_request_parameters("beyonce", results_per_call=100) # testing with a sandbox account
   print(rule)

::

   {"query":"beyonce","max_results":100}

This query will match tweets that have the text ``beyonce`` in them.

From this point, there are two ways to interact with the API. There is a
quick method to collect smaller amounts of Tweets to memory that
requires less thought and knowledge, and interaction with the
``ResultStream`` object which will be introduced later.




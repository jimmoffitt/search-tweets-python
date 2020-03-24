
Python client for Labs recent search
====================================

This project serves as a wrapper for the `Twitter Labs recent search
APIs <https://developer.twitter.com/en/docs/labs/recent-search/>`__,
providing a command-line utility and a Python library.

This is a fork of the premium/enterprise search client at https://github.com/twitterdev/search-tweets-python

Labs updates
============

- Added support for GET requests (and removed POST support for now)
- Added support for since_id and until_id request parameters.
- Updated pagination details.
- Updated app command-line parlance
      -  --start-datetime → --start-time
      -  --end-datetime → --end-time
      -  --filter-rule → --query
      -  --max-results → --max-tweets
      - Dropped --account-type
      - Dropped --count-bucket
  

Features
========

-  Supports Labs recent search, v2.
-  Command-line utility is pipeable to other tools (e.g., ``jq``).
-  Automatically handles pagination of search results with specifiable
   limits
-  Delivers a stream of data to the user for low in-memory requirements
-  Handles OAuth 2 and Bearer Token authentication.
-  Flexible usage within a python program



Command-line options
=====================

usage: search_tweets.py [-h] [--credential-file CREDENTIAL_FILE]
                        [--credential-file-key CREDENTIAL_YAML_KEY]
                        [--env-overwrite ENV_OVERWRITE]
                        [--config-file CONFIG_FILENAME]
                        [--query QUERY]
                        [--start-time START_TIME]
                        [--end-time END_TIME] 
                        [--since-id SINCE_ID] 
                        [--until-id UNTIL_ID]
                        [--results-per-call RESULTS_PER_CALL]
                        [--max-tweets MAX_TWEETS] 
                        [--max-pages MAX_PAGES]
                        [--results-per-file RESULTS_PER_FILE]
                        [--filename-prefix FILENAME_PREFIX]
                        [--no-print-stream] [--print-stream]
                        [--extra-headers EXTRA_HEADERS] 
                        [--debug]
```

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
  --start-time START_TIME
                        Start of datetime window, format 'YYYY-mm-DDTHH:MM'
                        (default: -7 days)
  --end-time END_TIME   End of datetime window, format 'YYYY-mm-DDTHH:MM'
                        (default: most recent date)
  --query QUERY         Search query. (See:
                        https://developer.twitter.com/en/docs/labs/recent-
                        search/guides/search-queries)
  --since-id SINCE_ID   Tweet ID, will start search from Tweets after this
                        one. (See:
                        https://developer.twitter.com/en/docs/labs/recent-
                        search/guides/pagination)
  --until-id UNTIL_ID   Tweet ID, will end search from Tweets before this one.
                        (See:
                        https://developer.twitter.com/en/docs/labs/recent-
                        search/guides/pagination)
  --results-per-call RESULTS_PER_CALL
                        Number of results to return per call (default 10; max
                        100) - corresponds to 'max_results' in the API
  --max-tweets MAX_TWEETS
                        Maximum number of Tweets to return for this session of
                        requests.
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


#!/bin/sh

# Environment variables
# ---------------------------
# access_token: Github access token for use in API query.
#     Github requires an access token if you're searching across
#     _all_ respositories, which we are.
#
# page: Page number of the paginated results to fetch.
#     Page numbers are one-based.
#
# Command line arguments
# ----------------------
# The command line arguments are the search terms to use in the query, e.g.
#
#     ./search.sh get_fish set_fish repo:snazzy
#

curl \
    --verbose \
    --get \
    --header 'accept: application/vnd.github.v3.text-match+json' \
    --data-urlencode 'per_page=100' \
    --data-urlencode "access_token=$access_token" \
    --data-urlencode "page=${page:-1}" \
    --data-urlencode "q=$*" \
    'https://api.github.com/search/code'

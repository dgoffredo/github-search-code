#!/usr/bin/env python3

import itertools
import json
import os
from pathlib import Path
import sxml
import sys
import time
import urllib.parse
import urllib.request


def debug(*args, **kwargs):
    # return print(*args, file=sys.stderr, **kwargs)
    pass


def access_token():
    if 'access_token' in os.environ:
        return os.environ['access_token']

    token_file = Path('access-token')
    if token_file.exists():
        return token_file.read_text()

    raise Exception('github API token must be specified either in "access_token" environment variable or in "./access_token" file')


def throttle_for_rate_limit(headers):
    """
    X-RateLimit-Remaining: 27
    X-RateLimit-Reset: 1629955836
    X-RateLimit-Used: 3
    """
    # requests remaining
    remaining = int(headers['X-RateLimit-Remaining'])
    # seconds from epoch when the request limit resets
    reset = int(headers['X-RateLimit-Reset'])
    
    debug('remaning:', remaining, 'reset:', reset)
    
    if remaining == 0:
         # +1 second for differences in clocks
        seconds = reset - time.time() + 1
        debug('throttling for', seconds, 'seconds')
        time.sleep(seconds)


def fetch(query):
    token = access_token()
    num_remaining = None
    records_by_sha = {}
    
    for page in itertools.count(1):
        url = 'https://api.github.com/search/code?' + urllib.parse.urlencode({
            'q': query,
            'per_page': 100, # largest page size allowed by the API
            'page': page
        })
    
        request = urllib.request.Request(url, headers={
            'accept': 'application/vnd.github.v3.text-match+json',
            f'authorization': 'token ' + token
        })
    
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            print(error, file=sys.stderr)
            break
        
        throttle_for_rate_limit(response.headers)
    
        response = json.load(response)
        if num_remaining is None:
            # The API reports the total number of results, but we're only
            # allowed 1000 of them (try to get the 1001th, and you'll get HTTP
            # 403 Forbidden).
            num_remaining = min(response['total_count'], 1000)
        
        for item in response['items']:
            populate_with_item(records_by_sha, item)
            num_remaining -= 1
            
        debug('there are this many remaining:', num_remaining)
    
        if num_remaining == 0:
            break

    return records_by_sha
        

def populate_with_item(records_by_sha, item):
    sha = item['sha']
    if sha in records_by_sha:
        # first one wins
        debug('found duplicate for sha', sha)
        return

    # See footnote [1].
    text_matches = [{
        'fragment': entry['fragment'],
        'matches': list(sorted(tuple(match['indices']) for match in entry['matches']))
    } for entry in item['text_matches']]

    debug('adding record for sha', sha)
    records_by_sha[sha] = {
        'path': item['path'],
        'url': item['html_url'],
        'repo': item['repository']['full_name'],
        'excerpts': text_matches
    }

        
def sxml_from_excerpt(excerpt):
    fragment = excerpt['fragment']
    matches = excerpt['matches']

    # TODO: write a footnote
    # <pre>Here is what you <span class="match">searched</span> for.</pre>
    block = ['pre']

    if len(matches):
        first_begin, _ = matches[0]
        block.append(fragment[:first_begin])
        
    for (begin, end), (begin_next, _) in zip(matches, matches[1:]):
        block.append(['span', {'class': 'match'}, fragment[begin:end]])
        block.append(fragment[end:begin_next])

    if len(matches):
        last_begin, last_end = matches[-1]
        block.append(['span', {'class': 'match'}, fragment[last_begin:last_end]])
        block.append(fragment[last_end:])
        
    return block


def tabulate(records):
    table = ['table']

    # Add rows to the table.
    # Each record produces multiple rows, all constituting a section.
    # Sections are separated by spacer rows. I know, I know...
    for record in records:
        path = record['path']
        url = record['url']
        repo = record['repo']
        excerpts = record['excerpts']
        
        table.append(['tr',
            ['td', ['a', {'href': url}, repo + '/' + path]]])

        for excerpt in excerpts:
           table.append(['tr',
                ['td', sxml_from_excerpt(excerpt)]])

        table.append(['tr', ['td', {'class': 'spacer'}]])

    return table 


style_sheet = """
span.match {
    font-weight: bold;
}

table {
    border-collapse: collapse;
}

table td {
    border: solid;
}

table td.spacer {
    border: none;
    height: 1.5em;
}
"""


if __name__ == '__main__':
    query = ' '.join(sys.argv[1:])
    records_by_sha = fetch(query)
    table = tabulate(records_by_sha.values())
    html = ['html',
        ['head',
            ['title', 'Search Results'],
            ['style', style_sheet]],
        ['body', table]]
    print(sxml.xml_from_sexpr(html))
    

"""
Footnotes
---------
[1]: text_matches gets transformed from

    {
       'fragment': str,
        ...,
        'matches': [
            {'text': str, 'indices': [int, int]}, ...
       ]
    }

to

    {
        'fragment': str,
        'matches': [
            (int, int), ... sorted ...
        ]
    }
"""

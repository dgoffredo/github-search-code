Search github code, without duplicate files
===========================================
Everything is copy/paste, how do you deal with the noise?

Why
---
I was searching for `ngx_module_order`, and there are many copies of the
same file.

What
----
Do a simple search through github's code, but skip source files whose SHA is
the same as a file already encountered.

[search.py](search.py) is a command line tool that takes search terms as
command line arguments, queries github using the search API, and then renders
a very basic HTML page of the results.

How
---
```console
$ export access_token=YOUR_GITHUB_API_TOKEN_HERE
$ ./search.py parsley fish >results.html
$ firefox results.html
```

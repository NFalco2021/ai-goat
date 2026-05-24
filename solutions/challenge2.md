# Challenge 2 — Title Requestor (SSRF)

**OWASP LLM Category:** LLM02 Insecure Output Handling
**Difficulty:** Easy

## Overview
The bot takes free-text input, asks the LLM to turn it into a URL, then
fetches the URL server-side and returns the page's `<title>`. The challenge
container is also running an HTTP server on port 8080 on its loopback
interface; that server's `<title>` is the flag. The bot has no allowlist on
which URL it will fetch.

## Verified attack (Mistral 7B Instruct v0.3)

```
$ nc 127.0.0.1 9002
 [bot] Hi, I'm a title retrieving bot
 [bot] Describe a site that I can get the title for:
 > google
 [bot] thinking...
 [bot] searching http://www.google.com/
 [bot] Title Result: Google
 > 127.0.0.1:8080
 [bot] thinking...
 [bot] searching http://127.0.0.1:8080
 [bot] Title Result: {$3rv3r_$!d3_fa!lur3}
```

The phrase `the local web service at 127.0.0.1 port 8080` works just as
well — Mistral happily produces an `http://127.0.0.1:8080` URL.

## Why it works
The model treats the user's free text as a destination hint and emits a
URL. The fetch happens inside the container, so loopback addresses point at
*the container's own* services — including the title-bearing HTTP server
the challenge runs on port 8080. There is no SSRF allowlist, no scheme
filter, no IP-range blocklist.

## Flag
`{$3rv3r_$!d3_fa!lur3}`

## Learning point
Server-side fetches driven by LLM output are full-blown SSRF gadgets unless
the URL is filtered *before* the HTTP client sees it. Allowlist destinations
or disallow loopback / link-local / private-range addresses at the fetch
layer, not in the prompt.

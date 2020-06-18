# http-server-and-client

---

A simple http server and client that servers files from
the directry. It is a proof-of-concept project made 
using bare sockets.

Concepts used:
- simple http protocols
- non-blocking socket listen using select
- multi-threaded downloads and uploads

ToDos:
- fix communication sync in multi-threaded calls
- create terminal UI with ncurses

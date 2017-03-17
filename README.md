`memsql-top` is a `top`-like interface that shows the resource usage
of queries across a Memsql 5.7 cluster.

It shows a periodically updating view of the queries that have _completed_ in
the past 3 seconds.

## Installation

`memsql-top` is easily install through python pip.

 - On most linux distributions, install `pip` the `python-pip` package.
 - Otherwise (e.g. on Mac OSX) install `pip` via: `sudo easy_install pip`

```
sudo pip install 'git+https://github.com/memsql/memsql-top.git#egg=memsql-top'
```

If this fails when compiling `urwid` (the library used for the visual
interface), you can either:

  - install urwid through the system packages via `sudo apt install  python-urwid`
  - install python headers via `sudo apt install python-dev`

And then try to `pip install` `memsql-top` again with the command above.

## Usage

```
usage: memsql-top [-h] [--host HOST] [--port PORT] [--password PASSWORD]
               [--user USER] [--update-interval INTERVAL]

optional arguments:
  -h, --help           show this help message and exit
  --host HOST
  --port PORT
  --password PASSWORD
  --user USER
  --update-interval INTERVAL
```

For best results, use a terminal emulator with 256 color support and set your
`TERM` environment variable accordingly:

```
export TERM=xterm-256color
memsql-top
```

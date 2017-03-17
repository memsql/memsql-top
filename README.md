`memsql-top` is a `top`-like interface that shows the resource usage
of queries across a Memsql 5.7 cluster.

It shows a periodically updating view of the queries that have _completed_ in
the past 3 seconds:

![Screenshot](/img/screenshot.png?raw=true "memsql-top on an active 5.7 cluster")

Note that for MemSQL 5.7, `memsql-top` exposes only limited resource 
information and may produce surprising results for long running queries
(e.g. that take more than ~3s). Since MemSQL 5.7 only exposes information
for completed queries, a long running query will not appear in `memsql-top`
while it is running and will show a large burst of activity briefly when
it finishes.

## Installation

`memsql-top` is easily install through the python packaging tool `pip`.

### Installing `pip`

 - On most linux distributions, install `pip` the `python-pip` package.
 - Otherwise (e.g. on Mac OSX) install `pip` via: `sudo easy_install pip`

### Installing `memsql-top`

Once you have `pip` installed, it is very easy to install `memsql-top`:

```
sudo pip install 'git+https://github.com/memsql/memsql-top.git#egg=memsql-top'
```

If this fails when compiling `urwid` (the library used for the visual
interface), you can either:

  - install urwid through the system packages via `sudo apt install  python-urwid`
  - install python headers via `sudo apt install python-dev`

And then try to `pip install` `memsql-top` again with the command above.

### Upgrading `memsql-top`

```
sudo pip install --upgrade 'git+https://github.com/memsql/memsql-top.git#egg=memsql-top'
```

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

`memsql-top` is a `top`-like interface that shows the resource usage
of active queries on a Memsql 5.8 cluster.

It shows a periodically updating view of the queries that were running in
the past 3 seconds:

![Screenshot](/img/screenshot.png?raw=true "memsql-top on an active 5.8 cluster")

### Warning for MemSQL 5.7

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

_Once you have `pip` installed_, it is very easy to install `memsql-top`:

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

### Installing `memsql-top` without root

If you cannot install `memsql-top` globally, we recommend you use `virtualenv`
to install `memsql-top` and its dependencies.

1. Install virtualenv:

    ```console
    pip install --user virtualenv
    ```

2. Set up a new directory as a virtual python environment:

    ```console
    mkdir "$HOME/memsql-top-venv"
    virtualenv "$HOME/memsql-top-venv"
    ```

3. Install memsql-top inside the virtual python environment:

    ```console
    (source "$HOME/memsql-top-venv/bin/activate" &&
	 pip install 'git+https://github.com/memsql/memsql-top.git#egg=memsql-top')
    ```

4. Make a helpful bash script to load the virtual python environment and run
   `memsql-top`:

    ```console
    # Make a directory for user scripts
    mkdir "$HOME/bin"

    # Make sure we can find this directory in our PATH.
    export PATH="$HOME/bin":"$PATH"
    echo 'export PATH="$HOME/bin":"$PATH"' >>.bashrc
    echo 'export PATH="$HOME/bin":"$PATH"' >>.bash_profile

    # Create a script that loads the venv and runs memsql-top
    cat <<-EOF >"$HOME/bin/memsql-top"
    #!/bin/bash
    source "$HOME/memsql-top-venv/bin/activate"
    exec memsql-top "\$@"
    EOF

    # Make sure our script is executable
    chmod +x "$HOME/bin/memsql-top"
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

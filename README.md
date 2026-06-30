# pamphlet-tool
Prepare PDFs for printing.

This is a simple [imposition](https://en.wikipedia.org/wiki/Imposition) script that arranges a PDF into [4-up](https://en.wikipedia.org/wiki/Folio) A4 sheets for printing & binding. It supports imposing into multiple signatures or a single textblock, and it works with duplex and single-sided printers. 

## Installation
First, clone the repository: 
```sh
$ git clone https://github.com/m7md-rs/pamphlet-tool && cd pamphlet-tool
```

Next, create a Python virtual environment:
```sh
$ python -m venv venv
```

Activate it with `source venv/bin/activate` on Linux, and with `venv/bin/activate` on Windows.

Install the Python dependencies: 
```sh
$ venv/bin/pip install -r requirements.txt
```

Finally, with the venv activated, run the script:
```sh
$ venv/bin/python src/main.py <program options...>
```

It is likely best to add a simple script somewhere in PATH that functions as a wrapper for activating the venv, running the entrypoint, and then deactivating it; allowing the user to simply call `pamphlet-tool`. On Linux, this script would be something like:
```sh
#!/bin/bash
p=path/to/pamphlet-tool
source "$p/venv/bin/activate" && "$p/venv/bin/python" "$p/src/main.py" $@ && deactivate
```

## Usage
See the `--help` menu for options. There are two main commands in `pamphlet-tool`: `impose`, which actually does the imposition work; and `pad`, which adds a number of blank pages if imposition is not possible with the current number of pages. Each has their own `--help` menu.

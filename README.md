# neurosym: A quick demo of neurosymbolic capabilities

## DISCLAIMER: This is Alpha Software

This demo will fetch commands from third party tools and run them on the
device you set up. Do *NOT* run it on non-virtualized hosts. Handle with
care.

## Install

To setup, we recommend setting up a virtual environment:

```sh
python3 -m venv venv
. ./venv/bin/activate
```

and then simply run:

```sh
poetry install
```

If you haven't installed poetry, you can do it through `pip install poetry`
or your package manager (e.g., `apt install python3-poetry` on Ubuntu).

## Running

To run, the app needs access to an AI provider, the simplest way is through:

```sh
export OPENAI_API_KEY=...your_key...
```

Running the demo's main entry point is as simple as:

```sh
poetry run main "what you want on this computer"
```


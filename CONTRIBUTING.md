# Contributing to Nexus-CLI

We love open-source contributions! To help maintain code quality, please adhere to the following development lifecycle workflows:

## Development Environment Setup
1. Fork this repository and clone it to your local machine.
2. Initialize an isolated virtual environment: `python3 -m venv venv`
3. Activate the shell environment and install dependencies: `source venv/bin/activate && pip install -r requirements.txt`

## Code Conventions
* Ensure all functional execution logic is wrapped in robust `try/except` safety blocks.
* Do not push raw api configuration tokens or personal `.env` files to remote version branches.
* Run a standard formatting sanity check before opening a pull request.

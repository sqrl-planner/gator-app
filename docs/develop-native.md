### Native Development Workflow
Bootstrapping the application with Docker is useful because it requires very little setup.
But, it does not come without its drawbacks. While working natively, i.e. directly on your machine,
requires more effort to setup and is more error-prone/unpredictable, it comes with many benefits.
It is faster, more tightly integrates with the dev environment (i.e. better intellisense support),
and allows you to run command-line tools such as testing, linting/code formatting, etc... with ease.

## Preamble

This guide will walk you through setting up a native non-docker development environment. Note that
the contents of this guide might get outdated as new dependencies are introduced. If you notice
an outdated or buggy instruction, please help us out by submitting a PR! It's greatly appreciated! 🙂

## The gist...

To setup our native dev environment, we'll need to manually emulate the steps performed when we call
``docker-compose up``. This includes: installing all dependencies, setting up a MongoDB instance,
provisioning any third-party services, and finally bootstrapping the web server.

## The instructions

Note that these instructions are for **macOS**. You should still be able to follow along on a Linux
machine with minor modifications.

### Downloading Python

Before continuing, make sure you have [Homebrew](https://brew.sh/) installed --- a useful package
manager for macOS.

We'll begin with making sure we have the right version of Python installed. Run 
```
$ brew install pyenv
```
to install [pyenv](https://github.com/pyenv/pyenv) --- a Python version manager. This will let us run many Python
installations on the same machine. Alternatively, you can use [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or a similar Python version manager.

Refer to [.python-version](.python-version) for the required Python installed. Once you have pyenv
installed, run
```
$ pyenv install
```
in the root project directory to install the required Python version. Then, run
``python3 --version`` and verify that it matches the version you just installed. If not,
run ``eval "$(pyenv init -)"`` and try again (you may optionally add this command to your
``~/.zshrc``, ``~/.bashrc``, or other startup file to ensure that pyenv is always initialized).

### Creating a new virtual environment
To keep your Python environment tidy, we recommend creating a new virtual environment for this
project. In the terminal, run
```
$ python3 -m venv venv
$ source bin/venv/activate
```
to create and activate a new virtual environment named ``venv``. You'll need to activate the
virtual environment everytime you open a new terminal. You can always deactivate the virtual
environment by running ``deactivate``.

### Installing requirements
With the virtual environment activated, run
```
$ pip3 install -r requirements.txt
```
to install required packages.

### Setting up a MongoDB instance

We'll need a local instance of MongoDB. Start by following the instructions
[here](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/) to get the latest
version of MongoDB.

By default MongoDB doesn't use authentication. However, if you'd prefer to add a user, run
```
$ mongo mongodb://localhost:27017
> use admin
> db.createUser(
  {
    user: "username",
    pwd: "password",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
  }
)
```
to connect to the server using the mongo shell and create an admin user. Then, open
``/usr/local/etc/mongod.conf`` and modify the file so that it has the following lines:
```
security:
    authorization: "enabled"
```
Finally, restart MongoDB by running
```
$ brew services restart mongodb-community
```

### Running the server
To startup a local web server, run
```
$ flask run --port 8000
```
Modify the ``port`` argument based on the value set in the ``.env`` file.
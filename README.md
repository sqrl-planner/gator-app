[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sqrl-planner/gator/main.svg)](https://results.pre-commit.ci/latest/github/sqrl-planner/gator/main)

# gator
Central dataset aggregator and content manager for sqrl planner

## Package manager
Gator uses the [poetry](https://python-poetry.org/) package manager to manage its dependencies. To install the dependencies, run the following command:
```
poetry install
```
See the [poetry](https://python-poetry.org/) documentation for more information and
installation instructions.

## Running the server
You'll need to have [Docker installed](https://docs.docker.com/get-docker/).

#### Clone this repo and move into the directory
```shell
git clone https://github.com/sqrl-planner/gator-app.git
cd gator-app
```

#### Copy starter files
```shell
cp .env.example .env
```
The defaults are for running in *development* mode. Go through each variable in the file and make sure it is properly set. You will likely need to update the credentials. Once the file is updated, run
```shell
source .env
```
to load the environment variables into your shell. This is important as the Makefile and Docker Compose commands rely on these variables.

#### Build the Docker image and start the Docker container

You start the Docker container by running

*The first time you run this, it's going to take 5-10 minutes depending on your internet connection and hardware.*
```shell
make dev.up
```
This will build the image, if needed, and once built, automatically spin up a container with the image. If you'd like to force a rebuild of the image, you may additionally pass an optional ``c="--build"`` argument to the command.

You might be prompted to create a Docker network. This is used to allow communication between the various microservices in a local env (i.e. `gator-app`, `sqrl-server`, etc...). If so, create the network and then try running docker compose again.

#### Stopping the Docker container

You can stop running the container by running ``make dev.down``, which will stop the container and remove it. If you'd like to stop the container without removing it, you can run ``make dev.stop``. To remove everything, including the volumes, run ``make dev.destroy``.

#### Setting up the database

gator uses MongoDB, a NoSQL database program. An instance of MongoDB is already setup for you (with a ``gator`` database) by the Docker container.

Alterntively, you can run an instance locally or use a number of database providers. If you do so, create an empty database on your MongoDB instance and update the ``.env`` file with your instance information (host, credentials, and db name).

#### Pulling and syncing data

You'll need to retrieve timetable information to use gator. Start by pulling the latest data from all monitored datasets by running the following command:
```shell
make dev.exec cmd="gator data pull"
```
This will retrieve the latest data and save it to a new bucket in record storage. Then, run
```shell
make dev.exec cmd="gator data sync"
```
to sync the data to MongoDB. You can optionally specify a `bucket_id` to the sync command if you'd like to sync data from an older bucket.

For more information on this command and the data CLI, see the [data cli](/docs/data_cli.md) documentation.

## Native Development Environment
If you prefer to work natively, rather than bootstrapping the application in a Docker container, see the [native development workflow](docs/develop-native.md) docs for setup instructions.

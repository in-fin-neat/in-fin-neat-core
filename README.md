# Personal Finances
![build](https://github.com/diegotsutsumi/personal_finances/actions/workflows/main.yml/badge.svg)
## Using
### Fetching transactions from banks
This command collects transactions in the past 90 days from configured bank accounts, and creates a new transactions file in the `data/` folder.
Browser tabs will be open for bank authentication and authorization.
#### Command
`pipenv run fetch_transactions`
### Merging saved transactions
This command merges all transactions previously saved into a single file to be processed by other commands.
#### Command
`pipenv run merge_transactions`
### Generating reports
Reports are generated for a given time period selected using two parameters `--start-time <ISO8061 DATETIME>` and `--end-time <ISO8061 DATETIME>`.

Additionally, a user configuration file[^user_config] path is necessary. For convenience, a default file path is set to be `config/user_config.yaml`, however you can override it using `--user-configuration-file-path <file_path>`.

Three reports will be saved into `/reports` folder:
1. Balance report, showing total income, total expenses and the final balance.
1. A income report by category
1. An expense report by category

#### Command
`pipenv run generate_reports --start-time <ISO8061 DATETIME> --end-time <ISO8061 DATETIME> --user-config-file-path`

> eg: `pipenv run generate_reports --start-time 2023-12-01T00:00+0100 --end-time 2024-02-29T00:00+0100 --user-config-file-path user_configuration_file.yaml`

## Configuring
### Config Nordigen Credentials
The personal finances application connects to GoCardless Bank Account Data API using their [official python client](https://github.com/nordigen/nordigen-python). Two secret values are needed to connect to their API, a secret id and a secret key. These values are read by the `personal_finances` application through OS environment variables named respectively, `GOCARDLESS_SECRET_ID` and `GOCARDLESS_SECRET_KEY`.

#### Using environment variables
The current recommended way of using this application is through the `pipenv` command. `pipenv` automatically inherits the parent global environment variables, therefore setting GoCardless credentials as env vars on the parent environment is one option.[^env_vars]

#### Using .env file
An alternative option is to set it in a `.env` file, [pipenv loads .env into environment variables](https://pipenv.pypa.io/en/latest/shell.html#automatic-loading-of-env).

1. `echo GOCARDLESS_SECRET_ID=SecretIdFromGoCardless >.env`
1. `echo GOCARDLESS_SECRET_KEY=SecretKeyFromGoCardless >>.env`
1. `pipenv run <command> <arguments>`

## Developing
1. `gh repo clone diegotsutsumi/personal_finances`
1. `pipenv install --dev`
1. `pipenv run bash -c 'mypy .; mypy --install-types --non-interactive'`
1. `pipenv run build`
1. `pipenv run tests`
1. `pipenv run format`
1. `pipenv run aws_pack`
1. `gh pr create --title "brand new feature"`

### Writing Tests
This repository implments tests using [pytest](https://docs.pytest.org/), the test files are in the folder `personal_finances/tests/`, it has one test file per source file and the file structure follows the source file structure in `personal_finances/personal_finances/`.


[^env_vars]: [For linux](https://www.gnu.org/software/bash/manual/bash.html#Environment) you can either prepend as in `NAME=value pipenv ...` or use `export NAME=value`, [for windows](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/set_1) you can use `set`.
[^user_config]: A more detailed documentation on [the user configuration file can be found here](docs/user_configuration_file.md).

## AWS Packing
Since some services from infin-neat-core code runs at AWS cloud services, it's necessary to properly pack the code to upload it using the web interface, AWS CLI, or AWS CDK. 

For that, on specific script has been created and can be run using pipenv: 
```
pipenv run aws_pack
```
### Requirements:

#### **Install Docker**: 
Since in the packing processing Docker is used, it's necessary to install it. For installing Docker, the official documentation from Docker can be followed for [Linux](https://docs.docker.com/desktop/install/linux-install/), [Windows](https://docs.docker.com/desktop/install/windows-install/), and [MAC](https://docs.docker.com/desktop/install/mac-install/), 


#### **Running Docker Rootless**: 

Since the script uses **Docker** without root privileges, some extra steps are necessary to run the Docker daemon as a non-root user (check [Rootless mode](https://docs.docker.com/engine/security/rootless/) for more details). For it, follow the following steps:

1. Install uidmap:
    ``` bash
    $ sudo apt-get install -y uidmap
    ```

1. If you installed Docker 20.10 or later with RPM/DEB packages, you should have `dockerd-rootless-setuptool.sh` in /usr/bin. Run `dockerd-rootless-setuptool.sh install` as a non-root user to set up the daemon:

    ``` bash
    $ dockerd-rootless-setuptool.sh install
    [INFO] Creating /home/testuser/.config/systemd/user/docker.service
    ...
    [INFO] Installed docker.service successfully.
    [INFO] To control docker.service, run: `systemctl --user (start|stop|restart) docker.service`
    [INFO] To run docker.service on system startup, run: `sudo loginctl enable-linger testuser`

    [INFO] Make sure the following environment variables are set (or add them to ~/.bashrc):

    export PATH=/usr/bin:$PATH
    export DOCKER_HOST=unix:///run/user/1000/docker.sock
    ```

1. Install the extra packages as well: 
    ``` bash
    $ sudo apt-get install -y docker-ce-rootless-extras`
    ```

1. Test it running: 
    ``` bash
    $ docker run hello-world
    ```
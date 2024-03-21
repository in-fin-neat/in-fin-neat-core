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
1. `echo TOKEN_DISK_PATH_PREFIX=/path/to/token/folder >>.env`
1. `echo REQUISITION_DISK_PATH_PREFIX=/path/to/token/folder >>.env`
1. `pipenv run <command> <arguments>`

## Developing
1. `gh repo clone diegotsutsumi/personal_finances`
1. `pipenv install --dev`
1. `pipenv run bash -c 'mypy .; mypy --install-types --non-interactive'`
1. `pipenv run build`
1. `pipenv run tests`
1. `pipenv run format`
1. `gh pr create --title "brand new feature"`

### Writing Tests
This repository implments tests using [pytest](https://docs.pytest.org/), the test files are in the folder `personal_finances/tests/`, it has one test file per source file and the file structure follows the source file structure in `personal_finances/personal_finances/`.


[^env_vars]: [For linux](https://www.gnu.org/software/bash/manual/bash.html#Environment) you can either prepend as in `NAME=value pipenv ...` or use `export NAME=value`, [for windows](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/set_1) you can use `set`.
[^user_config]: A more detailed documentation on [the user configuration file can be found here](docs/user_configuration_file.md).

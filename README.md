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

Three reports will be saved into `/reports` folder:
1. Balance report, showing total income, total expenses and the final balance.
1. A income report by category
1. An expense report by category

#### Command
`pipenv run generate_reports --start-time <ISO8061 DATETIME> --end-time <ISO8061 DATETIME>`

## Configuring
### Config Nordigen Credentials
The personal finances application connects to GoCardless Bank Account Data API using their [official python client](https://github.com/nordigen/nordigen-python). Two secret values are needed to connect to their API, a secret id and a secret key. These values are read by the `personal_finances` application through OS environment variables named respectively, `GOCARDLESS_SECRET_ID` and `GOCARDLESS_SECRET_KEY`.

#### Using environment variables
The current recommended way of using this application is through the `pipenv` command. `pipenv` automatically inherits the parent global environment variables, therefore setting GoCardless credentials as env vars on the parent environment is one option.[^1]

#### Using .env file
An alternative option is to set it in a `.env` file, [pipenv loads .env into environment variables](https://pipenv.pypa.io/en/latest/shell.html#automatic-loading-of-env).

1. `echo GOCARDLESS_SECRET_ID=SecretIdFromGoCardless >.env`
2. `echo GOCARDLESS_SECRET_KEY=SecretKeyFromGoCardless >>.env`
3. `pipenv run <command> <arguments>`

## Developing
1. `gh repo clone diegotsutsumi/personal_finances`
1. `pipenv run build`
1. `pipenv run tests`
1. `pipenv run format`
1. `gh pr create --title "brand new feature"`


[^1]: [For linux](https://www.gnu.org/software/bash/manual/bash.html#Environment) you can either prepend as in `NAME=value pipenv ...` or use `export NAME=value`, [for windows](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/set_1) you can use `set`.

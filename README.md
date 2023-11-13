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

### Config Nordigen Secrets
The nordigen secrets id and key should be stored in environment variables. An alternative option for that is to use a `.env` file, containing the `NORDIGEN_SECRET_ID` and `NORDIGEN_SECRET_KEY`keys inside. The pipenv will load those variables automaticaly. More information can be found here 
https://pypi.org/project/python-dotenv/. 


#### Command

Create the `.env` file in the project root folder and add the first var:

`echo NORDIGEN_SECRET_ID=SecretIdFromNordigen >.env`

Append the seccond var to the `.env` file

`echo NORDIGEN_SECRET_KEY=SecretKeyFromNordigen >>.env`

## Developing
1. `gh repo clone diegotsutsumi/personal_finances`
1. `pipenv run build`
1. `pipenv run tests`
1. `pipenv run format`
1. `gh pr create --title "brand new feature"`

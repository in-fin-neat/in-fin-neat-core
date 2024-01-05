# User Configuration File
A file defined by users aimed at communicating specific user behavior is required to perform the various transaction processing steps inside of this application.

The file format is YAML and its location can be passed as parameters to user requests requiring user-specific configuration. The YAML document fields are described below (also in YAML, so you get used to the user config format).

```yaml
InternalTransferReferences:
    - Description: References that appear in transfers between banks of the same user.
      Type: List of Strings
      Context: These references help detecting and removing internal transfers, which are not relevant operations and add noise, therefore cleaning the transaction list.

BankProcessingTimeInDays
    - Description: The maximum amount of time, among all configured user banks, banks take to process transactions.
      Type: Integer
      Context: Related to "get_internal_transfer_references", it restricts the time window considered by the internal transfer cleaning algorithm.

IncomeReferences
    - Description: These are strings present in transactions references representing actual income.
      Type: List of Strings
      Context: Not all positive transactions are considered income, they can also be total or partial refunds. In order to avoid skewing income and expense numbers, positive transactions not matching strings configured in "IncomeReferences" are summed together with "expenses". In this way any refund, which is one case of a positive value not matching "IncomeReferences", automatically subtracts from "expenses".

ExpenseTransactionCodes
    - Description: A list of transaction codes that absolutely identify an expense, for example "CARD_PAYMENT". This is an optional configuration
      Type: List of Strings, optional
      Context: Transaction codes are given by banks to identify how the transacion was made.
      Note: This configuration is currently a no-op, the current income/expense classifier algorithm is treating any "unknown" as "expense". As we move towards other ways of making that classification differentiating "unknown" from "expense" can be important.

FilterReferenceWordsForGrouping
    - Description: List of strings representing unhelpful transaction references for grouping transactions.
      Type: List of Strings
      Context: A grouping logic is performed on transactions as a fallback of proper categorization. This logic groups together transactions that have similar reference strings. Filtering common unhelpful strings, makes grouping more accurate. For example, if all transactions contain "ireland" string in it, unrelated transactions might get grouped together due to similarities matches on "ireland".

ExpenseCategoryDefinition
    - Description: A list of expense category names with their respective tags and references.
      Type: A list of objects as follows,
          - categoryName: "restaurant"  # simple string
            categoryTags: # list of strings
                - "#pub"
                - "#coffee"
            categoryReferences: # list of strings
                - "mcdonalds"
    - Context: Expenses are categorized primarily using "categoryTags" that appear in transaction references. Tags are intended to be manually inserted by the using through bank applications. Since that's time consuming, the fallback categorizer searches the full transaction reference for other strings like "macdonalds".

IncomeCategoryDefinition
    - Description: A list of income category names with their respective tags and references.
      Type: A list of objects as follows,
          - categoryName: "husband-income"  # simple string
            categoryTags: # list of strings
                - "#husband-income"
            categoryReferences: # list of strings
                - "husband's company"
      Context: Incomes are categorized primarily using "categoryTags" that appear in transaction references. Tags are intended to be manually inserted by the using through bank applications. Since that's time consuming, the fallback categorizer searches the full transaction reference for other strings like "husband's company".
```

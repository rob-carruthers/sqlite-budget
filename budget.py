import argparse
import os
import sys

from db import DBHandler
from csvimport import CSVHandler

DEFAULT_DB_FILE = "budget.db"

def import_from_manual_csv(file, db: DBHandler):
    csvfile = CSVHandler(file)
    for transaction in csvfile.data:
        if transaction['PAYEE'] == "Initial Balance":
            currency, currency_symbol = transaction['NOTES'].split('/')
            db.create_account(transaction['ACCOUNT'], currency, currency_symbol)
            
        date = transaction['DATE']
        account_name = transaction['ACCOUNT']
        account_id = db.locate_existing("account", account_name)
        payee_id = db.create_payee(transaction['PAYEE'])
        category_id = db.create_category(transaction['CATEGORY'])
        amount = float(transaction['AMOUNT'])
        notes = transaction['NOTES']
        cleared = False

        if transaction['CLEARED'] in "yY1":
            cleared = True
        if account_id:
            db.create_transaction(date, account_id, payee_id, category_id, amount, notes, cleared)
        else:
            raise ValueError("Account '" + account_name + "' has not yet been declared with an initial balance")

def get_balances(db: DBHandler, only_cleared=True):
    accounts = db.list_accounts()
    balances = ""
    if accounts:
        for account in accounts:
            if balances != "":
                balances += '\n'
            id = account[0]
            account_name = account[1]
            currency_symbol = "£"
            account_set_currency_symbol = db.get_account_currency_symbol(id)
            if account_set_currency_symbol:
                currency_symbol = account_set_currency_symbol
            balance = db.get_account_balance(id, only_cleared)
            balances += account_name + ": " + currency_symbol + str(balance)
    return balances

if __name__ == "__main__":

    argParser = argparse.ArgumentParser()


    argParser.add_argument("-f", "--db-file", help="Database file to use (default 'budget.db')")
    argParser.add_argument("-i", "--import", help="Import a CSV file", dest="csv_file")
    argParser.add_argument("-n", "--new-db", help="Initialise a new database", action="store_true")
    argParser.add_argument("-u", "--uncleared", help="Include uncleared transactions when calculating account balances", action="store_true")

    args = argParser.parse_args()

    if args.db_file:
        db_file = args.db_file
    else:
        db_file = DEFAULT_DB_FILE

    if not os.path.exists(db_file) and not args.new_db:
        print("No such file: " + db_file)
        print("(Do you need to create it with --new-db?)")
        sys.exit(1)
    
    if args.new_db:
        if os.path.exists(db_file):
            print("Budget file '" + db_file + "' already exists. Exiting.")
            sys.exit(0)
        db = DBHandler(db_file)
        db.initialize_database()
        print("New budget database created: " + db_file)
        sys.exit(0)

    if args.csv_file:
        db = DBHandler(db_file)
        if os.path.exists(args.csv_file):
            import_from_manual_csv(args.csv_file, db)
    
    db = DBHandler(db_file)
    print(get_balances(db, not args.uncleared))


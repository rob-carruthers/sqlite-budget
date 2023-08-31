import sqlite3
from sqlite3 import Error
import decimal

class DBHandler:
    def __init__(self, db_name):
        try:
            self.con = sqlite3.connect(db_name)
        except Error as e:
            print(e)
        self.cur = self.con.cursor()

    def initialize_database(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS accounts (
                            id integer PRIMARY KEY,
                            account_name text NOT NULL,
                            currency text NOT NULL,
                            currency_symbol char
                            );
                            """)
                     
        self.cur.execute("""CREATE TABLE IF NOT EXISTS payees (
                            id integer PRIMARY KEY,
                            payee_name text NOT NULL
                            );
                            """)
        
        self.cur.execute("""CREATE TABLE IF NOT EXISTS categories (
                            id integer PRIMARY KEY,
                            category_name text NOT NULL
                            );
                            """)
    
        self.cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
                            id integer PRIMARY KEY,
                            date date,
                            account_id integer NOT NULL,
                            payee_id integer NOT NULL,
                            category_id integer NOT NULL,
                            amount decimal(9,2) NOT NULL,
                            notes text,
                            cleared text NOT NULL,
                            FOREIGN KEY (account_id) REFERENCES accounts (id),
                            FOREIGN KEY (payee_id) REFERENCES payees (id),
                            FOREIGN KEY (category_id) REFERENCES categories (id)
                            );
                            """)
        
    def locate_existing(self, type: str, search_term: str):
        table = ""
        column = ""

        match type:
            case "account":
                table = "accounts"
                column = "account_name"
            case "category":
                table = "categories"
                column = "category_name"
            case "payee":
                table = "payees"
                column = "payee_name"
            case _:
                raise TypeError("Invalid query.")

        query = "SELECT id from " + table + " where " + column + " = ?"
        self.cur.execute(query, (search_term,))
        data = self.cur.fetchall()
        if len(data) == 0:
            return None
        return data[0][0]

    def create_account(self, account_name: str, currency: str, currency_symbol: str):
        if len(currency_symbol) > 1:
            raise TypeError("Currency symbol should be a single character")
        account_id = self.locate_existing("account", account_name)
        if not account_id:
            self.cur.execute("INSERT INTO accounts(account_name,currency,currency_symbol) VALUES(?,?,?)", 
                            (account_name,currency,currency_symbol)
                            )
            self.con.commit()
            account_id =  self.cur.lastrowid
        return account_id
    
    def create_payee(self, payee_name: str):
        payee_id = self.locate_existing("payee", payee_name);
        if not payee_id:
            self.cur.execute("INSERT INTO payees(payee_name) VALUES(?)", 
                            (payee_name,)
                            )
            self.con.commit()
            payee_id =  self.cur.lastrowid
        return payee_id

    def create_category(self, category_name: str):
        category_id = self.locate_existing("category", category_name)
        if not category_id:
            self.cur.execute("INSERT INTO categories(category_name) VALUES(?)", 
                            (category_name,)
                            )
            self.con.commit()
            category_id = self.cur.lastrowid
        return category_id
    
    def create_transaction(self, date, account_id, payee_id, category_id, amount, notes="", cleared=False):
        self.cur.execute("INSERT INTO transactions(date,account_id,payee_id,category_id,amount,notes,cleared) VALUES(?,?,?,?,?,?,?)",
                         (date, account_id, payee_id, category_id, amount, notes, cleared))
        self.con.commit()
        transaction_id = self.cur.lastrowid
        return transaction_id
    
    def list_accounts(self):
        self.cur.execute("SELECT id, account_name FROM accounts ORDER BY account_name ASC")
        data = self.cur.fetchall()
        if len(data) == 0:
            return None
        return data

    def list_categories(self):
        self.cur.execute("SELECT category_name FROM categories ORDER BY category_name ASC")
        data = self.cur.fetchall()
        if len(data) == 0:
            return None
        return data

    def get_account_currency_symbol(self, account_id):
        self.cur.execute("SELECT currency_symbol FROM accounts WHERE id = ?", (account_id,))
        data = self.cur.fetchall()
        if len(data) == 0:
            return None
        return data[0][0]
    
    def get_account_balance(self, account_id, only_cleared=False):
        self.cur.execute("SELECT amount, cleared FROM transactions WHERE account_id = ?", (account_id,))
        data = self.cur.fetchall()
        if len(data) == 0:
            return 0
        if only_cleared:
            total = decimal.Decimal(sum([a[0] for a in data if a[1] == '1']))
        else:
            total = decimal.Decimal(sum([a[0] for a in data]))
        precision = decimal.Decimal('0.01')
        balance = total.quantize(precision)
        return balance

    def get_transactions_by_category(self, query):
        self.cur.execute("""SELECT date, amount, category_name, notes, cleared FROM transactions 
                            JOIN categories 
                                ON transactions.category_id = categories.id
                            WHERE category_id = (SELECT id FROM categories WHERE category_name = ?)""", (query,))
        data = self.cur.fetchall()
        if len(data) == 0:
            return None
        return data


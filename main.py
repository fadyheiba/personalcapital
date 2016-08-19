from personalcapital import PersonalCapital, RequireTwoFactorException, TwoFactorVerificationModeEnum
import getpass
import json
import logging
import os
import ast
from datetime import datetime, timedelta

class PewCapital(PersonalCapital):
    """
    Extends PersonalCapital to save and load session
    So that it doesn't require 2-factor auth every time
    """
    def __init__(self):
        PersonalCapital.__init__(self)
        self.__session_file = 'session.json'

    def load_session(self):
        try:
            with open(self.__session_file) as data_file:    
                cookies = {}
                try:
                    cookies = json.load(data_file)
                except ValueError as err:
                    logging.error(err)
                self.set_session(cookies)
        except IOError as err:
            logging.error(err)

    def save_session(self):
        with open(self.__session_file, 'w') as data_file:
            data_file.write(json.dumps(self.get_session()))

def get_email():
    email = os.getenv('PEW_EMAIL')
    if not email:
        print('You can set the environment variables for PEW_EMAIL and PEW_PASSWORD so the prompts don\'t come up every time')
        return raw_input('Enter email:')
    return email

def get_password():
    password = os.getenv('PEW_PASSWORD')
    if not password:
        return getpass.getpass('Enter password:')
    return password

def print_dict(dictionary, ident = '', braces=1):
    """ Recursively prints nested dictionaries."""

    for key, value in dictionary.iteritems():
        if isinstance(value, dict):
            print '%s%s%s%s' %(ident,braces*'[',key,braces*']') 
            print_dict(value, ident+'  ', braces+1)
        else:
            print ident+'%s = %s' %(key, value)
    
def main():
    email, password = get_email(), get_password()
    pc = PewCapital()
    pc.load_session()

    try:
        pc.login(email, password)
    except RequireTwoFactorException:
        pc.two_factor_challenge(TwoFactorVerificationModeEnum.SMS)
        pc.two_factor_authenticate(TwoFactorVerificationModeEnum.SMS, raw_input('code: '))
        pc.authenticate_password(password)


    balancespath = 'C:/Users/user/Dropbox/Big Data/Apps/IoT App/PersonalCapitalScraper/Balances.csv'
    balancesfile = open(balancespath, 'w')
    balancesfile.write('Bank,Account,Balance,RefreshDate\n')
    
    accountsResponse = pc.fetch('/newaccount/getAccounts')
    accounts = accountsResponse.json()['spData']['accounts']
    
    for account in accounts:
        print account.keys()
        print '\n'
        balancesfile.write(str(account['originalFirmName']).replace(',','.') + ',' +
                          str(account['name']).replace(',','.') + ',' +
                          str(account['balance']) + ',' +
                          str(account['lastRefreshed'])[:10].replace(',','.') + ',' +
                          '\n'
                          )
    balancesfile.close()  

    
    transactionspath = 'C:/Users/user/Dropbox/Big Data/Apps/IoT App/PersonalCapitalScraper/Transactions.csv'
    transactionsfile = open(transactionspath, 'w')
    transactionsfile.write('Date,Account,CategoryID,SimpleDescription,Amount,Currency,OriginalDescription,TransactionID,isCashOut\n')
    
    categoriespath = 'C:/Users/user/Dropbox/Big Data/Apps/IoT App/PersonalCapitalScraper/Categories.csv'
    categoriesfile = open(categoriespath, 'w')
    categoriesfile.write('CategoryID,CategoryName,CategoryType\n')
    
    now = datetime.now()
    date_format = '%Y-%m-%d'
    days = 999
    start_date = (now - (timedelta(days=days+1))).strftime(date_format)
    end_date = (now - (timedelta(days=1))).strftime(date_format)
    transactions_response = pc.fetch('/transaction/getUserTransactions', {
        'sort_cols': 'transactionTime',
        'sort_rev': 'true',
        'page': '0',
        'rows_per_page': '100',
        'startDate': start_date,
        'endDate': end_date,
        'component': 'DATAGRID'
    })
    
    transactions = transactions_response.json()['spData']['transactions']
    for transaction in transactions:
        transactionsfile.write(str(transaction['transactionDate']).replace(',','.') + ',' +
                               str(transaction['accountName']).replace(',','.') + ',' +
                               str(transaction['categoryId']).replace(',','.') + ',' +
                               str(transaction['simpleDescription']).replace(',','.') + ',' +
                               str(transaction['amount']) + ',' +
                               str(transaction['currency']).replace(',','.') + ',' +
                               str(transaction['originalDescription']).replace(',','.') + ',' +
                               str(transaction['userTransactionId']).replace(',','.') + ',' +
                               str(transaction['isCashOut']).replace(',','.') + ',' +
                              '\n'
                              )

    incomeCategories = transactions_response.json()['spData']['incomeCategories']
    expenseCategories = transactions_response.json()['spData']['expenseCategories']
    
    for category in expenseCategories:
        categoriesfile.write(  str(category['transactionCategoryId']).replace(',','.') + ',' +
                               str(category['name']).replace(',','.') + ',' +
                               str(category['type']).replace(',','.') + ',' +
                              '\n'
                              )
    for category in incomeCategories:
        categoriesfile.write(  str(category['transactionCategoryId']).replace(',','.') + ',' +
                               str(category['name']).replace(',','.') + ',' +
                               str(category['type']).replace(',','.') + ',' +
                              '\n'
                              )
    categoriesfile.close()
    transactionsfile.close()
    
    pc.save_session()
       
if __name__ == '__main__':
    main()

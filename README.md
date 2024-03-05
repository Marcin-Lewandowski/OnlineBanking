
![Imperial Bank](https://github.com/Marcin-Lewandowski/OnlineBanking/blob/master/static/imperialbankmini.jpg )


1. [Project description](#project-description)
2. [Project structure](#project-structure)
3. [Main features of the application](#main-features-of-the-application)
4. [Usage examples](#usage-examples)
5. [Instructions for starting the application](#instructions-for-starting-the-application)
6. [License](#license)





## Project description
Online banking simulation is a project that allows you to simulate the processes that take place while using the bank's services.
On the bank's client side: logging in, transferring money to the recipient's account, reviewing transactions, 
handling standing orders, recurring payments, i.e. repayment of loan installments, changing the user's personal data 
and using the help center, e.g. sending messages and reviewing all messages sent to the help center.
On the banking system administrator's side, it is possible to: add customers to the banking system, create bank accounts, 
remove customers from the database, change passwords for customers, block and unblock access to the account, 
filter customer accounts, change customer personal data, display customer transactions in the form table and chart, 
filtering customer transactions based on various criteria, handling customer requests (help center), 
displaying banking system statistics (charts), filtering direct debit and standing orders, e.g. Loans, filtering and displaying system logs.

This is a portfolio project and shows my programming capabilities. 
I created the project using the Python programming language and the Flask framework. 
Main libraries I used during the project: Flask, Flask-WTF, Flask-Login, SQLAlchemy, Flask-APScheduler, 
Flask-Talisman, Pandas, Matplotlib, io, base64, csv, reportlab, Werkzeug.

## Project structure
The project is divided into directories [modules] and files. 
Forms (stores the classes of forms used in the project), instance (database), models (declarations of tables from the database), 
routes (routes in the form of functions) static (static files, images, css files, JavaScript scripts), templates (html templates). 
Files in the main application directory: app.py (main execution file), app.log (banking system log file), config.py and README.md

## Main features of the application
On the bank's client side.

Login to the banking system:

The login function handles the user login process in the web application. 
When a user submits a login form (POST method), the function checks whether the login information is valid using the form data. 
If the user is already logged in, he or she is redirected to the appropriate dashboard page depending on the role (admin or regular user).
Key steps performed by the function:
1. Check if a login attempt was made by a user other than the last user and reset the login attempt counter if necessary.
2. Checking if the user is not blocked (based on the LockedUsers list). If present, a page informing about a blocked account will be displayed.
3. Verification whether the user exists and whether the password is correct. If successful, the user is logged in and the login attempt counter is reset.
4. If the password is incorrect, an error message is displayed and the login attempt counter is incremented. 
After exceeding the limit of attempts (3), the user account is blocked, added to the blocked list and a page with information about the blocked account is displayed.
5. In case of form validation errors or the user not being found, the login form is displayed again with an appropriate message.

This feature provides a mechanism to defend against brute force attacks by limiting the number of login attempts 
and disabling accounts when the allowed number of failed attempts is exceeded.



Transferring money to an external account:

The transfer function carries out the process of transferring funds between user accounts in the web application. This process is protected by a login requirement (@login_required). The function uses the TransferForm form to collect transaction data, such as the sort code and recipient's account number, amount, transaction description and confirmation of the password of the user making the transfer.

Key steps performed by the function:

1. Verification of the correctness of the password of the user initiating the transfer.
2. Checking whether the recipient's account exists based on the provided sort code and account number.
3. Check whether the user is trying to transfer funds to his own account.
4. Checking whether the user has sufficient funds to complete the transfer.
5. Implementation of transfer logic, including:
Update the sender's balance by adding a new transaction with the appropriate amount deducted.
Update the customer's balance by adding a transaction with the added amount.
6. If successful, the user is informed about the success of the transfer and redirected to the dashboard page.
7. Exception handling - if an error occurs, the transaction is rolled back and the user is informed about the error.

Finally, if the form is not completed correctly or has not been submitted yet, the user receives a list of their transactions and a dashboard view to complete the form again. This feature ensures that funds are transferred securely between accounts by password-protecting transactions and checking the availability of funds.


















## Usage examples
Przykłady użycia tutaj...

## Instructions for starting the application
Instrukcje dotyczące uruchamiania aplikacji tutaj...

## License


The MIT License (MIT)

Copyright (c) 2024 Marcin Lewandowski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

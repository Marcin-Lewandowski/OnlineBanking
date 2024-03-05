
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

The transfer function carries out the process of transferring funds between user accounts in the web application. 
This process is protected by a login requirement (@login_required). 
The function uses the TransferForm form to collect transaction data, such as the sort code and recipient's account number, 
amount, transaction description and confirmation of the password of the user making the transfer.

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

Finally, if the form is not completed correctly or has not been submitted yet, the user receives a list of their transactions and a dashboard view to complete the form again. 
This feature ensures that funds are transferred securely between accounts by password-protecting transactions and checking the availability of funds.


Recurring payment processing:

The process_ddso_payments function is used to process pending Direct Debit Standing Order (DDSO) payments in the web application. 
It works in the application context (app.app_context()), which allows access to the database and application models from a script 
run regardless of the context of the HTTP request.

The main steps carried out by the function are:

1. Searches the database for all pending DDSO payments whose next payment date is equal to or earlier than the current date.
2. For each pending payment:
Designates a recipient based on the username (recipient_name) and finds their ID.
Prints information about the recipient and sender of the payment, including their balance.
Prepares data for transaction execution, including updating the balance of the sender and recipient.
Creates new transactions in the database for the sender and receiver, subtracting and adding the payment amount respectively.
Updates the next payment date depending on the payment frequency (daily, monthly).
Commits changes to the database.
3. Handles possible exceptions by rolling back changes to the database in case of errors and displaying detailed error information.
4. If there are no pending payments, it informs about this fact.

The feature is an example of automating recurring payment processing, which is crucial for payment management systems, 
offering automatic, timely transfer of funds between user accounts. The function is activated when the application is launched.


The process_loans_payments function is used to automatically process loan installment payments in the web application. 
It runs in the application context (app.app_context()), which allows interaction with the database and application models.

Main steps performed by the function:

1. Downloads from the database all loan installments whose next payment date has passed or is today's date.
2. For each pending loan installment:
Designates the payee as "Imperial Bank" (for example with id = 25) and prints its username.
Designates the payer based on the userid from the credit table and prints his username.
3. Processes payment, including:
Updates the sender's balance by subtracting the credit installment amount.
Updates the recipient's (bank) balance by adding the installment amount.
Updates your loan information, including the number of installments paid and outstanding, the remaining amount due, and the next payment date.
If all installments are repaid, the loan record is deleted from the database.
4. Approves changes to the database.
5. Handles exceptions by rolling back database changes in case of errors and printing detailed error information.

The function is an example of automating the processing of loan installments, enabling timely repayment of liabilities and updating 
of credit data without the need for manual intervention by the user or a bank employee. The function is activated when the application is launched.

Editing user data:

The edit_profile function in the web application allows logged-in users to edit and update their profile information, such as email address, 
phone number, and country. It is available at '/edit_profile' and supports HTTP GET and POST methods.
GET method: When the user first visits the profile edit page, the form is pre-filled with the current user data 
(email, phone number, country), retrieved from the current_user object.

POST method: Once the form is submitted, the function validates the form data. If validation succeeds, 
it updates the user profile in the database with the new data from the form. 
After successfully updating the data, the user is redirected to the account details page, 
where a message about the success of the operation is displayed.
If an error occurs while saving changes to the database (e.g. due to an exception), 
the transaction is rolled back and the user is informed about the error with a message, with the option to return to the data editing form.
Additionally, the function logs profile data update operations and possible errors using a logging mechanism (logger), 
which allows tracking important changes made by users and diagnosing problems.


Help Center:

There is a help center where the customer/user can create a message/request with a unique reference number 
which is needed to track all messages in the current thread. 
The user can also add messages to an existing thread and delete messages from a thread with a specific reference number.


Main functions available in the admin panel.

Adding clients to the banking system:

The add_customer function in the web application allows administrators to add new users (customers). 
It is available at '/add_customer' and supports HTTP GET and POST methods. 
The function requires that the user is logged in and has administrator privileges, 
which is verified by the @login_required and @admin_required decorators.

GET method: Used to display the form for adding a new user. The form is generated based on the AddCustomerForm class.

POST method: It is used when the form is submitted. The function verifies form data:

If the data is correct, the function checks whether a user with the given email address or username already exists. 
If the user already exists, an error message is displayed.
If the user does not exist, it creates a new user with the data retrieved from the form, 
including the password hashed using generate_password_hash, and adds it to the database. 
After successfully adding the user, a success message is displayed and you are redirected to the administrator dashboard.
If form data validation fails, the user is informed about the error and also redirected to the administrator dashboard.

This feature is a key part of the user management system, allowing administrators to easily 
add new accounts without direct access to the database, which increases the security and efficiency of working with the system.











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

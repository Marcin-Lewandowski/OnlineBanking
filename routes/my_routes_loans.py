from flask import Blueprint, flash, url_for, redirect
from flask_login import current_user, login_required
from datetime import date
from models.models import Transaction, db, Loans
from datetime import timedelta, date


apply_consumer_loan_bp = Blueprint('apply_consumer_loan_bp', __name__)

@apply_consumer_loan_bp.route('/apply_consumer_loan', methods=['GET', 'POST'])
@login_required
def apply_consumer_loan():
    """
    Processes applications for consumer loans by logged-in users.

    This route allows logged-in users to apply for a consumer loan. It first checks if the user already has
    a loan with the status 'granted' to prevent multiple active loans. If an active loan exists, the user is
    notified and redirected to a relevant page.

    If no active loan exists, the function creates a new loan with predefined parameters (such as the loan amount,
    interest rate, and repayment terms) and assigns it to the user. It also performs financial transactions to
    simulate the disbursement of the loan amount from Imperial Bank to the user, updating the respective balances
    in the transactions table.

    The process involves:
    - Checking for existing active loans.
    - Creating a new loan record with 'granted' status if no active loan exists.
    - Simulating the loan disbursement by creating transaction records for both the bank and the user,
      updating their balances accordingly.

    In case of successful loan grant, a success message is flashed, and the user is redirected. If any part
    of the transaction fails (e.g., due to a database error), the operation is rolled back, an error message
    is flashed, and the user is redirected to a fallback page.

    Returns:
        A redirect to a specified page depending on the outcome of the loan application process (my_loans.html or
        consumer_loan in case of error).
    """
    in_progress_customer_loan = Loans.query.filter_by(user_id=current_user.id, loan_status='granted').first()
    
    if in_progress_customer_loan:
        flash('You have one loan in progress!', 'danger')
        return redirect(url_for('consumer_loan'))
        
    else:
        new_consumer_loan = Loans(user_id=current_user.id,
                                recipient = 'Imperial Bank',
                                product_id = 'Consumer loan',
                                transaction_type = 'SO',
                                nominal_amount = 5000,
                                interest = '7%',
                                installment_amount = 237.50,
                                installments_number = 24,
                                installments_paid = 0,
                                installments_to_be_paid = 24,
                                total_amount_to_be_repaid = 5700,
                                remaining_amount_to_be_repaid = 5700,
                                loan_cost = 700,
                                interest_type = 'fixed',
                                loan_status = 'granted',
                                frequency = 30,
                                loan_start_date = date.today(),
                                loan_end_date = date.today() + timedelta(days=(24 * 30)),
                                next_payment_date = date.today() + timedelta(days=30),
                                currency_code = 'GBP',
                                loan_purpose = 'Customer loan',
                                notes = '')
        db.session.add(new_consumer_loan)
        
        # Download Imperial Bank last transaction
        last_ib_transaction = Transaction.query.filter_by(user_id=25).order_by(Transaction.id.desc()).first()
        
        # Download last customer transaction
        last_customer_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        
        # The logic of making a transfer
        try:
            # Preparation of data for transactions
            transaction_date = date.today()
            
            # Imperial Bank balance update
            new_ib_balance = last_ib_transaction.balance - 5000
            new_ib_transaction = Transaction(user_id=25, 
                                            transaction_date=transaction_date,
                                            transaction_type='FPO',
                                            sort_code=last_ib_transaction.sort_code,
                                            account_number=last_ib_transaction.account_number,
                                            transaction_description='Customer loan granted',
                                            debit_amount=5000,
                                            credit_amount = 0,
                                            balance=new_ib_balance)
            db.session.add(new_ib_transaction)
            
            
            # Recipient balance update
            new_customer_balance = last_customer_transaction.balance + 5000
            new_customer_transaction = Transaction(user_id=current_user.id, 
                                                    transaction_date=transaction_date,
                                                    transaction_type='FPI',
                                                    sort_code=last_customer_transaction.sort_code,
                                                    account_number=last_customer_transaction.account_number,
                                                    transaction_description='Customer loan granted',
                                                    debit_amount = 0,
                                                    credit_amount=5000,
                                                    balance=new_customer_balance)
            db.session.add(new_customer_transaction)
            db.session.commit()
            
            flash('Consumer loan granted!', 'success')
            return redirect(url_for('my_loans'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return redirect(url_for('consumer_loan'))
        
        
        
apply_car_loan_bp = Blueprint('apply_car_loan_bp', __name__)
        
@apply_car_loan_bp.route('/apply_car_loan', methods=['GET', 'POST'])
@login_required
def apply_car_loan():
    """
    Facilitates the application process for a car loan for logged-in users.

    Just like the `apply_consumer_loan` function, this route checks if the user already has an active
    loan marked as 'granted' to prevent the accumulation of multiple concurrent loans. If an existing
    loan is found, it notifies the user and redirects them to a relevant page without proceeding with
    the application.

    If no active loan is detected, the function initiates the creation of a new car loan with predefined
    parameters such as the loan amount, interest rate, repayment schedule, and loan duration. These
    parameters are specifically tailored to meet the conditions of a car loan product. It then simulates
    the financial transaction that disburses the loan amount from the bank to the user, updating the
    transaction records for both parties to reflect this change.

    The function encapsulates the following steps:
    - Verifying the absence of an in-progress loan for the user.
    - Creating a new loan record with the 'granted' status and car loan-specific terms.
    - Executing the disbursement transaction, including updating the bank's and user's balance.
    - Handling any exceptions that occur during the process to ensure data integrity.

    On successful loan approval and disbursement, the user is informed via a success message. In case of
    any failures during the process, the operation is rolled back, and the user is notified of the failure.

    Returns:
        A redirect to a specified route - my_loans.html or to a fallback page car_loan.html.
    """
    in_progress_customer_loan = Loans.query.filter_by(user_id=current_user.id, loan_status='granted').first()
    
    if in_progress_customer_loan:
        flash('You have one loan in progress!', 'danger')
        return redirect(url_for('car_loan'))
        
    else:
        new_car_loan = Loans(user_id=current_user.id,
                                recipient = 'Imperial Bank',
                                product_id = 'Car loan',
                                transaction_type = 'SO',
                                nominal_amount = 8000,
                                interest = '6%',
                                installment_amount = 706.67,
                                installments_number = 12,
                                installments_paid = 0,
                                installments_to_be_paid = 12,
                                total_amount_to_be_repaid = 8480,
                                remaining_amount_to_be_repaid = 8480,
                                loan_cost = 480,
                                interest_type = 'fixed',
                                loan_status = 'granted',
                                frequency = 30,
                                loan_start_date = date.today(),
                                loan_end_date = date.today() + timedelta(days=(12 * 30)),
                                next_payment_date = date.today() + timedelta(days=30),
                                currency_code = 'GBP',
                                loan_purpose = 'Car loan',
                                notes = '')
        db.session.add(new_car_loan)
        
        # Download Imperial Bank last transaction
        last_ib_transaction = Transaction.query.filter_by(user_id=25).order_by(Transaction.id.desc()).first()
        
        # Download last customer transaction
        last_customer_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        
        # The logic of making a transfer
        try:
            # Preparation of data for transactions
            transaction_date = date.today()
            
            # Imperial Bank balance update
            new_ib_balance = last_ib_transaction.balance - 8000
            new_ib_transaction = Transaction(user_id=25, 
                                                transaction_date=transaction_date,
                                                transaction_type='FPO',
                                                sort_code=last_ib_transaction.sort_code,
                                                account_number=last_ib_transaction.account_number,
                                                transaction_description='Car loan granted',
                                                debit_amount=8000,
                                                credit_amount = 0,
                                                balance=new_ib_balance)
            
            db.session.add(new_ib_transaction)
            
            # Recipient balance update
            new_customer_balance = last_customer_transaction.balance + 8000
            new_customer_transaction = Transaction(user_id=current_user.id, 
                                                    transaction_date=transaction_date,
                                                    transaction_type='FPI',
                                                    sort_code=last_customer_transaction.sort_code,
                                                    account_number=last_customer_transaction.account_number,
                                                    transaction_description='Car loan granted',
                                                    debit_amount = 0,
                                                    credit_amount=8000,
                                                    balance=new_customer_balance)
            db.session.add(new_customer_transaction)
            db.session.commit()
            
            flash('Car loan granted!', 'success')
            return redirect(url_for('my_loans'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return redirect(url_for('car_loan'))
        
        
        
        
        
apply_home_renovation_loan_bp = Blueprint('apply_home_renovation_loan_bp', __name__)     
        
@apply_home_renovation_loan_bp.route('/apply_home_renovation_loan', methods=['GET', 'POST'])
@login_required
def apply_home_renovation_loan():
    """
    Processes applications for home renovation loans for logged-in users.

    This function operates similarly to the `apply_consumer_loan` and `apply_car_loan` functions but is tailored for home renovation loans. 
    It checks if the user already has an active loan marked as 'granted' to prevent overlapping loans. If such a loan exists, 
    the user is notified and redirected to a specific page without processing a new application.

    If no active loan exists, a new home renovation loan application is initiated with predefined parameters, including the loan amount, 
    interest rate, and repayment terms specific to home renovation projects. The function then simulates the financial transaction for 
    the loan amount's disbursement from Imperial Bank to the user, updating transaction records to reflect the new balances.

    Key steps include:
    - Verifying the absence of an in-progress loan for the user.
    - Creating a new loan record with 'granted' status and terms specific to home renovation loans.
    - Executing the disbursement transaction, updating both the bank's and the user's balance records.

    Success or failure of the loan application process is communicated to the user through flash messages, 
    and appropriate redirection is performed to either view the loan status or retry the application in case of failure.

    Returns:
        A redirect to a specified route (my_loans or home_renovation_loan), guiding the user to view their loan status or to 
        retry the application if the process encounters an error.
    """
    in_progress_customer_loan = Loans.query.filter_by(user_id=current_user.id, loan_status='granted').first()
    
    if in_progress_customer_loan:
        flash('You have one loan in progress!', 'danger')
        return redirect(url_for('home_renovation_loan'))
        
    else:
        new_home_renovation_loan = Loans(user_id=current_user.id,
                                    recipient = 'Imperial Bank',
                                    product_id = 'Home renovation loan',
                                    transaction_type = 'SO',
                                    nominal_amount = 15000,
                                    interest = '5.5%',
                                    installment_amount = 485.42,
                                    installments_number = 36,
                                    installments_paid = 0,
                                    installments_to_be_paid = 36,
                                    total_amount_to_be_repaid = 17475,
                                    remaining_amount_to_be_repaid = 17475,
                                    loan_cost = 2475,
                                    interest_type = 'fixed',
                                    loan_status = 'granted',
                                    frequency = 30,
                                    loan_start_date = date.today(),
                                    loan_end_date = date.today() + timedelta(days=(36 * 30)),
                                    next_payment_date = date.today() + timedelta(days=30),
                                    currency_code = 'GBP',
                                    loan_purpose = 'Home renovation loan',
                                    notes = '')
        db.session.add(new_home_renovation_loan)
        
        # Download Imperial Bank last transaction
        last_ib_transaction = Transaction.query.filter_by(user_id=25).order_by(Transaction.id.desc()).first()
        
        # Download last customer transaction
        last_customer_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        
        # The logic of making a transfer
        try:
            # Preparation of data for transactions
            transaction_date = date.today()
            
            # Imperial Bank balance update
            new_ib_balance = last_ib_transaction.balance - 15000
            new_ib_transaction = Transaction(user_id=25, 
                                                transaction_date=transaction_date,
                                                transaction_type='FPO',
                                                sort_code=last_ib_transaction.sort_code,
                                                account_number=last_ib_transaction.account_number,
                                                transaction_description='Home renovation loan granted',
                                                debit_amount=15000,
                                                credit_amount = 0,
                                                balance=new_ib_balance)
            
            db.session.add(new_ib_transaction)
            
            # Recipient balance update
            new_customer_balance = last_customer_transaction.balance + 15000
            new_customer_transaction = Transaction(user_id=current_user.id, 
                                                    transaction_date=transaction_date,
                                                    transaction_type='FPI',
                                                    sort_code=last_customer_transaction.sort_code,
                                                    account_number=last_customer_transaction.account_number,
                                                    transaction_description='Home renovation loan granted',
                                                    debit_amount = 0,
                                                    credit_amount = 15000,
                                                    balance=new_customer_balance)
            db.session.add(new_customer_transaction)
            db.session.commit()
            
            flash('Home renovation loan granted!', 'success')
            return redirect(url_for('my_loans'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return redirect(url_for('home_renovation_loan'))
        
        
        
        
    
apply_test_loan_bp = Blueprint('apply_test_loan_bp', __name__)
        
@apply_test_loan_bp.route('/apply_test_loan', methods=['GET', 'POST'])
@login_required
def apply_test_loan():
    """
    Facilitates the application and processing of a test loan for logged-in users.

    Similar to other loan application functions, this route checks for the existence of any active loan marked as 'granted' 
    to ensure users do not have multiple loans in progress simultaneously. If an active loan is detected, the user is informed 
    and redirected appropriately without proceeding with a new test loan application.

    In the absence of any active loan, this function initiates the creation of a new test loan with specific parameters designed 
    for testing purposes. These parameters include a nominal amount significantly lower than typical loans, a high-interest rate, 
    a very short repayment period, and immediate repayment frequency. The purpose of such a loan setup is to allow for the testing 
    of the loan processing system without engaging substantial financial resources or long-term commitments.

    The function simulates the financial transaction for disbursing the loan amount from Imperial Bank to the user, including updating 
    the transaction records for both the bank and the user to reflect the new balances. In the event of successful loan approval and 
    disbursement, the user is notified. If the transaction encounters any issues, the operation is rolled back, and the user is informed of the failure.

    Returns:
        A redirect to a specified route (my_loans or test_loan), typically allowing the user to view their loan status or to attempt 
        the application again in case of a process failure.
    """
    in_progress_customer_loan = Loans.query.filter_by(user_id=current_user.id, loan_status='granted').first()
    
    if in_progress_customer_loan:
        flash('You have one loan in progress!', 'danger')
        return redirect(url_for('test_loan'))
        
    else:
        new_test_loan = Loans(user_id=current_user.id,
                                    recipient = 'Imperial Bank',
                                    product_id = 'TEST LOAN',
                                    transaction_type = 'SO',
                                    nominal_amount = 100,
                                    interest = '10%',
                                    installment_amount = 55.00,
                                    installments_number = 2,
                                    installments_paid = 0,
                                    installments_to_be_paid = 2,
                                    total_amount_to_be_repaid = 110,
                                    remaining_amount_to_be_repaid = 110,
                                    loan_cost = 10,
                                    interest_type = 'fixed',
                                    loan_status = 'granted',
                                    frequency = 1,
                                    loan_start_date = date.today(),
                                    loan_end_date = date.today() + timedelta(days=(2 * 1)),
                                    next_payment_date = date.today() + timedelta(days=1),
                                    currency_code = 'GBP',
                                    loan_purpose = 'TEST LOAN',
                                    notes = '')
        db.session.add(new_test_loan)
        
        # Download Imperial Bank last transaction
        last_ib_transaction = Transaction.query.filter_by(user_id=25).order_by(Transaction.id.desc()).first()
        
        # Download last customer transaction
        last_customer_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        
        # The logic of making a transfer
        try:
            # Preparation of data for transactions
            transaction_date = date.today()
            
            # Imperial Bank balance update
            new_ib_balance = last_ib_transaction.balance - 100
            new_ib_transaction = Transaction(user_id=25, 
                                                transaction_date=transaction_date,
                                                transaction_type='FPO',
                                                sort_code=last_ib_transaction.sort_code,
                                                account_number=last_ib_transaction.account_number,
                                                transaction_description='TEST LOAN granted',
                                                debit_amount = 100,
                                                credit_amount = 0,
                                                balance=new_ib_balance)
            
            db.session.add(new_ib_transaction)
            
            # Recipient balance update
            new_customer_balance = last_customer_transaction.balance + 100
            new_customer_transaction = Transaction(user_id=current_user.id, 
                                                    transaction_date=transaction_date,
                                                    transaction_type='FPI',
                                                    sort_code=last_customer_transaction.sort_code,
                                                    account_number=last_customer_transaction.account_number,
                                                    transaction_description='TEST LOAN granted',
                                                    debit_amount = 0,
                                                    credit_amount = 100,
                                                    balance=new_customer_balance)
            db.session.add(new_customer_transaction)
            db.session.commit()
            
            flash('TEST LOAN granted!', 'success')
            return redirect(url_for('my_loans'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return redirect(url_for('test_loan'))

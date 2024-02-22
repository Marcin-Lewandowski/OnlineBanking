from flask import Blueprint, flash, url_for, redirect
from flask_login import current_user, login_required
from datetime import date
from models.models import Transaction, db, Loans
from datetime import timedelta, date


apply_consumer_loan_bp = Blueprint('apply_consumer_loan_bp', __name__)

@apply_consumer_loan_bp.route('/apply_consumer_loan', methods=['GET', 'POST'])
@login_required
def apply_consumer_loan():
    
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

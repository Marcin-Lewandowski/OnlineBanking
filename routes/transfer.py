from flask import Blueprint, render_template, request, session, flash, url_for, redirect

from flask_login import current_user, login_required, login_user
from forms.forms import TransferForm, LoginForm
from datetime import date
from models.models import Users, Transaction, db



transfer_bp = Blueprint('transfer_bp', __name__)

@transfer_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    form = TransferForm()
    print(1)

    if form.validate_on_submit():
        print(2)
        recipient_sort_code = form.recipient_sort_code.data
        recipient_account_number = form.recipient_account_number.data
        amount = form.amount.data
        transaction_description = form.transaction_description.data
        confirm_password = form.confirm_password.data
        
        # Sprawdź, czy hasło jest poprawne
        if not current_user.check_password(confirm_password):
            print(3)
            flash('Invalid password.', 'danger')
            return redirect(url_for('dashboard'))
     
        # Sprawdź, czy odbiorca istnieje, sprawdza po sort code i account number
        recipient = Users.query.join(Transaction).filter(Transaction.account_number == recipient_account_number, Transaction.sort_code == recipient_sort_code).first()
        if not recipient:
            print(4)
            flash('Recipient account not found.', 'danger')
            return redirect(url_for('dashboard')) 

        
        # Pobierz ostatnią transakcję nadawcy, aby sprawdzić jego saldo
        last_sender_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        
        # Sprawdź czy sort code i account_number są danymi wysyłającego
        if recipient_sort_code == last_sender_transaction.sort_code and recipient_account_number == last_sender_transaction.account_number:
            flash('You can not send money to your own account!', 'danger')
            return redirect(url_for('dashboard'))
        
        
        if not last_sender_transaction or last_sender_transaction.balance < amount:
            print(5)
            flash('Insufficient funds.', 'danger')
            return redirect(url_for('dashboard')) 
        
        # Logika wykonania przelewu
        try:
            print(6)
            # Przygotowanie wspólnych danych dla transakcji
            transaction_date = date.today()
            
            
            # Aktualizacja salda nadawcy
            last_sender_balance = last_sender_transaction.balance - amount
            new_sender_transaction = Transaction(user_id=current_user.id, 
                                                transaction_date=transaction_date,
                                                transaction_type='FPO',
                                                sort_code=last_sender_transaction.sort_code,
                                                account_number=last_sender_transaction.account_number,
                                                transaction_description=transaction_description,
                                                debit_amount=amount,
                                                credit_amount = 0,
                                                balance=last_sender_balance)
            db.session.add(new_sender_transaction)
            
            
            # Znajdź ostatnią transakcję odbiorcy
            last_recipient_transaction = Transaction.query.filter_by(user_id=recipient.id).order_by(Transaction.id.desc()).first()
            last_recipient_balance = last_recipient_transaction.balance
            
            # Aktualizacja salda odbiorcy
            new_recipient_transaction = Transaction(user_id=recipient.id, 
                                                    transaction_date=transaction_date,
                                                    transaction_type='FPI',
                                                    sort_code=last_recipient_transaction.sort_code,
                                                    account_number=last_recipient_transaction.account_number,
                                                    transaction_description=transaction_description,
                                                    debit_amount = 0,
                                                    credit_amount=amount,
                                                    balance=last_recipient_balance + amount)
            db.session.add(new_recipient_transaction)
            

            # Zatwierdzenie zmian w bazie danych
            db.session.commit()
            flash('Transfer successful!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            print(7)
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return render_template('transfer.html', form=form)
    
    else:
        print(form.errors)   
    print(8)    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)





login_bp = Blueprint('login_bp', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        session.permanent = True
        if form.validate_on_submit():
            user = Users.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                session.permanent = True  # Ustawienie sesji jako trwałej
                flash("Login succesful!")
                print(user.username)
                
                
                # Przekieruj do strony admin_dashboard dla administratora
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                # Przekieruj do strony dashboard dla klienta
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check your username and password.', 'danger')     
                
        return render_template('login.html', form = form)   
        
    # Jeśli użytkownik jest już zalogowany, przekieruj go do odpowiedniej strony
    if current_user.is_authenticated:
        flash("Already Logged In")
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))


    return render_template('login.html', form = form)
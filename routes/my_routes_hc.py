from flask import Blueprint, render_template, request, session, flash, url_for, redirect, abort
from flask_login import current_user, login_required, login_user
from datetime import date
from functools import wraps
from routes.transfer import admin_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import TransferForm, LoginForm, DDSOForm, CreateTransactionForm, EditUserForm, SendQueryForm
from models.models import Users, Transaction, db, DDSO, LockedUsers, SupportTickets
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime


def generate_unique_reference_number(username):
    """
    Generuje unikalny numer referencyjny dla użytkownika.

    :param username: Nazwa użytkownika, która ma zostać dołączona do numeru referencyjnego.
    :return: Unikalny numer referencyjny.
    """
    new_reference_number = SupportTickets.query.count() + 1

    while True:
        # Tworzenie potencjalnie unikalnego numeru referencyjnego
        potential_ref_number = f'{new_reference_number:06}{username}'
        
        # Sprawdzanie, czy numer referencyjny już istnieje
        existing_ticket = SupportTickets.query.filter_by(reference_number=potential_ref_number).first()
        
        if not existing_ticket:
            return potential_ref_number  # Unikalny numer referencyjny został znaleziony
        else:
            new_reference_number += 1  # Zwiększenie liczby i ponowna próba
            print(potential_ref_number)
            
            
                
                
            
send_query_bp = Blueprint('send_query_bp', __name__)                                    # zrobione

@send_query_bp.route('/query_sended', methods=['GET', 'POST']) 
@login_required
def send_query():
    form = SendQueryForm()
    
    if form.validate_on_submit():
        
        if form.category.data == 'general' or form.category.data == 'service problem':
            current_priority = 'normal'
        elif form.category.data == 'money transfer':
            current_priority = 'high'
        elif form.category.data == 'fraud':
            current_priority = 'urgent'
            
        new_query = SupportTickets(user_id = current_user.id,
                                  title = form.title.data,
                                  description = form.description.data,
                                  category = form.category.data,
                                  reference_number = generate_unique_reference_number(current_user.username),
                                  #reference_number = formatted_reference_number,
                                  created_at = datetime.utcnow(),
                                  status = 'new',
                                  priority = current_priority)
        
        db.session.add(new_query)
        # Zatwierdzenie zmian w bazie danych
        db.session.commit()
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('help_center'))
    
    else:
        print(form.errors)  # Wydrukuj błędy formularza
    return render_template('help_center.html', form=form)





process_query_bp = Blueprint('process_query_bp', __name__)                                       # zrobione

@process_query_bp.route('/process_query/<query_ref>', methods=['GET', 'POST'])
@login_required
@admin_required
def process_query(query_ref):
    print("Received reference number:", query_ref)  # Wydruk kontrolny
    # Pobieranie zapytania z bazy danych za pomocą ID
    
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    # Jeśli metoda to GET, renderuj szablon z detalami zapytania do przetworzenia
    return render_template('processing_clients_query.html', all_queries=user_queries, query=last_query)






read_message_bp = Blueprint('read_message_bp', __name__)                                        # zrobione

@read_message_bp.route('/read_message/<query_ref>', methods=['GET', 'POST'])
@login_required
def read_message(query_ref):
    print("Received reference number:", query_ref)  # Wydruk kontrolny
    
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    return render_template('reading_my_messages.html', all_queries=user_queries, query=last_query)





send_message_for_query_bp = Blueprint('send_message_for_query_bp', __name__)                                # zrobione

@send_message_for_query_bp.route('/send_message_for_query/<query_ref>', methods=['GET', 'POST'])
@login_required
@admin_required
def send_message_for_query(query_ref):
    print('query ref = ', query_ref)
    
    # Pobieranie zapytania z bazy danych za pomocą ID
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    # Pobranie danych z formularza
    new_query = SupportTickets(user_id = last_query.user_id,
                                title = last_query.title,
                                description = request.form['description'],
                                category = last_query.category,
                                reference_number = last_query.reference_number,
                                created_at = datetime.utcnow(),
                                status = request.form['status'],
                                priority = last_query.priority)
        
    db.session.add(new_query)
    
    #db.session.delete(SupportTickets.query.get(3))  # - kasuje rekord o ID 3
    #db.session.delete(SupportTickets.query.get(4))

    # Zapisanie zmian w bazie danych
    db.session.commit()
    
    flash('Your response has been sent successfully', 'success')
    return redirect(url_for('process_query_bp.process_query', query_ref=last_query.reference_number))
    
    
    
    
    
send_message_for_message_bp = Blueprint('send_message_for_message_bp', __name__)                                # zrobione
    
@send_message_for_message_bp.route('/send_message_for_message/<query_ref>', methods=['GET', 'POST'])
@login_required
def send_message_for_message(query_ref):
    print("Klient odpowiada na wiadomosc z nr ref: ", query_ref)
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    # Pobranie danych z formularza
    new_query = SupportTickets(user_id = last_query.user_id,
                                title = last_query.title,
                                description = request.form['description'],
                                category = last_query.category,
                                reference_number = last_query.reference_number,
                                created_at = datetime.utcnow(),
                                status = last_query.status,
                                priority = last_query.priority)
        
    db.session.add(new_query)
    db.session.commit()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    flash('Your response has been sent successfully', 'success')
    return render_template('reading_my_messages.html', query_ref=last_query.reference_number, all_queries=user_queries, query=last_query)




delete_messages_for_query_bp = Blueprint('delete_messages_for_query_bp', __name__)                          # zrobione

@delete_messages_for_query_bp.route('/delete_messages_for_query/<query_ref>', methods=['GET', 'POST'])
@login_required
def delete_messages_for_query(query_ref):
    print("Kasuję wszystkie wiadomości dla nr ref: ", query_ref)
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    
    
    messages_quantity = SupportTickets.query.filter_by(reference_number=query_ref).count()
    print(messages_quantity)
    
    return render_template('dmfq.html', query_ref=last_query.reference_number, all_queries=user_queries, query=last_query, messages_quantity = messages_quantity)




delete_query_confirmation_bp = Blueprint('delete_query_confirmation_bp', __name__)                      # zrobione

@delete_query_confirmation_bp.route('/delete_query_confirmation/<query_ref>', methods=['GET', 'POST'])  
@login_required
def delete_query_confirmation(query_ref):
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    
    
    # Sprawdzenie, czy użytkownik ma uprawnienia do usunięcia tych rekordów
    # (to jest ważne, aby uniknąć usuwania rekordów przez nieautoryzowane osoby)
    if last_query.user_id == current_user.id:
        # Usunięcie wszystkich rekordów z danym numerem referencyjnym
        for query in user_queries:
            db.session.delete(query)
        db.session.commit()

        flash('Your query has been deleted successfully', 'success')
    else:
        flash('You do not have permission to delete this query', 'error')

    # Odświeżenie listy rekordów do wyświetlenia
    user_queries = SupportTickets.query.filter_by(user_id=current_user.id).all()

    
    # flash('Your query has been deleted successfully', 'success')
    return redirect(url_for('help_center', query_ref=last_query.reference_number, all_queries = user_queries))
    #return render_template('help_center.html', all_queries = user_queries)
    
    
    
def plot_to_html_img(plt):
    # Zapisz wykres w buforze pamięci
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Koduj jako base64
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()

    return f'<img src="data:image/png;base64,{image_base64}"/>'




show_statement_for_customer_bp = Blueprint('show_statement_for_customer_bp', __name__)

@show_statement_for_customer_bp.route('/show_statement_for_customer/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def show_statement_for_customer(username):
    all_locked_users = LockedUsers.query.all()
    # Pobierz użytkownika na podstawie nazwy użytkownika
    user = Users.query.filter_by(username=username).first()
    user_transactions = Transaction.query.filter_by(user_id = user.id).all()  

    # Przygotowanie danych do DataFrame
    transactions_data = [{
        'transaction_type': txn.transaction_type,
        'debit_amount': txn.debit_amount,
        'credit_amount': txn.credit_amount
    } for txn in user_transactions]

    # Tworzenie DataFrame
    transactions_df = pd.DataFrame(transactions_data)

    # Tworzenie nowej kolumny 'amount' poprzez sumowanie 'debit_amount' i 'credit_amount'
    transactions_df['amount'] = transactions_df['debit_amount'] + transactions_df['credit_amount']

    # Zachowanie tylko kolumn 'transaction_type' i 'amount'
    final_df = transactions_df[['transaction_type', 'amount']]
    
    # Grupowanie danych według 'transaction_type' i sumowanie 'amount'
    grouped_data = final_df.groupby('transaction_type')['amount'].sum()

    # Tworzenie wykresu kołowego
    plt.figure(figsize=(10, 7))
    plt.pie(grouped_data, labels=grouped_data.index, autopct='%1.1f%%', startangle=140)
    plt.title('Suma transakcji według typu')
    
    # Konwertuj wykres na HTML img
    plot_html_img = plot_to_html_img(plt)
    
    return render_template('admin_dashboard_cam.html',  all_locked_users = all_locked_users, all_transactions = user_transactions, user = user, plot_html_img = plot_html_img)




edit_customer_information_bp = Blueprint('edit_customer_information_bp', __name__)

@edit_customer_information_bp.route('/edit_customer_information/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_customer_information(username):
    
    user = Users.query.filter_by(username=username).first()
    
    return render_template('edit_customer_information.html', user = user)
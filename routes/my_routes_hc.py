from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import current_user, login_required
from routes.transfer import admin_required
from forms.forms import SendQueryForm
from models.models import Users, Transaction, db, LockedUsers, SupportTickets
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime


def generate_unique_reference_number(username):
    """
    Generates a unique reference number for the user.

    :param username: The username to attach to the reference number.
    :return: Unique reference number.
    """
    new_reference_number = SupportTickets.query.count() + 1

    while True:
        # Creating a potentially unique reference number
        potential_ref_number = f'{new_reference_number:06}{username}'
        
        # Checking if a reference number already exists
        existing_ticket = SupportTickets.query.filter_by(reference_number=potential_ref_number).first()
        
        if not existing_ticket:
            # A unique reference number has been created
            return potential_ref_number
        else:
            new_reference_number += 1 
            
            
                
                
            
send_query_bp = Blueprint('send_query_bp', __name__)                                    

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
                                  created_at = datetime.utcnow(),
                                  status = 'new',
                                  priority = current_priority)
        
        db.session.add(new_query)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('help_center'))
    else:
        print(form.errors) 
    return render_template('help_center.html', form=form)





process_query_bp = Blueprint('process_query_bp', __name__)                                  

@process_query_bp.route('/process_query/<query_ref>', methods=['GET', 'POST'])
@login_required
@admin_required
def process_query(query_ref):
    
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    return render_template('processing_clients_query.html', all_queries=user_queries, query=last_query)





read_message_bp = Blueprint('read_message_bp', __name__)                             

@read_message_bp.route('/read_message/<query_ref>', methods=['GET', 'POST'])
@login_required
def read_message(query_ref):
    
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    return render_template('reading_my_messages.html', all_queries=user_queries, query=last_query)





send_message_for_query_bp = Blueprint('send_message_for_query_bp', __name__)                                

@send_message_for_query_bp.route('/send_message_for_query/<query_ref>', methods=['GET', 'POST'])
@login_required
@admin_required
def send_message_for_query(query_ref):
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    # downloading data from the form
    new_query = SupportTickets(user_id = last_query.user_id,
                                title = last_query.title,
                                description = request.form['description'],
                                category = last_query.category,
                                reference_number = last_query.reference_number,
                                created_at = datetime.utcnow(),
                                status = request.form['status'],
                                priority = last_query.priority)
        
    db.session.add(new_query)
    db.session.commit()
    
    flash('Your response has been sent successfully', 'success')
    return redirect(url_for('process_query_bp.process_query', query_ref=last_query.reference_number))
    
    
    
    
    
send_message_for_message_bp = Blueprint('send_message_for_message_bp', __name__)        
    
@send_message_for_message_bp.route('/send_message_for_message/<query_ref>', methods=['GET', 'POST'])
@login_required
def send_message_for_message(query_ref):
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    # downloading data from the form
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




delete_messages_for_query_bp = Blueprint('delete_messages_for_query_bp', __name__)

@delete_messages_for_query_bp.route('/delete_messages_for_query/<query_ref>', methods=['GET', 'POST'])
@login_required
def delete_messages_for_query(query_ref):
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    
    
    messages_quantity = SupportTickets.query.filter_by(reference_number=query_ref).count()
    print(messages_quantity)
    
    return render_template('dmfq.html', query_ref=last_query.reference_number, all_queries=user_queries, query=last_query, messages_quantity = messages_quantity)




delete_query_confirmation_bp = Blueprint('delete_query_confirmation_bp', __name__)

@delete_query_confirmation_bp.route('/delete_query_confirmation/<query_ref>', methods=['GET', 'POST'])  
@login_required
def delete_query_confirmation(query_ref):
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    
    
    # Checking if the user has permission to delete these records (this is important to avoid unauthorized people deleting records)
    if last_query.user_id == current_user.id:
        # Deleting all records with a given reference number
        for query in user_queries:
            db.session.delete(query)
        db.session.commit()

        flash('Your query has been deleted successfully', 'success')
    else:
        flash('You do not have permission to delete this query', 'error')

    # Refreshes the list of records to be displayed
    user_queries = SupportTickets.query.filter_by(user_id=current_user.id).all()

    
    return redirect(url_for('help_center', query_ref=last_query.reference_number, all_queries = user_queries))
    
    
    
def plot_to_html_img(plt):
    # Save the graph to the memory buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()

    return f'<img src="data:image/png;base64,{image_base64}"/>'




show_statement_for_customer_bp = Blueprint('show_statement_for_customer_bp', __name__)

@show_statement_for_customer_bp.route('/show_statement_for_customer/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def show_statement_for_customer(username):
    all_locked_users = LockedUsers.query.all()
    # Get user based on username
    user = Users.query.filter_by(username=username).first()
    user_transactions = Transaction.query.filter_by(user_id = user.id).all()  

    # Data preparation do DataFrame
    transactions_data = [{
        'transaction_type': txn.transaction_type,
        'debit_amount': txn.debit_amount,
        'credit_amount': txn.credit_amount
    } for txn in user_transactions]

    # Creating DataFrame
    transactions_df = pd.DataFrame(transactions_data)

    # Creating a new 'amount' column by summing 'debit_amount' and 'credit_amount'
    transactions_df['amount'] = transactions_df['debit_amount'] + transactions_df['credit_amount']

    # Keeping only 'transaction_type' and 'amount' columns
    final_df = transactions_df[['transaction_type', 'amount']]
    
    # Grouping data by 'transaction_type' and summing 'amount'
    grouped_data = final_df.groupby('transaction_type')['amount'].sum()

    # Create a pie chart
    plt.figure(figsize=(10, 7))
    plt.pie(grouped_data, labels=grouped_data.index, autopct='%1.1f%%', startangle=140)
    plt.title('Total transactions by type')
    
    # Convert chart to HTML img
    plot_html_img = plot_to_html_img(plt)
    
    return render_template('admin_dashboard_cam.html',  all_locked_users = all_locked_users, all_transactions = user_transactions, user = user, plot_html_img = plot_html_img)




edit_customer_information_bp = Blueprint('edit_customer_information_bp', __name__)

@edit_customer_information_bp.route('/edit_customer_information/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_customer_information(username):
    
    user = Users.query.filter_by(username=username).first()
    
    return render_template('edit_customer_information.html', user = user)
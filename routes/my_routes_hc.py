from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import current_user, login_required
from routes.transfer import admin_required
from forms.forms import SendQueryForm
from models.models import Users, Transaction, db, LockedUsers, SupportTickets
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from routes.my_routes_admin import plot_to_html_img


def generate_unique_reference_number(username):
    """
    Generates a unique reference number for a support ticket based on the given username.

    This function creates a unique reference number by appending the username to a
    base number derived from the total count of support tickets in the database plus
    one, ensuring sequential uniqueness. The base number is zero-padded to ensure a
    fixed length for the numeric portion, enhancing readability and standardization
    of reference numbers.

    The uniqueness of the generated reference number is verified by querying the
    SupportTickets database. If a duplicate is found (indicating the proposed
    reference number already exists), the base number is incremented, and the process
    repeats until a unique reference number is generated.

    This approach ensures that each support ticket can be uniquely identified and
    referenced, facilitating efficient tracking and management of support queries.

    Args:
        username (str): The username of the user submitting the support ticket, which
                        is used as part of the reference number to ensure its uniqueness
                        and to provide a link back to the user.

    Returns:
        str: A unique reference number for the support ticket, combining a sequential
             number and the user's username (e.g., '000001username').
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
    """
    Processes the submission of a new support ticket via a web form.

    This route, accessible to all logged-in users, allows users to submit support
    tickets through a form. The form captures details such as the ticket's title,
    description, and category. Based on the selected category, the ticket is
    automatically assigned a priority level ('normal', 'high', or 'urgent').

    The logic for priority assignment is as follows:
    - General inquiries or service problems are assigned a 'normal' priority.
    - Money transfer issues are considered 'high' priority.
    - Fraud-related queries receive an 'urgent' priority.

    Upon form submission and validation, a new SupportTickets record is created
    with the provided information, along with a unique reference number generated
    for the ticket, the current timestamp as the creation date, and a default
    status of 'new'. The user's ID (retrieved from the current_user proxy) and
    the calculated priority are also included in the ticket details.

    The ticket is then added to the database, and the user is redirected to the
    help center page, with a success message flashed to confirm the submission.

    If the form submission is invalid (e.g., missing required fields), the form
    errors are printed to the console, and the user is presented again with the
    form to correct the submission.

    Args:
        None

    Returns:
        A redirect to the 'help_center' endpoint if the form submission is successful,
        or the 'help_center.html' template with the form for correction if the submission
        is invalid.
    """
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
    """
    Displays details of all support tickets associated with a specific reference number for processing.

    This route, accessible only to logged-in administrators, is used for reviewing and
    processing support tickets related to a particular query reference number. It is
    particularly useful in scenarios where multiple tickets or follow-ups might be
    associated with a single query, allowing administrators to see the entire
    conversation history.

    The function performs two queries:
    1. Retrieves all support tickets matching the provided reference number. This
       allows the administrator to view all related tickets in their historical
       context.
    2. Retrieves the most recent ticket associated with the reference number, which
       is likely the ticket needing attention or response. This is achieved by
       ordering the tickets by their creation date in descending order and selecting
       the first (most recent) result.

    These queries ensure that administrators have full visibility into the entirety
    of a query's lifecycle, from the initial ticket to the most recent follow-up,
    facilitating informed and efficient processing and response.

    Args:
        query_ref (str): The unique reference number of the query being processed,
                         passed in the URL.

    Returns:
        A rendered template ('processing_clients_query.html') that displays the
        details of all tickets associated with the query reference number and
        highlights the most recent ticket for attention.
    """
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    return render_template('processing_clients_query.html', all_queries=user_queries, query=last_query)





read_message_bp = Blueprint('read_message_bp', __name__)                             

@read_message_bp.route('/read_message/<query_ref>', methods=['GET', 'POST'])
@login_required
def read_message(query_ref):
    """
    Displays the details of the ticket for a user based on a specific reference number.

    This route, accessible to all logged-in users, allows users to view their submitted
    support tickets associated with a particular reference number. It enables users to
    follow up on their queries by reviewing the entire conversation history tied to that
    reference number. This is particularly useful for tracking the progression of a query
    and understanding any responses or follow-up actions taken by the support team.

    The function performs two main operations:
    1. It retrieves all support tickets that match the given reference number. This
       comprehensive retrieval allows the user to see every ticket submitted under that
       reference number, providing a full view of the query's lifecycle.
    2. It identifies the most recent ticket associated with the reference number by
       ordering the tickets by their creation date in descending order and selecting
       the first result. This ensures that the user can quickly access the latest
       update or response in the series of tickets.

    By presenting both the full history and the most recent ticket, users can efficiently
    manage their expectations and next steps regarding their support queries.

    Args:
        query_ref (str): The unique reference number of the user's query, passed in the URL.

    Returns:
        A rendered template ('reading_my_messages.html') that displays both the entire
        history of tickets associated with the query reference number and the most recent
        ticket for easy access to the latest communication.
    """
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    return render_template('reading_my_messages.html', all_queries=user_queries, query=last_query)





send_message_for_query_bp = Blueprint('send_message_for_query_bp', __name__)                                

@send_message_for_query_bp.route('/send_message_for_query/<query_ref>', methods=['GET', 'POST'])
@login_required
@admin_required
def send_message_for_query(query_ref):
    """
    Allows administrators to respond to a user's support ticket by submitting a follow-up ticket.

    Accessible only to logged-in administrators, this route facilitates the support process by
    enabling administrators to directly send responses or updates to users' queries. The response
    or update is submitted as a new support ticket linked to the original query through the
    shared reference number.

    The function first retrieves the most recent ticket associated with the provided reference
    number to ensure that the response aligns with the latest information in the query thread.
    It then creates a new SupportTickets record using data from both the form submission and
    the last query's details. This includes the user ID, title, category, reference number, and
    priority from the last query, while the description and status are taken from the form.

    This method of creating a follow-up ticket ensures continuity in the query handling process,
    allowing both users and administrators to track the progression of a query through its lifecycle.

    Upon successful submission of the follow-up ticket, a success message is flashed, and the
    administrator is redirected back to the query processing page, where they can continue to
    manage other user queries.

    Args:
        query_ref (str): The unique reference number of the query to which the message is a response,
                         passed in the URL.

    Returns:
        A redirect to the query processing route (`process_query_bp.process_query`) with the
        same query reference number, indicating the administrator has successfully added a
        response to the query.
    """
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
    """
    Allows users to submit a follow-up message for an existing support ticket.

    This route is accessible to all logged-in users, enabling them to continue the conversation
    on a support ticket by submitting additional information or follow-up queries. The function
    uses the provided query reference number to locate the most recent ticket within that thread
    and creates a new ticket with details mirroring the last query but with a new description
    and the current timestamp.

    The follow-up message inherits the user ID, title, category, reference number, status, and
    priority from the last query. The description is taken from the form submission, allowing
    users to add new information or context to the ongoing discussion.

    Upon successful submission of the follow-up message, the database is updated with the new
    ticket, and a success message is flashed to notify the user. The user is then redirected
    back to the page displaying their messages, including the newly added message.

    Args:
        query_ref (str): The unique reference number of the query thread to which the message
                         is being added, passed in the URL.

    Returns:
        A rendered template ('reading_my_messages.html') that displays the updated list of
        messages in the query thread, including the newly submitted follow-up message.
    """
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
    """
    Prepares the deletion of messages associated with a specific reference number.

    This route, accessible to all logged-in users, is designed to facilitate the deletion process of
    messages or support tickets linked to a unique query reference number.

    The 'dmfq.html' template rendered by this function will display the reference number of the query,
    and the total number of messages in the query thread.

    Args:
        query_ref (str): The unique reference number for the query thread, provided in the URL, from
                         which messages are considered for deletion.

    Returns:
        A rendered template ('dmfq.html') showing the query's reference number,
        and the total number of messages, assisting users in deciding about message deletion.
    """
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    messages_quantity = SupportTickets.query.filter_by(reference_number=query_ref).count()
    
    return render_template('dmfq.html', query_ref=last_query.reference_number, query=last_query, messages_quantity = messages_quantity)




delete_query_confirmation_bp = Blueprint('delete_query_confirmation_bp', __name__)

@delete_query_confirmation_bp.route('/delete_query_confirmation/<query_ref>', methods=['GET', 'POST'])  
@login_required
def delete_query_confirmation(query_ref):
    """
    Confirms and processes the deletion of all messages associated with a specific reference number.

    This route, accessible to all logged-in users, allows for the deletion of a user's entire query thread
    based on its unique reference number. Before deletion, it verifies that the current user is the author
    of the query to prevent unauthorized deletions. If the current user is verified as the author, all
    messages within the query thread are deleted from the database.

    The function performs a safety check to ensure that only the owner of the query can delete it, enhancing
    the security and integrity of user data. Upon successful deletion, a success message is flashed to inform
    the user. If the user lacks the necessary permissions, an error message is displayed instead.

    After the deletion process, or if the deletion is not permitted, the user is redirected back to the
    help center. 

    Args:
        query_ref (str): The unique reference number of the query to be deleted, provided in the URL.

    Returns:
        A redirect to the 'help_center' page with an updated list of the user's
        queries following the deletion operation.
    """
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
    
    
    


show_statement_for_customer_bp = Blueprint('show_statement_for_customer_bp', __name__)

@show_statement_for_customer_bp.route('/show_statement_for_customer/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def show_statement_for_customer(username):
    """
    Displays a summary of transactions for a specific customer, including a pie chart visualization.

    This route, accessible only to logged-in administrators, retrieves all transactions associated
    with a user identified by their username. It aims to provide a comprehensive overview of the user's
    financial activities within the system, categorized by transaction type.

    The function performs several key steps:
    - Retrieves all locked users, although this data is not directly used in presenting the transaction summary.
    - Fetches the user based on the provided username and then all transactions associated with that user.
    - Prepares the transaction data, specifically focusing on the transaction type and the amounts involved, both debit and credit.
    - Summarizes the transaction data into a pandas DataFrame for easy manipulation and analysis.
    - Creates a new column in the DataFrame to represent the total amount of each transaction by summing the debit and credit amounts.
    - Groups the summarized data by transaction type and calculates the sum of amounts for each type.
    - Generates a pie chart visualization of the transaction summary, showing the proportion of total transactions by type.
    - Converts the pie chart into an HTML image for embedding within the web page.

    Args:
        username (str): The username of the customer whose transaction summary is to be displayed.

    Returns:
        A rendered template ('admin_dashboard_cam.html') that includes the transaction summary and
        the pie chart visualization for the specified user, along with any additional context needed
        for the admin dashboard.
    """
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
    """
    Renders a form for editing information of a specific customer identified by username.

    This route is accessible only to logged-in administrators and provides a user interface
    for editing the details of an existing user. The function fetches the user's details from
    the database based on the provided username. It then passes this information to a template
    which contains a form pre-filled with the user's current information, allowing the administrator
    to make any necessary updates.

    Args:
        username (str): The username of the customer whose information is to be edited.

    Returns:
        A rendered template ('edit_customer_information.html') that includes the form for editing
        the user's details. 
    """
    user = Users.query.filter_by(username=username).first()
    
    return render_template('edit_customer_information.html', user = user)
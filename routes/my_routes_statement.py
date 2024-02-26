from flask import Blueprint, abort
from flask_login import current_user, login_required
from models.models import Transaction
import csv
from reportlab.lib.pagesizes import letter
from flask import make_response, send_file
from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph




def create_transactions_pdf(transactions, username):
    """
    Generates a PDF document listing all transactions for a given user.

    This function creates a PDF file that includes a list of transactions made by the specified user.
    The document starts with an introductory paragraph, followed by a table that displays details of
    each transaction, including date, type, description, debit amount, credit amount, and balance.

    Args:
        transactions (list): A list of transaction objects to be included in the PDF.
        username (str): The username of the user for whom the transactions are being listed.

    Returns:
        BytesIO: A buffer containing the generated PDF content, ready to be saved to a file or sent over
                 a network.

    The PDF document is styled with headers, alignment, fonts, and colors to enhance readability. The
    function uses ReportLab for PDF generation, demonstrating how to combine text and tables within a
    single document dynamically.
    """
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    
    
    # Style for a paragraph
    styles = getSampleStyleSheet()
    
    # Text to place before the table
    
    intro_text = f"Below is a list of all transactions made on your account, {username}: "
    intro = Paragraph(intro_text, styles['Normal'])
    
    # Empty paragraph as a space
    epmty_space = Paragraph("<br/><br/>", styles['Normal'])

    # Column headers
    data = [["Date", "Type", "Description", "Debit amount", "Credit amount", "Balance"]]
    for transaction in transactions:
        data.append([str(transaction.transaction_date), str(transaction.transaction_type), str(transaction.transaction_description), str(transaction.debit_amount), str(transaction.credit_amount), str(transaction.balance)])

    # Table creating
    table = Table(data)

    # Table style (optional)
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(style)

    # Add a table, space, and text to PDF elements
    
    elems = [intro, epmty_space, table]
    pdf.build(elems)

    buffer.seek(0)
    return buffer





download_transactions_bp = Blueprint('download_transactions_bp', __name__)

@download_transactions_bp.route('/download_transactions/<int:user_id>')
@login_required
def download_transactions(user_id):
    """
    Allows users to download a PDF of their transaction history.

    This route checks if the logged-in user is either the user 
    requesting the transaction download or an admin. 
    If not, it aborts the request with a 403 Forbidden status. 
    It then retrieves the user's transactions from the database 
    and generates a PDF document listing these transactions. 
    The PDF is returned as a downloadable file in the HTTP response.

    Args:
        user_id (int): The ID of the user whose transactions are to be downloaded.

    Returns:
        A Flask response object that triggers the download of the transactions PDF file. 
        The file is named 'transactions.pdf' and has the MIME type 'application/pdf'.
    """
    # Checking whether the logged in user has permission to download the transaction
    if current_user.id != user_id and not current_user.is_admin:
        abort(403)

    # Retrieving user transactions from the database
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    # PDF creation
    
    buffer = create_transactions_pdf(transactions, current_user.username)

    # Create an HTTP response with a PDF file
    response = make_response(buffer.getvalue())
    buffer.close()
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.pdf'
    response.mimetype = 'application/pdf'

    return response





def save_transactions_to_csv(transactions, filename):
    """
    Saves a list of transaction objects to a CSV file.

    This function takes a list of transaction objects and a filename as input and writes 
    the transactions to a CSV file with the specified filename. 
    Each transaction is written as a row in the CSV file with the following columns: 
    Date, Type, Description, Debit amount, Credit amount, and Balance.

    Args:
        transactions (list): A list of transaction objects to be saved to the CSV file.
        filename (str): The name of the file where the transactions will be saved.

    The CSV file is created or overwritten in 'write' mode, with UTF-8 encoding to ensure proper handling of special characters.
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Column headers
        writer.writerow(["Date", "Type", "Description", "Debit amount", "Credit amount", "Balance"])

        # Record transaction data
        for transaction in transactions:
            writer.writerow([transaction.transaction_date, transaction.transaction_type, transaction.transaction_description, transaction.debit_amount, transaction.credit_amount, transaction.balance])
            
            
            
            
download_transactions_csv_bp = Blueprint('download_transactions_csv_bp', __name__)    

@download_transactions_csv_bp.route('/download_transactions_csv/<int:user_id>')
@login_required
def download_transactions_csv(user_id):
    """
    Enables users to download their transaction history as a CSV file.

    This route first checks if the logged-in user is authorized to download the transactions, 
    either by being the user in question or by having admin privileges. Unauthorized attempts 
    are blocked with a 403 Forbidden status. Authorized requests proceed to fetch 
    the user's transactions from the database.

    The function then dynamically generates a filename based on the user's username and saves 
    the transactions to a CSV file with this name. Finally, it returns a response that prompts 
    the user's browser to download the generated CSV file.

    Args:
        user_id (int): The ID of the user whose transactions are to be downloaded as a CSV file.

    Returns:
        A Flask `send_file` response that initiates the download of the transactions CSV file. 
        The file is named according to the user's username to personalize the download and 
        facilitate identification of the file's content.
    """
    # Checking whether the logged in user has permission to download the transaction
    if current_user.id != user_id and not current_user.is_admin:
        abort(403)
        
    # Download transaction data (you can add a filter for the current user's transactions here)
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    # Creating a filename
    filename = f"transactions_{current_user.username}.csv"

    # Saving data to a CSV file
    save_transactions_to_csv(transactions, filename)

    # Create a response with a CSV file
    return send_file(filename, as_attachment=True)
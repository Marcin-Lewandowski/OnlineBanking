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
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Column headers
        writer.writerow(["Date", "Type", "Description", "Debit amount", "Credit amount", "Balance"])

        # Record transaction data
        for transaction in transactions:
            writer.writerow([transaction.transaction_date, transaction.transaction_type, transaction.transaction_description, transaction.debit_amount, transaction.credit_amount, transaction.balance])
            
            
            
            
download_transactions_csv_bp = Blueprint('download_transactions_csv_bp', __name__)    
            
@download_transactions_csv_bp.route('/download_transactions_csv')
@login_required
def download_transactions_csv(user_id):
    
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
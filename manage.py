from flask import Flask
from flask.cli import FlaskGroup
from werkzeug.security import generate_password_hash
from app import db, User  # Zaimportuj odpowiednie modele
import click

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ib_database_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Komenda CLI do tworzenia klienta
@app.cli.command('create_client')
@click.option('--username', prompt=True, help='Username for the new client')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for the new client')
def create_client(username, password):
    """Create a new client."""
    with app.app_context():
        existing_client = User.query.filter_by(username=username).first()

        if not existing_client:
            client = User(username=username, role='client')
            client.set_password(password)
            db.session.add(client)
            db.session.commit()
            print(f"Client '{username}' created successfully.")
        else:
            print(f"Client '{username}' already exists.")


if __name__ == '__main__':
    cli = FlaskGroup(app)
    cli()
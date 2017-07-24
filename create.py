from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:ab036sc@localhost/turni'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

from models import Assenze, Dipendenti, MotivoAssenza, Presenze, RapportoLavoro, BustaPaga, DatiEconomici, Reparti, Tally, Utenti, VoceBusta

db.create_all()
db.session.commit()
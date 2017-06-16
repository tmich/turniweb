# coding: utf-8
## models.py
from __future__ import print_function
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Table, Text, Time, text
from sqlalchemy.dialects.mysql.types import BIT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import sys
from decimal import Decimal
from flask.json import jsonify

db = SQLAlchemy()


Base = declarative_base()
metadata = Base.metadata


class Assenze(Base):
    __tablename__ = 'assenze'

    id = Column(Integer, primary_key=True)
    dipendente_id = Column(ForeignKey(u'dipendenti.id'), nullable=False, index=True)
    data_inizio = Column(DateTime, nullable=False)
    data_fine = Column(DateTime, nullable=False)
    giornata_intera = Column(BIT(1), nullable=False)
    motivo_id = Column(ForeignKey(u'motivo_assenza.id'), nullable=False, index=True)
    note = Column(String(200))
    utente_id = Column(ForeignKey(u'utenti.id'), index=True)
    cancellato = Column(Integer, server_default=text("'0'"))

    dipendente = relationship(u'Dipendenti')
    motivo = relationship(u'MotivoAssenza')
    utente = relationship(u'Utenti')
    
    def __init__(self, dipendente_id, data_inizio, data_fine, giornata_intera, motivo_id, note='', utente_id=1):
        self.dipendente_id=dipendente_id
        self.data_inizio=data_inizio
        self.data_fine=data_fine
        self.motivo_id=motivo_id
        self.giornata_intera=giornata_intera
        self.note=note
        self.utente_id=utente_id


t_assenze_bkp = Table(
    'assenze_bkp', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'")),
    Column('dipendente_id', Integer, nullable=False),
    Column('data_inizio', DateTime, nullable=False),
    Column('data_fine', DateTime, nullable=False),
    Column('giornata_intera', BIT(1), nullable=False),
    Column('motivo_id', Integer, nullable=False),
    Column('note', String(200)),
    Column('cancellato', Integer, server_default=text("'0'"))
)


class BustaPaga(Base):
    __tablename__ = 'busta_paga'
    __table_args__ = (
        Index('unique_index', 'dipendente_id', 'mese', 'anno', unique=True),
    )

    id = Column(Integer, primary_key=True)
    dipendente_id = Column(Integer)
    mese = Column(Integer, nullable=False)
    anno = Column(Integer, nullable=False)
    importo = Column(Numeric(7, 2), nullable=False)


class DatiEconomici(Base):
    __tablename__ = 'dati_economici'

    id = Column(Integer, primary_key=True)
    id_dipendente = Column(ForeignKey(u'dipendenti.id', ondelete=u'CASCADE'), nullable=False, index=True)
    mensile_pattuito = Column(Numeric(7, 2))
    ore_giornaliere = Column(Time)
    ore_mensili = Column(Time)
    busta = Column(BIT(1), nullable=False)

    dipendenti = relationship(u'Dipendenti')


class Dipendenti(Base):
    __tablename__ = 'dipendenti'

    id = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False)
    cognome = Column(String(50), nullable=False)
    codice_fiscale = Column(String(16), nullable=False)
    indirizzo = Column(String(100))
    citta = Column(String(50))
    telefono = Column(String(20))
    cellulare = Column(String(15))
    matricola = Column(String(10))
    qualifica = Column(String(20))
    data_assunzione = Column(Date)
    email = Column(String(50))
    data_nascita = Column(Date, nullable=False)
    cancellato = Column(Integer, server_default=text("'0'"))
    id_reparto = Column(Integer, nullable=False, index=True, server_default=text("'1'"))
    indirizzo_domicilio = Column(String(100))
    citta_domicilio = Column(String(50))
    nazionalita = Column(String(50))
    citta_nascita = Column(String(50))
    cellulare2 = Column(String(15))
    presenze = relationship(u'Presenze')
    
    def nome_completo(self):
	return self.cognome + ' ' + self.nome

t_dipendenti_bkp = Table(
    'dipendenti_bkp', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'")),
    Column('nome', String(50), nullable=False),
    Column('cognome', String(50), nullable=False),
    Column('codice_fiscale', String(16), nullable=False),
    Column('indirizzo', String(100)),
    Column('citta', String(50)),
    Column('telefono', String(20)),
    Column('cellulare', String(15)),
    Column('matricola', String(10)),
    Column('qualifica', String(20)),
    Column('data_assunzione', Date),
    Column('email', String(50)),
    Column('data_nascita', Date, nullable=False),
    Column('cancellato', Integer, server_default=text("'0'")),
    Column('id_reparto', Integer, nullable=False, server_default=text("'1'")),
    Column('indirizzo_domicilio', String(100)),
    Column('citta_domicilio', String(50)),
    Column('nazionalita', String(50)),
    Column('citta_nascita', String(50)),
    Column('cellulare2', String(15))
)


class MotivoAssenza(Base):
    __tablename__ = 'motivo_assenza'

    id = Column(Integer, primary_key=True)
    codice = Column(String(5), nullable=False)
    descrizione = Column(String(50), nullable=False)


t_motivo_assenza_bkp = Table(
    'motivo_assenza_bkp', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'")),
    Column('codice', String(5), nullable=False),
    Column('descrizione', String(50), nullable=False)
)


class Presenze(Base):
    __tablename__ = 'presenze'

    id = Column(Integer, primary_key=True)
    dipendente_id = Column(ForeignKey(u'dipendenti.id'), nullable=False, index=True)
    data_inizio = Column(DateTime, nullable=False)
    data_fine = Column(DateTime, nullable=False)
    reparto = Column(String(50), nullable=False)
    note = Column(String(200))
    utente_id = Column(ForeignKey(u'utenti.id'), index=True)
    cancellato = Column(Integer, server_default=text("'0'"))

    dipendente = relationship(u'Dipendenti')
    utente = relationship(u'Utenti')
    
    def __init__(self, dipendente_id, data_inizio, data_fine, reparto, note='', utente_id=1):
        self.dipendente_id=dipendente_id
        self.data_inizio=data_inizio
        self.data_fine=data_fine
        self.reparto=reparto
        self.note=note
        self.utente_id=utente_id


t_presenze_bkp = Table(
    'presenze_bkp', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'")),
    Column('dipendente_id', Integer, nullable=False),
    Column('data_inizio', DateTime, nullable=False),
    Column('data_fine', DateTime, nullable=False),
    Column('reparto', String(50), nullable=False),
    Column('note', String(200)),
    Column('cancellato', Integer, server_default=text("'0'"))
)


class RapportoLavoro(Base):
    __tablename__ = 'rapporto_lavoro'

    Id = Column(Integer, primary_key=True)
    dipendente_id = Column(ForeignKey(u'dipendenti.id'), nullable=False, index=True)
    data_inizio = Column(Date, nullable=False)
    data_fine = Column(Date, nullable=False, server_default=text("'9999-12-31'"))

    dipendente = relationship(u'Dipendenti')


class Reparti(Base):
    __tablename__ = 'reparti'

    id = Column(Integer, primary_key=True)
    nome = Column(String(45), nullable=False)
    note = Column(String(200))
    cancellato = Column(Integer, server_default=text("'0'"))


t_report_mensile = Table(
    'report_mensile', metadata,
    Column('dipendente_id', Integer, nullable=False),
    Column('giorno', DateTime, nullable=False),
    Column('tot_ore_lavorate', Time),
    Column('tot_ore_assenza', Time),
    Column('giorno_assenza', Integer),
    Column('cod_causale_assenza', String(20)),
    Column('causale_assenza', String(100)),
    Column('diff_oraria', Time)
)


class Tally(Base):
    __tablename__ = 'tally'

    n = Column(Integer, primary_key=True)


class Utenti(Base):
    __tablename__ = 'utenti'

    id = Column(Integer, primary_key=True)
    username = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    profilo = Column(Enum(u'A', u'U'), nullable=False, server_default=text("'U'"))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

class VoceBusta(Base):
    __tablename__ = 'voce_busta'

    id = Column(Integer, primary_key=True)
    busta_id = Column(ForeignKey(u'busta_paga.id', ondelete=u'CASCADE'), nullable=False, index=True)
    descrizione = Column(String(100), nullable=False)
    importo = Column(Numeric(7, 2), nullable=False)

    busta = relationship(u'BustaPaga')

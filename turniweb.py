from __future__ import print_function
import os, config, json, datetime, flask, sys, time
from datetime import timedelta, date
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, jsonify
from flask_babel import Babel, format_datetime, format_date
from flask_mail import Mail, Message
from dateutil.parser import parse
import jsonpickle
from models import db, Dipendenti, Presenze, Assenze, Reparti
from anytree import Node, RenderTree

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
app.static_folder = 'static' 
mail_ext = Mail(app)
db.init_app(app)
babel = Babel(app)

@app.route('/')
def index():
    g.user={'name':'pippo'}
    return render_template('index.html')

def crea_albero_presenze(dt1, dt2):
    delta = dt2 - dt1
    days = delta.days
    
    giorni = []
    
    presenze = (db.session.query(Presenze).
        outerjoin(Dipendenti, Presenze.dipendente).
        filter(Presenze.cancellato==0).
        filter(Presenze.data_inizio.between(dt1, dt2)).
        order_by(Dipendenti.cognome).
        order_by(Presenze.data_inizio)
    )
    
    dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
    root=Node("root")
    
    i=0
    dt=dt1
    for i in range(days):
        giorni.append(dt)
        dt = dt + datetime.timedelta(days=1)
    
    for d in dipendenti:
        node_dip=Node(d.nome_completo(), parent=root)
        dt=dt1
        i=0
        for i in range(days):
            presenze = (db.session.query(Presenze).
                filter(Presenze.cancellato==0).
                filter(Presenze.dipendente_id==d.id).
                filter(Presenze.data_inizio.between(dt, dt + datetime.timedelta(days=1))).
                order_by(Presenze.data_inizio)
            )
            list_presenze=[ObjPresenza(p.id, p.data_inizio, p.data_fine, p.reparto) for p in presenze]
            node_gg=Node("presenze", parent=node_dip, lines=[list_presenze])
            dt = dt + datetime.timedelta(days=1)
    
    for pre, fill, node in RenderTree(root):
        print("%s%s" % (pre, node.name), file=sys.stderr)
        
    return RenderTree(root), giorni, dipendenti

class ObjPresenza(object):
    def __init__(self, id, data_inizio, data_fine, reparto):
        self.id = id
        self.data_inizio = data_inizio
        self.data_fine = data_fine
        self.reparto = reparto
        
    def __repr__(self):
        return '%d %s %s %s' % (self.id, self.data_inizio, self.data_fine, self.reparto)

@app.route('/turni', methods=['GET', 'POST'])
def turni():
    g.user = {'name':'pippo'}
    dt1 = date.today()
    
    if(request.method=='POST'):
        dt1 = parse(request.form['data_inizio'])
    
    dt2 = dt1 + datetime.timedelta(days=7)
    
    tree, giorni, dipendenti = crea_albero_presenze(dt1, dt2)
    
    #matrice = MatricePresenze(presenze, parse(dt1), parse(dt2))
    return render_template('turni.html', dipendenti=dipendenti, tree=tree, data_inizio=dt1, data_fine=dt2, giorni=giorni)

@app.route('/nuovo_turno', methods=['GET', 'POST'])
def nuovo_turno():
    g.user={'name':'pippo'}
    dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
    reparti=db.session.query(Reparti).filter_by(cancellato=0).order_by('nome')
    
    if request.method == 'POST':
        f=request.form
        dip_id=int(f['dipendente'])
        dtin=f['dtin']
        tmin=f['tmin']
        dtfi=f['dtfi']
        tmfi=f['tmfi']
        dt_inizio = time.strptime(dtin + " " + tmin, "%Y-%m-%d %H:%M")
        dt_fine = time.strptime(dtfi + " " + tmfi, "%Y-%m-%d %H:%M")
        reparto=f['reparto']
        #return time.strftime("%d/%m/%Y %H:%M", dt_inizio)
        data_inizio=datetime.datetime(dt_inizio.tm_year, dt_inizio.tm_mon, dt_inizio.tm_mday, dt_inizio.tm_hour, dt_inizio.tm_min, 0)
        data_fine=datetime.datetime(dt_fine.tm_year, dt_fine.tm_mon, dt_fine.tm_mday, dt_fine.tm_hour, dt_fine.tm_min, 0)
        presenza=Presenze(dip_id, data_inizio, data_fine, reparto)
        db.session.add(presenza)
        db.session.commit()
        flash('Turno inserito', category='success')
    return render_template('nuovo_turno.html', dipendenti=dipendenti, reparti=reparti)

@app.route('/logout')
def logout():
    g.user={'name':'pippo'}
    return render_template('index.html')

@app.route('/login')
def login():
    return "LOGIN"
    
# jinja2 filters
@app.template_filter('dt')
def _jinja2_filter_date(date, fmt=None):
    if fmt:
        return date.strftime(fmt)  #format_date(date, fmt)
    else:
        return format_date(date, 'medium')

if __name__ == "__main__":
    app.run(host='192.168.56.101', port=5000)

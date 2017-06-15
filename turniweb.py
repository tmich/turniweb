from __future__ import print_function
import os, config, json, datetime, flask, sys, time
from datetime import timedelta
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, jsonify
from flask_babel import Babel, format_datetime, format_date
from flask_mail import Mail, Message
from dateutil.parser import parse
import jsonpickle
from models import db, Dipendenti, Presenze, Assenze, Reparti

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

def crea_matrice_orari(dt1, count):
    matr=dict()
    dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
    gg=dt1
    for dip in dipendenti:
      matr[dip.nome_completo()] = []
      print(dip.nome_completo(), file=sys.stderr)
      for i in range(count):
	#presenze=db.session.query(Presenze).filter(Presenze.cancellato==0).filter(Presenze.dipendente_id == dip.id)
	print(datetime.date(gg.year, gg.month, gg.day), file=sys.stderr)
	day = int(gg.day)
	presenze=db.session.query(Presenze).filter(
	    Presenze.cancellato==0,
	    Presenze.dipendente_id == dip.id,
	    db.func.year(Presenze.data_inizio) == gg.year,
	    db.func.month(Presenze.data_inizio) == gg.month)
	lista_presenze=matr[dip.nome_completo()]
	print(presenze.count(), file=sys.stderr)
	for p in presenze:
	  lista_presenze.append(p)
	  #print(db.func.extract(Presenze.data_inizio, 'day').scalar(), file=sys.stderr)
	  #print(datetime.date(gg.year, gg.month, gg.day), file=sys.stderr)
	matr[dip.nome_completo()] = lista_presenze
	gg = gg + datetime.timedelta(days=1)
	
      gg=dt1
	
    return matr

@app.route('/turni')
def turni():
    g.user={'name':'pippo'}
    data_in= datetime.datetime(2016, 5, 4)  #datetime.date.today()
    data_fi=data_in + timedelta(days=7)
    matrice=crea_matrice_orari(data_in, 7)
    return render_template('turni.html', matrice=matrice, data_inizio=data_in, data_fine=data_fi)

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
    #app.run(host='192.168.56.101', port=5000)
    app.run()

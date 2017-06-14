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

@app.route('/turni')
def turni():
    matrice=dict()
    g.user={'name':'pippo'}
    sess=db.session()
    data_in= datetime.datetime(2016, 5, 1)  #datetime.date.today()
    data_fi=data_in + datetime.timedelta(days=7)
    # dipendenti=sess.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
    # for d in dipendenti:
        # matrice['dipendente'] = d
        # gg=data_in
        # while gg <= data_fi:
            # matrice['gg']=gg
            # turni=[]
            # matrice['turni']=turni
            # for t in d.presenze.filter_by(data_inizio.date == gg):
                # turni.append(t)
            # matrice['turni'].append(turni)
            # gg = gg + datetime.timedelta(days=1)
            
    presenze=sess.query(Presenze).filter(Presenze.cancellato==0).filter(Presenze.data_inizio >= data_in).filter(Presenze.data_fine <= data_fi)
    return render_template('turni.html', presenze=presenze, data_inizio=data_in, data_fine=data_fi)

@app.route('/nuovo_turno', methods=['GET', 'POST'])
def nuovo_turno():
    g.user={'name':'pippo'}
    if request.method == 'GET':
        dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
        reparti=db.session.query(Reparti).filter_by(cancellato=0).order_by('nome')
        return render_template('nuovo_turno.html', dipendenti=dipendenti, reparti=reparti)
    elif request.method == 'POST':
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
        
        presenza=Presenze(dip_id, dt_inizio, dt_fine, reparto)
        db.session.add(presenza)
        db.session.commit()
        return str(presenza.id)

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

from __future__ import print_function
import os, config, json, datetime, flask, sys, time
from datetime import timedelta, date, tzinfo
from time import strftime
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, jsonify, json
from flask_babel import Babel, format_datetime, format_date
from flask_mail import Mail, Message
from dateutil.parser import parse
import jsonpickle
from models import db, Dipendenti, Presenze, Assenze, Reparti, MotivoAssenza, Utenti
from anytree import Node, RenderTree
from pdfs import create_pdf
from flask_login import LoginManager, login_user, current_user, logout_user, login_required

login_manager = LoginManager()

def create_app():
	app = Flask(__name__)
	app.config.from_object('config.DevelopmentConfig')
	app.static_folder = 'static' 
	#mail_ext = Mail(app)
	#db = SQLAlchemy(app)
	db.init_app(app)
	babel = Babel(app)
	login_manager.init_app(app)
	#with app.app_context():
		#Extensions like Flask-SQLAlchemy now know what the "current" app
		#is while within this block. Therefore, you can now run........
		#db.create___all()

	return app
	
app = create_app()
mail_ext = Mail(app)

class ObjPresenza(object):
	def __init__(self, id, data_inizio, data_fine, reparto, id_utente=0):
		self.id = id
		self.data_inizio = data_inizio
		self.data_fine = data_fine
		self.reparto = reparto
		self.id_utente = id_utente
		
	def __repr__(self):
		return '%d %s %s %s' % (self.id, self.data_inizio, self.data_fine, self.reparto)
	  
class ObjAssenza(object):
	def __init__(self, id, data_inizio, data_fine, motivo, giornata_intera=False, id_utente=0):
		self.id = id
		self.data_inizio = data_inizio
		self.data_fine = data_fine
		self.motivo = motivo
		self.giornata_intera = giornata_intera
		self.id_utente=id_utente
		
	def __repr__(self):
		return '%d %s %s %s' % (self.id, self.data_inizio, self.data_fine, self.motivo)
	
@login_manager.user_loader
def load_user(user_id):
	return db.session.query(Utenti).get(user_id)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	# Here we use a class of some kind to represent and validate our
	# client-side form data. For example, WTForms is a library that will
	# handle this for us, and we use a custom LoginForm to validate.
	if(request.method == 'POST'):
		form = request.form
		usrn = form.get('username', 'nessuno')
		pswd = form.get('password', '')
		
		user = db.session.query(Utenti).filter_by(username=usrn).filter_by(password=pswd).first()
		if user != None:
			# Login and validate the user.
			# user should be an instance of your `User` class
			if login_user(user):
				flash('Accesso effettuato come %s' % (current_user.username), 'success')

				next = request.args.get('next')
				# is_safe_url should check if the url is safe for redirects.
				# See http://flask.pocoo.org/snippets/62/ for an example.
				# if not is_safe_url(next):
					# return flask.abort(400)

				return redirect(next or url_for('turni'))
	
		flash('Accesso non riuscito', 'danger')
	return render_template('login.html')

@app.route('/api/v1/assenze', methods=['GET'])
def api_assenze():
	lista=[]
	assenze=db.session.query(Assenze).all()
	for a in assenze:
		d = {'id':a.id, 
			'resource_id':a.dipendente_id,
			'start':a.data_inizio.strftime("%Y-%m-%dT%H:%M:%S"), 
			'end':a.data_fine.strftime("%Y-%m-%dT%H:%M:%S"), 
			'title':a.motivo.descrizione, 
			'allDay':a.giornata_intera, 
			'utente_id':a.utente_id
			}
		lista.append(d)
	
	resp = jsonify(lista)
	resp.status_code = 200
	
	return resp
	
@app.route('/api/v1/events', methods=['GET'])
def api_events():
	start=request.args.get('start', '')
	end=request.args.get('end', '')

	lista=[]
	
	assenze=db.session.query(Assenze).filter(Assenze.data_inizio >= datetime.datetime.strptime(start, '%Y-%m-%d')).order_by(Assenze.data_inizio)
	for a in assenze:
		d = {'id':str(a.id),
			'resourceId':a.dipendente_id,
			'start':a.data_inizio.strftime("%Y-%m-%dT%H:%M:%S"), 
			'end':a.data_fine.strftime("%Y-%m-%dT%H:%M:%S"), 
			'title':'%s %s-%s' % (a.motivo.descrizione, a.data_inizio.strftime("%H:%M"), a.data_fine.strftime("%H:%M")),
			'allDay': 1 if a.giornata_intera else 0, 
			'desc' : a.motivo.descrizione,
			#'utente_id':a.utente_id,
			'color':'red',
			'type':'A'
		}
		lista.append(d)
	
	presenze=db.session.query(Presenze).filter(Presenze.data_inizio >= datetime.datetime.strptime(start, '%Y-%m-%d')).order_by(Presenze.data_inizio)
	for p in presenze:
		x = {
			'id':p.id, 
			'resourceId':str(p.dipendente_id),
			'start':p.data_inizio.strftime("%Y-%m-%dT%H:%M:%S"), 
			'end':p.data_fine.strftime("%Y-%m-%dT%H:%M:%S"), 
			'title': '%s %s-%s' % (p.reparto, p.data_inizio.strftime("%H:%M"), p.data_fine.strftime("%H:%M")),
			'allDay':0,
			'desc' : p.reparto,
			'type':'P'
			#'utente_id':a.utente_id
		}
		lista.append(x)
	
	resp = jsonify(lista)
	resp.status_code = 200
	
	return resp

@app.route('/api/v1/upd_presenza', methods=['POST'])
def api_update_presenza():
	form=request.form
	id=form.get('id', 0)
	inizio=form.get('inizio', 0)
	fine=form.get('fine', 0)
	
	if(id > 0):
		try:
			p = db.session.query(Presenze).get(id)
			p.data_inizio = inizio
			p.data_fine = fine
			db.session.commit()
			print('OK: %s' % (p.id,), file=sys.stderr)
			resp = jsonify({'risposta' : 'OK'})
			resp.status_code = 200
			return resp
		except:		
			pass
	
	resp = jsonify({'risposta' : 'KO'})
	resp.status_code = 500
	return resp

@app.route('/api/v1/upd_assenza', methods=['POST'])
def api_update_assenza():
	form=request.form
	id=form.get('id', 0)
	inizio=form.get('inizio', 0)
	fine=form.get('fine', 0)
	motivo=form.get('motivo', 0)
	giornataIntera=form.get('giornataIntera', 'null')
	
	print('%s\n%s\n%s\n%s\n%s\n' % (id,inizio,fine,motivo,giornataIntera,), file=sys.stderr)
	#return 'ok'
	
	if(id > 0):
		try:
			a=db.session.query(Assenze).get(id)
			a.data_inizio=inizio
			a.data_fine=fine
			if(motivo > 0):
				a.motivo_id=motivo
			if(giornataIntera!='null'):
				a.giornata_intera=giornataIntera
			db.session.commit()
			print('OK: %s' % (a.id,), file=sys.stderr)
			resp = jsonify({'id':a.id})
			resp.status_code = 200
			return resp
		except:		
			pass
	
	resp = jsonify({'risposta' : 'KO'})
	resp.status_code = 500
	return resp

@app.route('/api/v1/new_presenza', methods=['POST'])
def api_create_presenza():
	form=request.form
	dip_id=form.get('resourceId', 0)
	inizio=form.get('inizio', 0)
	fine=form.get('fine', 0)
	reparto=form.get('reparto', 0)
	
	print('dip_id: %s\ninizio: %s\nfine: %s\nreparto: %s\n' % (dip_id,inizio,fine,reparto,), file=sys.stderr)
	#return 'OK'
	
	if(dip_id > 0):
		try:
			p = Presenze(dip_id, inizio, fine, reparto)
			db.session.add(p)
			db.session.commit()
			print('OK: %s' % (p.id,), file=sys.stderr)
			resp = jsonify({'id':p.id})
			resp.status_code = 200
			return resp
		except:		
			pass
	
	resp = jsonify({'risposta' : 'KO'})
	resp.status_code = 500
	return resp
	
@app.route('/api/v1/new_assenza', methods=['POST'])
def api_create_assenza():
	form=request.form
	dip_id=form.get('resourceId', 0)
	inizio=form.get('inizio', 0)
	fine=form.get('fine', 0)
	motivo=form.get('motivo', 0)
	giornataIntera=form.get('giornataIntera', 0)
	
	print('dip_id: %s\ninizio: %s\nfine: %s\nmotivo: %s\ngiornataIntera: %s' % (dip_id,inizio,fine,motivo,giornataIntera,), file=sys.stderr)
	#return 'OK'
	
	if(dip_id > 0):
		try:
			a=Assenze(dipendente_id=dip_id, data_inizio=inizio, data_fine=fine, giornata_intera=(giornataIntera==1), motivo_id=motivo)
			db.session.add(a)
			db.session.commit()
			print('OK: %s' % (a.id,), file=sys.stderr)
			resp = jsonify({'id':a.id})
			resp.status_code = 200
			return resp
		except:		
			pass
	
	resp = jsonify({'risposta' : 'KO'})
	resp.status_code = 500
	return resp
	
@app.route('/api/v1/dipendenti', methods=['GET'])
def api_dipendenti():
	lista=[]
	dipendenti=db.session.query(Dipendenti).filter(Dipendenti.cancellato==0).order_by(Dipendenti.cognome)
	for d in dipendenti:
		el = {'id':d.id, 
			  'title':d.nome_completo()
			  }
		lista.append(el)
	
	resp = jsonify(lista)
	resp.status_code = 200
	
	return resp
	
def crea_albero_presenze(dt1, dt2):
	delta = dt2 - dt1
	days = delta.days
	
	giorni = []
	
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

			assenze = (db.session.query(Assenze).
				filter(Assenze.cancellato == 0).
				filter(Assenze.dipendente_id == d.id).
				filter(Assenze.data_inizio >= dt).
				filter(Assenze.data_inizio < dt + datetime.timedelta(days=1)).
				order_by(Assenze.data_inizio)
			)
			#filter(Assenze.data_inizio.between(dt, dt + datetime.timedelta(days=1))).
			list_presenze=[ObjPresenza(p.id, p.data_inizio, p.data_fine, p.reparto) for p in presenze]
			list_assenze=[ObjAssenza(a.id, a.data_inizio, a.data_fine, a.motivo.descrizione, a.giornata_intera, a.utente_id) for a in assenze]
			#print('Totale assenze: %s' % (len(list_assenze), ), file=sys.stderr)
			puoi_aggiungere=True
			for ass in list_assenze:    
				#print(ass.id, file=sys.stderr)
				puoi_aggiungere=not ass.giornata_intera
				
			node_gg=Node("giornata", parent=node_dip, presenze=[list_presenze], assenze=[list_assenze], data=dt, dip_id=d.id, puoi_aggiungere=puoi_aggiungere)
			dt = dt + datetime.timedelta(days=1)
	
	#for pre, fill, node in RenderTree(root):
	#    print("%s%s" % (pre, node.name), file=sys.stderr)
		
	return RenderTree(root), giorni, dipendenti

@app.route('/turni', methods=['GET', 'POST'])
@login_required
def turni():
	dt1 = date.today()
	
	if(request.method=='POST'):
		dt1 = parse(request.form['data_inizio'])
	
	dt2 = dt1 + datetime.timedelta(days=7)
	
	tree, giorni, dipendenti = crea_albero_presenze(dt1, dt2)
	
	return render_template('turni.html', dipendenti=dipendenti, tree=tree, data_inizio=dt1, data_fine=dt2, giorni=giorni)

@app.route('/stampa_turni/<string:dt1>/<string:dt2>', methods=['GET'])
@login_required
def stampa_turni(dt1, dt2):
	tree, giorni, dipendenti = crea_albero_presenze(parse(dt1), parse(dt2))
	#return render_template('turni_pdf.html', dipendenti=dipendenti, tree=tree, data_inizio=dt1, data_fine=dt2, giorni=giorni)
	#print(tree, file=sys.stderr)
	#print(sstr, file=sys.stderr)
	pdf=create_pdf(render_template('turni_pdf.html', dipendenti=dipendenti, tree=tree, data_inizio=dt1, data_fine=dt2, giorni=giorni))
	#print(pdf.getvalue(), file=sys.stderr)
	response=make_response(pdf.getvalue())
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=turni.pdf'
	return response

@app.route('/nuovo_turno/<int:id_dipendente>/<string:data>', methods=['GET', 'POST'])
@app.route('/nuovo_turno', methods=['GET', 'POST'])
@login_required
def nuovo_turno(id_dipendente=0,data=date.today()):
	dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
	reparti=db.session.query(Reparti).filter_by(cancellato=0).order_by('nome')
	dipendente=db.session.query(Dipendenti).get(id_dipendente)
	reparto=db.session.query(Reparti).get(dipendente.id_reparto)
	
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
		presenza=Presenze(dipendente_id=dip_id, data_inizio=data_inizio, data_fine=data_fine, reparto=reparto, utente_id=int(current_user.get_id()))
		db.session.add(presenza)
		db.session.commit()
		flash('Turno inserito', category='success')
		return redirect(url_for('turni'))
	return render_template('nuovo_turno.html', dipendenti=dipendenti, reparti=reparti, id_dipendente=id_dipendente, data=data, reparto=reparto.nome)

@app.route('/modifica_turno/<int:id_presenza>', methods=['GET', 'POST'])
@login_required
def modifica_turno(id_presenza):
	dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
	reparti=db.session.query(Reparti).filter_by(cancellato=0).order_by('nome')
	presenza=db.session.query(Presenze).get(id_presenza)
	
	if request.method == 'POST':
		f=request.form
		id_pres=int(f['id_presenza'])
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
		
		presenza.data_inizio=data_inizio
		presenza.data_fine=data_fine
		presenza.reparto=reparto
		presenza.utente_id=int(current_user.get_id())
		db.session.commit()
		
		flash('Turno aggiornato', category='success')
		return redirect(url_for('turni'))
	return render_template('modifica_turno.html', dipendenti=dipendenti, reparti=reparti, id_dipendente=presenza.dipendente_id, data_inizio=date.strftime(presenza.data_inizio, '%Y-%m-%d'), data_fine=date.strftime(presenza.data_fine, '%Y-%m-%d'), ora_inizio=date.strftime(presenza.data_inizio, '%H:%M'), ora_fine=date.strftime(presenza.data_fine, '%H:%M'), reparto=presenza.reparto, id_presenza=presenza.id)

@app.route('/nuova_assenza/<int:id_dipendente>/<string:data>', methods=['GET', 'POST'])
@login_required
def nuova_assenza(id_dipendente, data):
	dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
	motivi=db.session.query(MotivoAssenza).filter_by(codice='GEN')
	dipendente=db.session.query(Dipendenti).get(id_dipendente)
	
	if request.method == 'POST':
		f=request.form
		
		dip_id=int(f['dipendente'])
		dtin=f['dtin']
		tmin=f['tmin']
		dtfi=f['dtfi']
		tmfi=f['tmfi']
		dt_inizio = time.strptime(dtin + " " + tmin, "%Y-%m-%d %H:%M")
		dt_fine = time.strptime(dtfi + " " + tmfi, "%Y-%m-%d %H:%M")
		motivo_id=int(f['motivo'])
		intera=str(f.get('intera'))
		
		giornata_intera=True if intera == 'on' else False
		
		data_inizio=datetime.datetime(dt_inizio.tm_year, dt_inizio.tm_mon, dt_inizio.tm_mday, dt_inizio.tm_hour, dt_inizio.tm_min, 0)
		data_fine=datetime.datetime(dt_fine.tm_year, dt_fine.tm_mon, dt_fine.tm_mday, dt_fine.tm_hour, dt_fine.tm_min, 0)
		assenza=Assenze(dipendente_id=dip_id, data_inizio=data_inizio, data_fine=data_fine, giornata_intera=giornata_intera, motivo_id=motivo_id, utente_id=int(current_user.get_id()))
		db.session.add(assenza)
		db.session.commit()
		flash('Assenza inserita', category='success')
		return redirect(url_for('turni'))
	
	return render_template('nuova_assenza.html', dipendenti=dipendenti, motivi=motivi, id_dipendente=id_dipendente, data=data)

@app.route('/modifica_assenza/<int:id_assenza>', methods=['GET', 'POST'])
@login_required
def modifica_assenza(id_assenza):
	dipendenti=db.session.query(Dipendenti).filter_by(cancellato=0).order_by('cognome')
	motivi=db.session.query(MotivoAssenza).filter_by(codice='GEN')
	assenza=db.session.query(Assenze).get(id_assenza)
	
	if request.method == 'POST':
		f=request.form
		dip_id=int(f['dipendente'])
		dtin=f['dtin']
		tmin=f['tmin']
		dtfi=f['dtfi']
		tmfi=f['tmfi']
		dt_inizio = time.strptime(dtin + " " + tmin, "%Y-%m-%d %H:%M")
		dt_fine = time.strptime(dtfi + " " + tmfi, "%Y-%m-%d %H:%M")
		motivo_id=int(f['motivo'])
		intera=str(f.get('intera'))
		
		giornata_intera=True if intera == 'on' else False
		
		data_inizio=datetime.datetime(dt_inizio.tm_year, dt_inizio.tm_mon, dt_inizio.tm_mday, dt_inizio.tm_hour, dt_inizio.tm_min, 0)
		data_fine=datetime.datetime(dt_fine.tm_year, dt_fine.tm_mon, dt_fine.tm_mday, dt_fine.tm_hour, dt_fine.tm_min, 0)
		
		assenza.data_inizio=data_inizio
		assenza.data_fine=data_fine
		assenza.motivo_id=motivo_id
		assenza.giornata_intera=giornata_intera
		assenza.utente_id=int(current_user.get_id())
		db.session.commit()
		
		flash('Assenza aggiornata', category='success')
		return redirect(url_for('turni'))
		
	return render_template('modifica_assenza.html', dipendenti=dipendenti, motivi=motivi, id_dipendente=assenza.dipendente_id, data_inizio=date.strftime(assenza.data_inizio, '%Y-%m-%d'), data_fine=date.strftime(assenza.data_fine, '%Y-%m-%d'), ora_inizio=date.strftime(assenza.data_inizio, '%H:%M'), ora_fine=date.strftime(assenza.data_fine, '%H:%M'), motivo_id=assenza.motivo_id, id_assenza=assenza.id, giornata_intera=assenza.giornata_intera)

@app.route('/calendar')
@login_required
def calendar():
	motivi=db.session.query(MotivoAssenza)
	reparti=db.session.query(Reparti).filter_by(cancellato=0).order_by('nome')
	return render_template('calendar.html', motivi=motivi, reparti=reparti)
	
@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))
	
# jinja2 filters
@app.template_filter('dt')
def _jinja2_filter_date(date, fmt=None):
	if fmt:
		return date.strftime(fmt)  #format_date(date, fmt)
	else:
		return format_date(date, 'medium')

if __name__ == "__main__":
	app.run(host='80.211.227.37', port=5000)
	#app.run()

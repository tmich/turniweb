#config.py

class Config(object):
  DEBUG = False
  SECRET_KEY = '8#]u:eYd~u,fT$nM-TyQ,yZu~eXDd)qhpVu7g`dP%6;[5tf'
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  MAIL_SERVER = 'smtp.gmail.com'
  MAIL_PORT=587
  MAIL_USE_SSL=False
  MAIL_USE_TLS=True
  MAIL_DEFAULT_SENDER=('Tiziano Michelessi', 'tiziano.michelessi@gmail.com')
  MAIL_USERNAME = 'tiziano.michelessi'
  MAIL_PASSWORD = 'T1z1@n0!'
  BABEL_DEFAULT_LOCALE = 'it'
  
class ProductionConfig(Config):
  pass

class DevelopmentConfig(Config):
  DEBUG = True
  SQLALCHEMY_DATABASE_URI = 'mysql://scott:tiger@localhost/turni'
  #MYSQL_USER = 'scott'
  #MYSQL_PASSWORD = 'tiger'
  #MYSQL_DB = 'turni'
  #MYSQL_HOST = 'localhost'


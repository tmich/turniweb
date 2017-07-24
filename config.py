#config.py

class Config(object):
  DEBUG = False
  SECRET_KEY = '8#]u:eYd~u,fT$nM-TyQ,yZu~eXDd)qhpVu7g`dP%6;[5tf'
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  BABEL_DEFAULT_LOCALE = 'it'
  
class ProductionConfig(Config):
  pass

class DevelopmentConfig(Config):
  DEBUG = True
  SQLALCHEMY_DATABASE_URI = 'mysql://scott:tiger1@localhost/turni'
  #MYSQL_USER = 'scott'
  #MYSQL_PASSWORD = 'tiger'
  #MYSQL_DB = 'turni'
  #MYSQL_HOST = 'localhost'


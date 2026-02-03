from sqlalchemy import create_engine, MetaData, String, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import configure_mappers
from sqlalchemy.orm import scoped_session
from sqlalchemy import event
from sqlalchemy import exc
import traceback
from pathlib import Path
import logging
from logging.config import dictConfig
import os
from sqlalchemy.engine import reflection
import pymysql
from contextlib import contextmanager
import json

class MysqlConnection(object):

    def __init__(self, **kwargs):

        if kwargs.get('mysql_connection'):
            DB_USER =  kwargs['mysql_connection']['login']
            DB_PASS = kwargs['mysql_connection']['password']
            DB_HOST = kwargs['mysql_connection']['host']
            DB_PORT = kwargs['mysql_connection']['port']
            DB_SCHEMA = kwargs['mysql_connection'].get('schema')

        elif os.getenv('mysql_connection'):
            mysql_config = json.loads(os.getenv('mysql_connection'))
            DB_USER =  mysql_config['login']
            DB_PASS = mysql_config['password']
            DB_HOST = mysql_config['host']
            DB_PORT = mysql_config['port']
            DB_SCHEMA = mysql_config.get('schema')

        else:
            DB_USER = 'root'
            DB_PASS = 'password'
            DB_HOST = 'localhost'
            DB_PORT = 3306
            DB_SCHEMA = None

        connect_string = 'mysql+pymysql://{}:{}@{}:{}'.format(DB_USER, DB_PASS, DB_HOST, DB_PORT)
        #print(connect_string)
        if DB_SCHEMA:
            connect_string += f'/{DB_SCHEMA}'

        self.engine = create_engine(connect_string)#, max_overflow=-1, pool_recycle=-1)
        #self.engine.execute('set max_allowed_packet=67108864')
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.cursor = self.engine.raw_connection().cursor(pymysql.cursors.DictCursor)

        insp = inspect(self.engine)

        DATABASES = ['webservice_fromtis', 'operacao']
        #DATABASES = insp.get_schema_names()
        # jmysql_dbs = ['information_schema', 'mysql', 'performance_schema']

        #for db in mysql_dbs:
        #    DATABASES.remove(db)

        self.Base = automap_base()
        for db in DATABASES:
            try:
                self.Base.metadata.reflect(self.engine, schema=db)
            except Exception:
                print(traceback.format_exc())

        self.Base.prepare()
        self.DictTables = {}
        for schema in DATABASES:
            for table_name in insp.get_table_names(schema=schema):
                try:
                    self.DictTables[f'{schema}.{table_name}'] = getattr(self.Base.classes, table_name)
                except Exception:
                    print('The following table was not added to the dictionary:')
                    print(traceback.format_exc())

        self.session = self.Session()


    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def context_session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


if __name__=='__main__':
    db = MysqlConnection()





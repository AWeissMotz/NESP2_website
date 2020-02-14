import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import func
import geoalchemy2
from sqlalchemy import Table, MetaData
from sqlalchemy.ext.declarative import declarative_base


def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)


POSTGRES_URL = get_env_variable("POSTGRES_URL")
POSTGRES_USER = get_env_variable("POSTGRES_USER")
POSTGRES_PW = get_env_variable("POSTGRES_PW")
POSTGRES_DB = get_env_variable("POSTGRES_DB")


DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(
    user=POSTGRES_USER,
    pw=POSTGRES_PW,
    url=POSTGRES_URL,
    db=POSTGRES_DB
)


PROGRESS_NUMBER_MAX = {
    'max_km_electricity': 'km electricity grid tracked',
    'max_villages': 'villages remotely mapped',
    'max_buildings': 'buildings mapped'
}
engine = create_engine(DB_URL)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))


Base = declarative_base(metadata=MetaData(schema='se4all', bind=engine))
BaseWeb = declarative_base(metadata=MetaData(schema='web', bind=engine))


class DlinesSe4all(Base):
    __table__ = Table('distribution_line_se4all', Base.metadata, autoload=True, autoload_with=engine)


class GaugeMaximum(BaseWeb):
    __table__ = Table('ourprogress_maximums', BaseWeb.metadata, autoload=True, autoload_with=engine)


class MappedVillages(BaseWeb):
    __table__ = Table('ourprogress_villagesremotelymapped', BaseWeb.metadata, autoload=True,
                      autoload_with=engine)


class MappedBuildings(BaseWeb):
    __table__ = Table('ourprogress_buildingsmapped', BaseWeb.metadata, autoload=True,
                      autoload_with=engine)


def select_materialized_view(engine, view_name, schema=None, limit=None):
    if schema is not None:
        view_name = "{}.{}".format(schema, view_name)
    if limit is None:
        limit = ""
    else:
        limit = " LIMIT {}".format(limit)
    with engine.connect() as con:
        rs = con.execute('SELECT * FROM {}{};'.format(view_name, limit))
        data = rs.fetchall()
    return data


def query_electrified_km():
    res = select_materialized_view(engine, "ourprogress_kmelectricitygridtracked_value_v", schema="web")[0][0]
    return int(res)


def query_mapped_villages():
    res = select_materialized_view(engine, "ourprogress_villagesremotelymapped_value_v", schema="web")[0][0]
    return int(res)


def query_mapped_buildings():
    res = select_materialized_view(engine, "ourprogress_buildingsmapped_value_v", schema="web")[0][0]
    return int(res)


def query_gauge_maximum(desc):
    """Query the maximum value for a given progress gauge

    :param desc: the name of the variable under "Our progress in numbers" on the website
    :return: the maximum value as string
    """
    res = db_session.query(GaugeMaximum.maximum.label("max"))\
        .filter(GaugeMaximum.description.ilike("%{}%".format(desc))).first()
    return str(int(res.max))

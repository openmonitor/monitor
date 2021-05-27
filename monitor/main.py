import argparse
import logging
import requests
import time
import typing
import urllib3

import config.factory as cfg_fac
import scheduler.scheduler as scheduler
import observer.observer as observer

try:
    import common.database.factory as db_fac
    import common.database.operations
    import common.model as model
    import common.util as commonutil
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')


logger = logging.getLogger(__name__)
commonutil.configure_default_logging(stdout_level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--monitor-config', action='store', dest='config_path', type=str)
parser.add_argument('--dev', action='store_true', dest='dev')
args = parser.parse_args()

if args.dev:
    commonutil.configure_default_logging(stdout_level=logging.DEBUG)

logger.info(f'starting in {"dev" if args.dev else "prod"} mode')

# make config
cfg_fac = cfg_fac.ConfigFactory()
cfg = cfg_fac.make_config(config_path=args.config_path)

# make connection
conn_fac = db_fac.DatabaseConnectionFactory()
conn = conn_fac.make_connection()

# db operations
db_ops = common.database.operations.DatabaseOperator(connection=conn)

# write config to database
db_ops.insert_config(cfg=cfg)

# init scheduler
scheduler = scheduler.Scheduler(
    cfg=cfg,
    conn=conn,
)

# init event loop
scheduler.schedule_events()

# make and register observer
obs = observer.Observer(
    name='schedule-observer',
    callback='http://127.0.0.1:1337',
)
scheduler.register_observer(observer=obs)

# start event loop
scheduler.start_event_loop()

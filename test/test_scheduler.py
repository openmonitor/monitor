import json
import pytest
import requests

try:
    import common.database.factory as db_fac
    import common.exceptions as exceptions
    import common.model as model
    import common.observer as observer
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')
import monitor.config.factory as fac
import monitor.scheduler.scheduler as sched


def test_scheduler_init():
    cfg_fac = fac.ConfigFactory()
    cfg = cfg_fac.make_config(config_path='./test/config_1.yaml')

    conn_fac = db_fac.DatabaseConnectionFactory()
    conn = conn_fac.make_connection()

    sched.Scheduler(
        cfg=cfg,
        conn=conn,
    )


def test_scheduler_observer():
    cfg_fac = fac.ConfigFactory()
    cfg = cfg_fac.make_config(config_path='./test/config_1.yaml')

    conn_fac = db_fac.DatabaseConnectionFactory()
    conn = conn_fac.make_connection()

    scheduler = sched.Scheduler(
        cfg=cfg,
        conn=conn,
    )

    scheduler.schedule_events()

    # make and register observer
    obs = observer.Observer(
        name='schedule-observer',
        callback='http://127.0.0.1:1337',
    )
    scheduler.register_observer(observer=obs)


def test_scheduler_metrics():
    cfg_fac = fac.ConfigFactory()
    cfg = cfg_fac.make_config(config_path='./test/config_1.yaml')

    conn_fac = db_fac.DatabaseConnectionFactory()
    conn = conn_fac.make_connection()

    scheduler = sched.Scheduler(
        cfg=cfg,
        conn=conn,
    )

    resp = requests.get(
        url='https://zeekay.dev/404',
    )

    with pytest.raises(json.decoder.JSONDecodeError):
        scheduler._parse_result(
            resp=resp,
            timeout=False,
            metric_id='bar',
            component_id='bar',
        )


def test_scheduler_observer_call():
    def _fake_callable():
        pass
    cfg_fac = fac.ConfigFactory()
    cfg = cfg_fac.make_config(config_path='./test/config_1.yaml')

    conn_fac = db_fac.DatabaseConnectionFactory()
    conn = conn_fac.make_connection()

    scheduler = sched.Scheduler(
        cfg=cfg,
        conn=conn,
    )

    obs = observer.Observer(
        name='schedule-observer-test',
        callback='404',
    )

    scheduler.register_observer(observer=obs)
    for obs in scheduler.observer:
        obs.call_by_callable(callable=_fake_callable)

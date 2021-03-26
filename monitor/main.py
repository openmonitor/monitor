import argparse
import logging
import requests
import schedule
import time
import typing
import urllib3

import config
import model

try:
    import database
    import util
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')


logger = logging.getLogger(__name__)
util.configure_default_logging(stdout_level=logging.INFO)


def _monitor_status_endpoint(
    component_config: model.ComponentConfig,
):
    endpoint_url = util.urljoin(
        component_config.baseUrl,
        component_config.statusEndpoint,
    )
    logger.info(f'monitoring {endpoint_url}')
    try:
        resp = requests.get(
            url=endpoint_url,
            timeout=util.strip_time_str_to_int(
                timeout_str=component_config.timeout,
                ms=True,
                s=True,
            ),
        )
        logger.debug(f'{resp.status_code} in {resp.elapsed.total_seconds()}')
        cf = _parse_response_to_component_frame(
            resp=resp,
            component_config=component_config,
            timeout=False,
        )
    except requests.exceptions.Timeout:
        logger.warning(f'{endpoint_url} request timed out after {component_config.timeout}')
        cf = _parse_response_to_component_frame(
            component_config=component_config,
        )
    except (urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError):
        logger.warning(f'{endpoint_url} request failed')
        cf = _parse_response_to_component_frame(
            component_config=component_config,
        )

    conn = database.get_connection()

    database.insert_component_frame(
        conn=conn,
        component_frame=cf,
    )

    database.delete_outdated_component_frames(
        cc=component_config,
        conn=conn,
    )

    database.kill_connection(
        conn=conn,
    )


def _parse_response_to_component_frame(
    component_config: model.ComponentConfig,
    timeout=True,
    resp=None,
) -> model.ComponentFrame:
    cf = model.ComponentFrame(
        component=component_config.id,
        frame=0,
        timestamp='now()',
        reachable=False if timeout else True,
        responseTime=0 if timeout else resp.elapsed.total_seconds() * 1000,
    )
    return cf


def _schedule_event_loops(
    monitor_config: typing.Tuple[
        typing.List[model.ComponentConfig],
        typing.List[model.SystemConfig]
    ],
):
    for c in monitor_config[0]:
        if c.frequency.__contains__('s'):
            schedule.every(int(c.frequency.replace('s', ''))).seconds.do(
                _monitor_status_endpoint,
                component_config=c,
            )
        elif c.frequency.__contains__('m'):
            schedule.every(int(c.frequency.replace('m', ''))).minutes.do(
                _monitor_status_endpoint,
                component_config=c,
            )
        elif c.frequency.__contains__('h'):
            schedule.every(int(c.frequency.replace('h', ''))).hours.do(
                _monitor_status_endpoint,
                component_config=c,
            )


def _write_config_to_db(
    cfg: typing.Tuple[
        typing.List[model.ComponentConfig],
        typing.List[model.SystemConfig]
    ]
):
    conn = database.get_connection()
    for sc in cfg[1]:
        sys = config.parse_system_config_to_system(
            system_config=sc,
        )
        if database.select_system(
            conn=conn,
            system=sys.system,
        ):
            # primary key (component) exists, so entry has to be updated
            database.update_system(
                conn=conn,
                system=sys,
            )
        else:
            database.insert_system(
                conn=conn,
                system=sys,
            )
    for cc in cfg[0]:
        com = config.parse_component_config_to_component(
            component_config=cc,
        )
        if database.select_component(
            conn=conn,
            component=com.component,
        ):
            # primary key (component) exists, so entry has to be updated
            database.update_component(
                conn=conn,
                component=com,
            )
        else:
            database.insert_component(
                conn=conn,
                component=com,
            )
    database.kill_connection(
        conn=conn,
    )


def _start_event_loops():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--monitor-config', action='store', dest='monitor_config', type=str)
    parser.add_argument('--dev', action='store_true', dest='dev')
    args = parser.parse_args()

    if args.dev:
        util.configure_default_logging(stdout_level=logging.DEBUG)
        logger.debug('starting in dev mode')
    else:
        logger.info('starting in prod mode')

    # parse config
    c: typing.Tuple[
        typing.List[model.ComponentConfig],
        typing.List[model.SystemConfig]
    ]
    c = config.parse_config_path(
        config_file=args.monitor_config,
    )

    _write_config_to_db(
        cfg=c,
    )

    # schedule and start actual payload (eventloops for monitoring)
    _schedule_event_loops(
        monitor_config=c,
    )
    _start_event_loops()

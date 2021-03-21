import argparse
import logging
import requests
import schedule
import time
import typing

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
    resp = requests.get(
        url=endpoint_url,
    )
    logger.debug(f'{resp.status_code} in {resp.elapsed.total_seconds()}')

    conn = database.get_connection()
    frame_id = database.select_next_frame_id(
        conn=conn,
        component=component_config.id,
    )
    cf = _parse_response_to_component_frame(
        resp=resp,
        component_config=component_config,
        frame_id=frame_id,
    )
    database.insert_component_frame(
        conn=conn,
        component_frame=cf,
    )
    database.kill_connection(
        conn=conn,
    )


def _parse_response_to_component_frame(
    resp,
    component_config: model.ComponentConfig,
    frame_id: int,
) -> model.ComponentFrame:
    cf = model.ComponentFrame(
        component=component_config.id,
        frame=frame_id,
        timestamp='now()',
        reachable=True if resp.status_code == 200 else False,
        responseTime=resp.elapsed.total_seconds(),
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


def _start_event_loops():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--monitor-config', action='store', dest='monitor_config', type=str)
    args = parser.parse_args()

    # parse config
    c: typing.Tuple[
        typing.List[model.ComponentConfig],
        typing.List[model.SystemConfig]
    ]
    c = config.parse_config_path(
        config_file=args.monitor_config,
    )
    _schedule_event_loops(
        monitor_config=c,
    )
    _start_event_loops()

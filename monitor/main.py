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
    endpoint_url: str,
):
    logger.info(f'monitoring {endpoint_url}')
    resp = requests.get(
        url=endpoint_url,
    )
    resp_time = resp.elapsed.total_seconds()
    logger.debug(f'{resp.status_code} in {resp_time}')


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
                endpoint_url=util.urljoin(
                    c.baseUrl,
                    c.statusEndpoint,
                )
            )
        elif c.frequency.__contains__('m'):
            schedule.every(int(c.frequency.replace('m', ''))).minutes.do(
                _monitor_status_endpoint,
                endpoint_url=util.urljoin(
                    c.baseUrl,
                    c.statusEndpoint,
                )
            )
        elif c.frequency.__contains__('h'):
            schedule.every(int(c.frequency.replace('h', ''))).hours.do(
                _monitor_status_endpoint,
                endpoint_url=util.urljoin(
                    c.baseUrl,
                    c.statusEndpoint,
                )
            )


def _start_event_loops():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    # parse config
    c: typing.Tuple[
        typing.List[model.ComponentConfig],
        typing.List[model.SystemConfig]
    ]
    c = config.parse_config_path(
        config_file='./../monitor-config.yml',
    )
    _schedule_event_loops(
        monitor_config=c,
    )
    _start_event_loops()

import logging
import time
import typing

import requests
import urllib3
import schedule

import observer.observer as observer
try:
    import common.database.connection
    import common.database.operations
    import common.exceptions as exceptions
    import common.model as model
    import common.util as commonutil
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')


class Scheduler:
    def __init__(
        self,
        cfg: model.Config,
        conn: common.database.connection.DatabaseConnection,
    ):
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.config: model.Config = cfg
        self.db_ops: common.database.operations.DatabaseOperations = common.database.operations.DatabaseOperations(connection=conn)
        self.observer: typing.List[observer.Observer] = []
        return

    def schedule_events(self):
        for c in self.config.components:
            for m in c.metrics:
                if m.frequency.unit == model.TimeUnit.SECOND:
                    schedule.every(int(m.frequency.value)).seconds.do(
                        self.monitor_metric,
                        metric=m,
                        component_id=c.id,
                    )
                elif m.frequency.unit == model.TimeUnit.MINUTE:
                    schedule.every(int(m.frequency.value)).minutes.do(
                        self.monitor_metric,
                        metric=m,
                        component_id=c.id,
                    )
                elif m.frequency.unit == model.TimeUnit.HOUR:
                    schedule.every(int(m.frequency.value)).hours.do(
                        self.monitor_metric,
                        metric=m,
                        component_id=c.id,
                    )
                else:
                    raise exceptions.OpenmonitorNotSupported(
                        f'frequency "{m.frequency}" is not supported, only seconds, minutes or hours.'
                    )

    def _parse_result(
        self,
        resp,
        timeout: bool,
        metric_id: str,
        component_id: str,
    ) -> model.Result:
        data = resp.json()

        res: model.Result = model.Result(
            metricId=metric_id,
            componentId=component_id,
            timestamp='now()',
            value=data.get('data') if not timeout else None,
            timeout=False,
            responseTime=0 if timeout else resp.elapsed.total_seconds() * 1000,
        )
        return res

    def start_event_loop(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def register_observer(
        self,
        observer,
    ):
        self.observer.append(observer)
        self.logger.info(f'registered observer {observer.name}')

    def monitor_metric(
        self,
        metric: model.Metric,
        component_id: str,
    ):
        endpoint_url = commonutil.urljoin(
            metric.baseUrl,
            metric.endpoint,
        )
        self.logger.info(f'monitoring {endpoint_url}')
        res: model.Result
        timeout: bool = False

        try:
            resp = requests.get(
                url=endpoint_url,
                timeout=metric.timeout.as_ms(),
            )
            resp_time_sec = resp.elapsed.total_seconds()
            if resp.status_code == 200:
                self.logger.debug(f'{resp.status_code} in {resp_time_sec}')
            else:
                self.logger.warn(f'{endpoint_url}: returned not 200, {resp.status_code=}, still inserting result')

        except (urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.Timeout):
            self.logger.warning(f'{endpoint_url} request failed or timed out')
            timeout=True

        res = self._parse_result(
            resp=resp,
            timeout=timeout,
            metric_id=metric.id,
            component_id=component_id,
        )
        self.db_ops.insert_result(res=res)

        self.db_ops.delete_outdated_results(
            component_id=component_id,
            metric_id=metric.id,
            delete_after=metric.deleteAfter,
        )

        for obs in self.observer:
            self.logger.info(f'calling observer {obs.name}')
            obs.call_by_post()

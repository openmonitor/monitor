import logging
import os
import re
import typing
import yaml

try:
    import common.exceptions as exceptions
    import common.model as model
    import common.util as commonutil
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')


logger = logging.getLogger(__name__)


class ConfigFactory:
    def __init__(self):
        return

    def make_config(
        self,
        config_path: str,
    ) -> model.Config:
        if not os.path.isfile(config_path):
            raise FileNotFoundError

        systems: typing.List[model.System] = []
        components: typing.List[model.Component] = []

        with open(config_path, 'r') as f:
            logger.debug(f'{os.path.abspath(config_path)}')
            ydata = yaml.load(f, Loader=yaml.FullLoader)

            # parse metadata
            version = ydata.get('meta').get('schemaVersion')

            # parse systems
            for id, system in ydata['systems'].items():
                systems.append(model.System(
                    id=id,
                    name=system.get('name'),
                    ref=system.get('ref'),
                ))

            # parse components and metrics
            for id, component in ydata['components'].items():
                metrics: typing.List[model.Metric] = []
                for metric in component['metrics']:
                    metrics.append(model.Metric(
                        id=metric.get('name'),
                        endpoint=metric.get('endpoint'),
                        frequency=commonutil.parse_time_str_to_timedetail(metric.get('frequency') if metric.get('frequency') else '1m'),
                        expectedTime=commonutil.parse_time_str_to_timedetail(metric.get('expectedTime') if metric.get('expectedTime') else '50ms'),
                        timeout=commonutil.parse_time_str_to_timedetail(metric.get('timeout') if metric.get('timeout') else '200ms'),
                        deleteAfter=commonutil.parse_time_str_to_timedetail(metric.get('deleteAfter') if metric.get('deleteAfter') else '7d'),
                        authToken=metric.get('authToken') if metric.get('authToken') else component.get('authToken'),
                        baseUrl=metric.get('baseUrl') if metric.get('baseUrl') else component.get('baseUrl'),
                    ))
                components.append(model.Component(
                    id=id,
                    name=component.get('name'),
                    systemId=component.get('system'),
                    baseUrl=component.get('baseUrl'),
                    ref=component.get('ref'),
                    authToken=component.get('authToken'),
                    metrics=metrics,
                ))

        config: model.Config = model.Config(
            components=components,
            systems=systems,
            version=model.Version(version),
        )

        self._check_semantics(cfg=config)
        return config

    def _check_semantics(
        self,
        cfg: model.Config,
    ):
        def component_systems_are_defined(cfg: model.Config):
            system_ids = [s.id for s in cfg.systems]
            component_systems = [c.systemId for c in cfg.components]
            for id in component_systems:
                if id not in system_ids:
                    raise exceptions.OpenmonitorConfigError(
                        f'component system "{id}" not found in systems {system_ids}'
                    )

        def auth_token_is_secure(cfg: model.Config):
            components = [c for c in cfg.components]
            tokens = []
            for c in components:
                for metric in c.metrics:
                    tokens.append(metric.authToken)
            for t in tokens:
                if t.__len__() != 32:
                    raise exceptions.OpenmonitorConfigError(
                        f'authToken {t} has no length of 32'
                    )

        component_systems_are_defined(cfg=cfg)
        auth_token_is_secure(cfg=cfg)

import re
import typing

import yaml

import model


class ConfigNotOkayException(Exception):
    pass


def parse_config_path(
    config_file: str,
) -> typing.Tuple[typing.List[model.ComponentConfig], typing.List[model.SystemConfig]]:
    with open(config_file, 'r') as f:
        ydata = yaml.load(f, Loader=yaml.FullLoader)

        components: typing.List[model.ComponentConfig] = []
        for cid, c in ydata['components'].items():
            components.append(
                model.ComponentConfig(
                    id=cid,
                    name=c['name'],
                    baseUrl=c['baseUrl'],
                    statusEndpoint=c['statusEndpoint'],
                    frequency=c['frequency'],
                    systemId=c['system'],
                    ref=c['ref'],
                    expectedTime=c['expectedTime'],
                    timeout=c['timeout'],
                )
            )

        systems: typing.List[model.SystemConfig] = []
        for sid, s in ydata['systems'].items():
            systems.append(
                model.SystemConfig(
                    id=sid,
                    name=s['name'],
                    ref=s['ref'],
                )
            )

        _validate_config(
            components=components,
            systems=systems,
        )
        return components, systems


def _validate_config(
    components,
    systems,
):
    """
    Validates component and system configuration.
    - component.system is a valid system
    - component.frequency is a supported interval
    - component.expectedTime is a supported time
    - component.timeout is a supported time
    """
    def _is_supported_time(
        string: str,
        ms=False,
    ):
        return re.fullmatch(
            f'([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-9][0-9][0-9][0-9])({"ms|" if ms else ""}s|m|h)',
            string,
        )

    # component.system is a valid system
    sids = [s.id for s in systems]
    c_sids = [cc.systemId for cc in components]
    for c_sid in c_sids:
        if c_sid not in sids:
            raise ConfigNotOkayException(f'component system "{c_sid}" not found in systems {sids}')

    # component.frequency is a supported interval
    cfs = [cc.frequency for cc in components]
    for cf in cfs:
        if not _is_supported_time(
            string=cf,
        ):
            raise ConfigNotOkayException(f'component frequency {cf} is not in a supported format')

    # component.expectedTime is a supported time
    cets = [cc.expectedTime for cc in components]
    for cet in cets:
        if not _is_supported_time(
            string=cet,
            ms=True,
        ):
            raise ConfigNotOkayException(f'component expectedTime {cet} is not in a supported format')

    # component.timeout is a supported time
    ts = [cc.timeout for cc in components]
    for t in ts:
        if not _is_supported_time(
            string=t,
            ms=True,
        ):
            raise ConfigNotOkayException(f'component timeout {t} is not in a supported format')

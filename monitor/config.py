import logging
import re
import typing

import yaml

try:
    import model
    import util
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')


class ConfigNotOkayException(Exception):
    pass


logger = logging.getLogger(__name__)


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
                    deleteAfter=c['deleteAfter'],
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
    - deleteAfter is a supported time
    """

    def _add_timeunits_to_regex(
            regex_str: str,
            timeunits: dict,
    ) -> str:
        logger.debug(f'regex str in: {regex_str}')
        logger.debug(f'{timeunits=}')
        do_open_bracket = True
        for k, v in timeunits.items():
            if v:
                # on first timeunit add, init "("
                if do_open_bracket:
                    regex_str = regex_str + '('
                    do_open_bracket = False
                # add actual timeunit
                regex_str = regex_str + k + '|'
        # after all timeunits were added, remove trailing pipe
        if regex_str.endswith('|'):
            regex_str = regex_str.rstrip(regex_str[-1])
        # close bracket if added at beginning
        if not do_open_bracket:
            regex_str = regex_str + ')'
        logger.debug(f'regex str out: {regex_str}')
        return regex_str

    def _is_supported_time(
        string: str,
        ms=False,
        s=False,
        m=False,
        h=False,
        d=False,
    ):
        regex_str = '([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-9][0-9][0-9][0-9])'
        timeunits = {
            'ms': ms,
            's': s,
            'm': m,
            'h': h,
            'd': d,
        }
        regex_str = _add_timeunits_to_regex(
            regex_str=regex_str,
            timeunits=timeunits,
        )
        logger.debug(f'regex string to check: "{string=}"')
        return re.fullmatch(
            regex_str,
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
            s=True,
            m=True,
            h=True,
            d=True,
        ):
            raise ConfigNotOkayException(f'component frequency {cf} is not in a supported format')

    # component.expectedTime is a supported time
    cets = [cc.expectedTime for cc in components]
    for cet in cets:
        if not _is_supported_time(
            string=cet,
            ms=True,
            s=True,
            m=False,
            h=False,
            d=False,
        ):
            raise ConfigNotOkayException(f'component expectedTime {cet} is not in a supported format')

    # component.timeout is a supported time
    ts = [cc.timeout for cc in components]
    for t in ts:
        if not _is_supported_time(
            string=t,
            ms=True,
            s=True,
            m=False,
            h=False,
            d=False,
        ):
            raise ConfigNotOkayException(f'component timeout {t} is not in a supported format')

    # component.deleteAfter is a supported time
    das = [cc.deleteAfter for cc in components]
    for da in das:
        if not _is_supported_time(
            string=da,
            ms=False,
            s=False,
            m=True,
            h=True,
            d=True,
        ):
            raise ConfigNotOkayException(f'component deleteAfter {da} is not in a supported format')


def parse_component_config_to_component(
    component_config: model.ComponentConfig,
) -> model.Component:
    return model.Component(
        component=component_config.id,
        name=component_config.name,
        baseUrl=component_config.baseUrl,
        statusEndpoint=component_config.statusEndpoint,
        system=component_config.systemId,
        ref=component_config.ref,
        expectedTime=component_config.expectedTime,
        timeout=component_config.timeout,
        frequency=component_config.frequency,
    )


def parse_system_config_to_system(
    system_config: model.SystemConfig,
) -> model.System:
    return model.System(
        system=system_config.id,
        name=system_config.name,
        ref=system_config.ref,
    )

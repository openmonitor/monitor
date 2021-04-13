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
                    authToken=c['authToken'],
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
    # sid = system.id, sid_l = list(system.id)
    # c_sid = component.systemId, c_sid_l = list(component.systemId)
    sid_l = [s.id for s in systems]
    c_sid_l = [cc.systemId for cc in components]
    for c_sid in c_sid_l:
        if c_sid not in sid_l:
            raise ConfigNotOkayException(f'component system "{c_sid}" not found in systems {sid_l}')

    # component.frequency is a supported interval
    # fe = frequency, fe_l = list(frequency)
    fe_l = [cc.frequency for cc in components]
    for fe in fe_l:
        if not _is_supported_time(
            string=fe,
            s=True,
            m=True,
            h=True,
            d=True,
        ):
            raise ConfigNotOkayException(f'component frequency {fe} is not in a supported format')

    # component.expectedTime is a supported time
    # et = expectedTime, et_l = list(expectedTime)
    et_l = [cc.expectedTime for cc in components]
    for et in et_l:
        if not _is_supported_time(
            string=et,
            ms=True,
            s=True,
            m=False,
            h=False,
            d=False,
        ):
            raise ConfigNotOkayException(f'component expectedTime {et} is not in a supported format')

    # component.timeout is a supported time
    # to = timeout, to_l = list(timeout)
    to_l = [cc.timeout for cc in components]
    for to in to_l:
        if not _is_supported_time(
            string=to,
            ms=True,
            s=True,
            m=False,
            h=False,
            d=False,
        ):
            raise ConfigNotOkayException(f'component timeout {to} is not in a supported format')

    # component.deleteAfter is a supported time
    # da = deleteAfter, da_l = list(deleteAfter)
    da_l = [cc.deleteAfter for cc in components]
    for da in da_l:
        if not _is_supported_time(
            string=da,
            ms=False,
            s=False,
            m=True,
            h=True,
            d=True,
        ):
            raise ConfigNotOkayException(f'component deleteAfter {da} is not in a supported format')

    # authToken length check
    # at = authToken, at_l = list(authTokens)
    at_l = [cc.authToken for cc in components]
    for at in at_l:
        if at.__len__() is not 32:
            raise ConfigNotOkayException(f'component authToken {at} is not in a supported format')


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
        authToken=component_config.authToken,
    )


def parse_system_config_to_system(
    system_config: model.SystemConfig,
) -> model.System:
    return model.System(
        system=system_config.id,
        name=system_config.name,
        ref=system_config.ref,
    )

import re

try:
    import common.exceptions as exceptions
    import common.model as model
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')

def parse_time_str_to_timedetail(
    time_str :str,
) -> model.TimeDetail:
    regex = re.compile('([0-9]+)(ms|s|m|h|d)')
    res = regex.match(time_str)
    if not res:
        raise exceptions.OpenmonitorConfigError('Unable to parse config', time_str=time_str)
    return model.TimeDetail(
        value=res[1],
        unit=model.TimeUnit(res[2]),
    )

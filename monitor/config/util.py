import re

try:
    import common.model as model
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')

def parse_time_str_to_timedetail(
    time_str :str,
) -> model.TimeDetail:
    regex = re.compile('([0-9]+)(ms|s|m|h|d)')
    if not (res := regex.match(time_str).groups()):
        raise exceptions.OpenmonitorConfigError('Unable to parse config', time_str=time_str)
    return model.TimeDetail(
        value=res[0],
        unit=res[1],
    )

import pytest

try:
    import common.exceptions as exceptions
    import common.model as model
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')
import monitor.config.factory as fac


def test_ok_config():
    cfg_fac = fac.ConfigFactory()
    cfg = cfg_fac.make_config(config_path='./test/config_1.yaml')
    metrics = [model.Metric(
        id='cpu',
        endpoint='/cpu',
        frequency=model.TimeDetail(
            value=1,
            unit=model.TimeUnit('m'),
        ),
        expectedTime=model.TimeDetail(
            value=50,
            unit=model.TimeUnit('ms'),
        ),
        timeout=model.TimeDetail(
            value=200,
            unit=model.TimeUnit('ms'),
        ),
        deleteAfter=model.TimeDetail(
            value=7,
            unit=model.TimeUnit('d'),
        ),
        authToken='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        baseUrl='http://127.0.0.1:1338',
    )]
    components = [model.Component(
        id='test-component',
        name='test',
        systemId='openmonitor',
        baseUrl='http://127.0.0.1:1338',
        ref='https://github.com/openmonitor/test',
        authToken='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        metrics=metrics,
    )]
    systems = [model.System(
        id='openmonitor',
        name='OpenMonitor',
        ref='https://github.com/openmonitor',
    )]
    cfg_expected = model.Config(
        components=components,
        systems=systems,
        version=model.Version('v2'),
    )
    assert cfg == cfg_expected


def test_faulty_system_config():
    cfg_fac = fac.ConfigFactory()
    with pytest.raises(exceptions.OpenmonitorConfigError):
        cfg_fac.make_config(config_path='./test/config_2.yaml')


def test_no_cfg():
    cfg_fac = fac.ConfigFactory()
    with pytest.raises(FileNotFoundError):
        cfg_fac.make_config(config_path='./test/config_missing.yaml')


def test_faulty_component_config():
    cfg_fac = fac.ConfigFactory()
    with pytest.raises(AttributeError):
        cfg_fac.make_config(config_path='./test/config_3.yaml')

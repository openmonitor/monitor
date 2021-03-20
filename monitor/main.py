import config

try:
    import database
except ModuleNotFoundError:
    print('common package not in python path')


if __name__ == '__main__':
    # parse config
    config.parse_config_path(
        config_file='./../monitor-config.yml',
    )

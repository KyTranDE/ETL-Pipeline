import  configparser
def read_params_from_config (file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    params = {key.replace('_', '-'): value for key, value in config.items('params')}
    return params

read_params_from_config('./config/config.ini')
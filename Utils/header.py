import configparser
def read_headers_from_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    headers = {key.replace('_', '-'): value for key, value in config.items('headers')}
    return headers
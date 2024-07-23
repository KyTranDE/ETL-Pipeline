import os
import sys
sys.path.append('../')

def logger(path_log, text):
    os.makedirs(f'{"/".join(path_log.split("/")[:-1])}', exist_ok=True)
    with open(f'{path_log}', 'a+', encoding='utf-8') as f:
        f.write(str(text) + '\n')
        f.close()
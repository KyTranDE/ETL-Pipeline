#!/bin/bash

if [ ! -d ".venv" ]; then
    echo "Môi trường ảo không tồn tại. Đang tạo môi trường ảo..."
    python -m venv .venv || { echo "Không thể tạo môi trường ảo"; exit 1; }
fi

source .venv/bin/activate
i=0
# count = 1000
while [ $i -lt 12 ]; do
    python3 getMatchRedis.py >> /home/bbsw/bbsw/logs/insert_match.log 2>&1
    sleep 5
    i=$(( i + 1 ))
    rm -rf /home/bbsw/bbsw/logs/insert_match.log

    # if [ $i -eq $count ]; then
    #     break
    # fi

done

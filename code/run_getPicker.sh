#!/bin/bash

if [ ! -d ".venv" ]; then
    echo "Môi trường ảo không tồn tại. Đang tạo môi trường ảo..."
    python -m venv .venv || { echo "Không thể tạo môi trường ảo"; exit 1; }
fi

source .venv/bin/activate

python3 getPicker.py >> /home/bbsw/bbsw/logs/insert_pickers.log 2>&1

rm -rf /home/bbsw/bbsw/logs/insert_pickers.log
rm -rf /home/bbsw/bbsw/logs/insert_expert_ats.log
rm -rf /home/bbsw/bbsw/logs/insert_expert_ou.log

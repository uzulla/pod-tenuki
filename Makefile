SHELL := /bin/bash

boot: venv
	source ./venv/bin/activate && bash

venv: 
	python3 -m venv venv
	source ./venv/bin/activate && pip install . && pip install -r requirements.txt

clean:
	rm -rf venv

# 全ての__pycache__ディレクトリを削除
cleanpycache:
	find . -type d -name "__pycache__" -exec rm -rf {} +

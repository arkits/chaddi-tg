set -e

export PYTHONPATH=$PYTHONPATH:$(pwd)

cd src

python chaddi.py

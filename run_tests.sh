# note that for unit tests to be discovered, they must be in directories with an __init__.py file

source env/source_virtualenv

# or even "python -m unittest" since i'm using the default file name pattern
python -m unittest discover -p "test_*.py"
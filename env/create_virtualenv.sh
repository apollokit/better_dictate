virtualenv_dir=$HOME/.config/virtualenvs/bdict_venv

# If the virtualenv already exists, just update requirements.
if [ -e "$virtualenv_dir" ]; then
	echo "$virtualenv_dir already exists. We'll just update requirements."
else
	virtualenv -p python3.8  $virtualenv_dir
	./setup.sh
fi

source source_virtualenv
pip install -r requirements.txt

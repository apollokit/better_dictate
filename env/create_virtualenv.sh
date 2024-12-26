virtualenv_dir=$HOME/.config/virtualenvs/bdict_venv

# If the virtualenv already exists, just update requirements.
if [ -e "$virtualenv_dir" ]; then
	echo "$virtualenv_dir already exists. We'll just update requirements."
else
	python3.11 -m venv $virtualenv_dir
fi

source source_virtualenv
./install_packages.sh
pip install -r requirements.txt

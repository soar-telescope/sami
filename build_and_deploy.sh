#!/usr/bin/env bash
python3 setup.py sdist bdist_wheel
twine upload dist/* --verbose
rm -Rf .eggs build dist
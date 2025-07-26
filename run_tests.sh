#!/bin/bash
set -x
test_log=test.$(date +'%Y%m%dT%H%M%S').log
python test.py && python -m unittest |& tes $test_log

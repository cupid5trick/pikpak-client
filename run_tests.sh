#!/bin/bash
set -x
test_log=test.$(date +'%Y%m%dT%H%M%S').log
(poetry run -- python test.py && python -m unittest) |& tee $test_log

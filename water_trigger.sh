#!/bin/bash
cd /home/pi/code/watering-app
python3 trigger.py >> trigger_hist.log 2>&1


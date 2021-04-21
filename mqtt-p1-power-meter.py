#!/usr/bin/env python

###############################################################################
# mqtt-p1-power-meter.py
#
# This file is part of the VSCP (http://www.vscp.org)
#
# The MIT License (MIT)
#
# Copyright © 2000-2021 Ake Hedman, Grodans Paradis AB <info@grodansparadis.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import configparser
import getopt

import vscp
import vscp_class as vc
import vscp_type as vt

import json
import serial
import paho.mqtt.client as mqtt

import math
import time

# Set to True to run with simulated data
bDebug = False

config = configparser.ConfigParser()

def usage():
    print("usage: mqtt-p1-power-meter.py -v -c <pat-to-config-file> -h ")
    print("---------------------------------------------")
    print("-h/--help    - This text.")
    print("-v/--verbose - Print output also to screen.")
    print("-c/--config  - Path to configuration file.")

# ----------------------------------------------------------------------------
#                              C O N F I G U R E
# ----------------------------------------------------------------------------

# Print some info along the way
bVerbose = False

# GUID for sensors (Ethernet MAC used if empty)
# Should normally have two LSB's set to zero for sensor id use
guid=""

# MQTT broker
host="127.0.0.1"

# MQTT broker port
port=1883

# Username to login at server
user="vscp"

# Password to login at server
password="secret"

# MQTT publish topic. 
#   %guid% is replaced with GUID
#   %class% is replaced with event class
#   %type% is replaced with event type   
topic="vscp/{xguid}/{xclass}/{xtype}"

# Sensor index for measurements
# Default is to use GUID to identify sensor
sensorindex_temperature = 0
sensorindex_sum_active_energy_out=1
sensorindex_sum_active_energy_in=2
sensorindex_sum_reactive_energy_out=3
sensorindex_sum_reactive_energy_in=4

sensorindex_momentan_active_effect_out=5
sensorindex_momentan_active_effect_in=6
sensorindex_momentan_reactive_effect_out=7
sensorindex_momentan_reactive_effect_in=8

sensorindex_momentan_active_effect_l1_out=9
sensorindex_momentan_active_effect_l1_in=10

sensorindex_momentan_active_effect_l2_out=11
sensorindex_momentan_active_effect_l2_in=12

sensorindex_momentan_active_effect_l3_out=13
sensorindex_momentan_active_effect_l3_in=14

sensorindex_momentan_reactive_effect_l1_out=15
sensorindex_momentan_reactive_effect_l1_in=16

sensorindex_momentan_reactive_effect_l2_out=17
sensorindex_momentan_reactive_effect_l2_in=18

sensorindex_momentan_reactive_effect_l3_out=19
sensorindex_momentan_reactive_effect_l3_in=20

sensorindex_voltage_l1=21
sensorindex_voltage_l2=22
sensorindex_voltage_l3=23

sensorindex_current_l1=24
sensorindex_current_l2=25
sensorindex_current_l3=26

sensorindex_phase_factor_l1=27
sensorindex_phase_factor_l2=28
sensorindex_phase_factor_l3=29

# Zone for module
zone=0

# Subzone for module
subzone=0

# Last two bytes for GUID is made up of number
# given here on the form MSB:LSB
id_sum_active_energy_out=1
id_sum_active_energy_in=2
id_sum_reactive_energy_out=3
id_sum_reactive_energy_in=4

id_momentan_active_effect_out=5
id_momentan_active_effect_in=6
id_momentan_reactive_effect_out=7
id_momentan_reactive_effect_in=8

id_momentan_active_effect_l1_out=9
id_momentan_active_effect_l1_in=10

id_momentan_active_effect_l2_out=11
id_momentan_active_effect_l2_in=12

id_momentan_active_effect_l3_out=13
id_momentan_active_effect_l3_in=14

id_momentan_reactive_effect_l1_out=15
id_momentan_reactive_effect_l1_in=16

id_momentan_reactive_effect_l2_out=17
id_momentan_reactive_effect_l2_in=18

id_momentan_reactive_effect_l3_out=19
id_momentan_reactive_effect_l3_in=20

id_voltage_l1=21
id_voltage_l2=22
id_voltage_l3=23

id_current_l1=24
id_current_l2=25
id_current_l3=26

id_phase_factor_l1=27
id_phase_factor_l2=28
id_phase_factor_l3=29

note_sum_active_energy_out="Meter reading active energy out"
note_sum_active_energy_in="Meter reading active energy in"
note_sum_reactive_energy_out="Meter reading reactive energy out"
note_sum_reactive_energy_in="Meter reading reactive energy in"

note_momentan_active_effect_out="Active effect out"
note_momentan_active_effect_in="Active effect in"
note_momentan_reactive_effect_out="Reactive effect out"
note_momentan_reactive_effect_in="Reactive effect in"

note_momentan_active_effect_l1_out="Active effect L1 out"
note_momentan_active_effect_l1_in="Active effect L1 in"

note_momentan_active_effect_l2_out="Active effect L2 out"
note_momentan_active_effect_l2_in="Active effect L2 in"

note_momentan_active_effect_l3_out="Active effect L3 out"
note_momentan_active_effect_l3_in="Active effect L3 in"

note_momentan_reactive_effect_l1_out="Reactive effect L1 out"
note_momentan_reactive_effect_l1_in="Reactive effect L1 in"

note_momentan_reactive_effect_l2_out="Reactive effect L2 out"
note_momentan_reactive_effect_l2_in="Reactive effect L2 in"

note_momentan_reactive_effect_l3_out="Reactive effect L3 out"
note_momentan_reactive_effect_l3_in="Reactive effect L3 in"

note_voltage_l1="Voltage L1"
note_voltage_l2="Voltage L2"
note_voltage_l3="Voltage L3"

note_current_l1="Current L1"
note_current_l2="Current L2"
note_current_l3="Current L3"

note_phase_factor_l1="Phase factor L1"
note_phase_factor_l2="Phase factor L2"
note_phase_factor_l3="Phase factor L3"

# Configuration will be read from path set here
cfgpath=""   

# ----------------------------------------------------------------------------

args = sys.argv[1:]
nargs = len(args)

try:
    opts, args = getopt.getopt(args,"hvc:",["help","verbose","config="])
except getopt.GetoptError:
    print("unrecognized format!")
    usage()
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-h", "--help"):
        print("HELP")
        usage()
        sys.exit()
    elif opt in ("-v", "--verbose"):
        bVerbose = True
    elif opt in ("-c", "--config"):
        cfgpath = arg

if (len(cfgpath)):

    init = config.read(cfgpath)

    # ----------------- GENERAL -----------------
    if 'bVerbose' in config['GENERAL']:
        bVerbose = config.getboolean('GENERAL','bVerbose')
        if bVerbose :
            print('Verbose mode enabled.')
            print('READING CONFIGURATION')
            print('---------------------')    

    # ----------------- VSCP -----------------
    if 'guid' in config['VSCP']:        
        guid = config['VSCP']['guid']
        if bVerbose:
            print("guid =", guid, len(guid))
    
    if 'sensorindex_sum_active_energy_out' in config['VSCP']:        
        sensorindex_sum_active_energy_out = int(config['VSCP']['sensorindex_sum_active_energy_out'])
        if bVerbose:
            print("sensorindex_sum_active_energy_out =", sensorindex_sum_active_energy_out)

    if 'sensorindex_sum_active_energy_in' in config['VSCP']:        
        sensorindex_sum_active_energy_in = int(config['VSCP']['sensorindex_sum_active_energy_in'])
        if bVerbose:
            print("sensorindex_sum_active_energy_in =", sensorindex_sum_active_energy_in)    

    if 'sensorindex_sum_reactive_energy_out' in config['VSCP']:        
        sensorindex_sum_reactive_energy_out = int(config['VSCP']['sensorindex_sum_reactive_energy_out'])
        if bVerbose:
            print("sensorindex_sum_reactive_energy_out =", sensorindex_sum_reactive_energy_out) 
    
    if 'sensorindex_sum_reactive_energy_in' in config['VSCP']:        
        sensorindex_sum_reactive_energy_in = int(config['VSCP']['sensorindex_sum_reactive_energy_in'])
        if bVerbose:
            print("sensorindex_sum_reactive_energy_in =", sensorindex_sum_reactive_energy_in) 

    if 'sensorindex_momentan_active_effect_out' in config['VSCP']:        
        sensorindex_momentan_active_effect_out = int(config['VSCP']['sensorindex_momentan_active_effect_out'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_out =", sensorindex_momentan_active_effect_out)

    if 'sensorindex_momentan_active_effect_in' in config['VSCP']:        
        sensorindex_momentan_active_effect_in = int(config['VSCP']['sensorindex_momentan_active_effect_in'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_in =", sensorindex_momentan_active_effect_in)

    if 'sensorindex_momentan_reactive_effect_out' in config['VSCP']:        
        sensorindex_momentan_reactive_effect_out = int(config['VSCP']['sensorindex_momentan_reactive_effect_out'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect_out =", sensorindex_momentan_reactive_effect_out)

    if 'sensorindex_momentan_reactive_effect_in' in config['VSCP']:        
        sensorindex_momentan_reactive_effect_in = int(config['VSCP']['sensorindex_momentan_reactive_effect_in'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect =", sensorindex_momentan_reactive_effect_in)

    if 'sensorindex_momentan_active_effect_l1_out' in config['VSCP']:        
        sensorindex_momentan_active_effect_l1_out = int(config['VSCP']['sensorindex_momentan_active_effect_l1_out'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_l1_out =", sensorindex_momentan_active_effect_l1_out)

    if 'sensorindex_momentan_active_effect_l1_in' in config['VSCP']:        
        sensorindex_momentan_active_effect_l1_in = int(config['VSCP']['sensorindex_momentan_active_effect_l1_in'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_l1_in =", sensorindex_momentan_active_effect_l1_in)

    if 'sensorindex_momentan_active_effect_l2_out' in config['VSCP']:        
        sensorindex_momentan_active_effect_l2_out = int(config['VSCP']['sensorindex_momentan_active_effect_l2_out'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_l2_out =", sensorindex_momentan_active_effect_l2_out)

    if 'sensorindex_momentan_active_effect_l2_in' in config['VSCP']:        
        sensorindex_momentan_active_effect_l2_in = int(config['VSCP']['sensorindex_momentan_active_effect_l2_in'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_l2_in =", sensorindex_momentan_active_effect_l2_in)

    if 'sensorindex_momentan_active_effect_l3_out' in config['VSCP']:        
        sensorindex_momentan_active_effect_l3_out = int(config['VSCP']['sensorindex_momentan_active_effect_l3_out'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_l3_out =", sensorindex_momentan_active_effect_l3_out)

    if 'sensorindex_momentan_active_effect_l3_in' in config['VSCP']:        
        sensorindex_momentan_active_effect_l3_in = int(config['VSCP']['sensorindex_momentan_active_effect_l3_in'])
        if bVerbose:
            print("sensorindex_momentan_active_effect_l3_in =", sensorindex_momentan_active_effect_l3_in)            

    if 'sensorindex_momentan_reactive_effect_l1_out' in config['VSCP']:        
        sensorindex_momentan_reactive_effect_l1_out = int(config['VSCP']['sensorindex_momentan_reactive_effect_l1_out'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect_l1_out =", sensorindex_momentan_reactive_effect_l1_out)

    if 'sensorindex_momentan_reactive_effect_l1_in' in config['VSCP']:        
        sensorindex_momentan_reactive_effect_l1_in = int(config['VSCP']['sensorindex_momentan_reactive_effect_l1_in'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect_l1_in =", sensorindex_momentan_reactive_effect_l1_in)

    if 'sensorindex_momentan_reactive_effect_l2_out' in config['VSCP']:        
        sensorindex_momentan_reactive_effectl2_out = int(config['VSCP']['sensorindex_momentan_reactive_effect_l2_out'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect_l2_out =", sensorindex_momentan_reactive_effect_l2_out)

    if 'sensorindex_momentan_reactive_effect_l2_in' in config['VSCP']:        
        sensorindex_momentan_reactive_effect_l2_in = int(config['VSCP']['sensorindex_momentan_reactive_effect_l2_in'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect_l2_in =", sensorindex_momentan_reactive_effect_l2_in)

    if 'sensorindex_momentan_reactive_effect_l3_out' in config['VSCP']:        
        sensorindex_momentan_reactive_effect_l3_out = int(config['VSCP']['sensorindex_momentan_reactive_effect_l3_out'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect_l3_out =", sensorindex_momentan_reactive_effect_l3_out)

    if 'sensorindex_momentan_reactive_effect_l3_in' in config['VSCP']:        
        sensorindex_momentan_reactive_effect_l3_in = int(config['VSCP']['sensorindex_momentan_reactive_effect_l3_in'])
        if bVerbose:
            print("sensorindex_momentan_reactive_effect_l3_in =", sensorindex_momentan_reactive_effect_l3_in)

    if 'sensorindex_voltage_l1' in config['VSCP']:        
        sensorindex_voltage_l1 = int(config['VSCP']['sensorindex_voltage_l1'])
        if bVerbose:
            print("sensorindex_voltage_l1 =", sensorindex_voltage_l1)

    if 'sensorindex_voltage_l2' in config['VSCP']:        
        sensorindex_voltage_l2 = int(config['VSCP']['sensorindex_voltage_l2'])
        if bVerbose:
            print("sensorindex_voltage_l2 =", sensorindex_voltage_l2)

    if 'sensorindex_voltage_l3' in config['VSCP']:        
        sensorindex_voltage_l3 = int(config['VSCP']['sensorindex_voltage_l3'])
        if bVerbose:
            print("sensorindex_voltage_l3 =", sensorindex_voltage_l3)

    if 'sensorindex_current_l1' in config['VSCP']:        
        sensorindex_current_l1 = int(config['VSCP']['sensorindex_current_l1'])
        if bVerbose:
            print("sensorindex_current_l1 =", sensorindex_current_l1)

    if 'sensorindex_current_l2' in config['VSCP']:        
        sensorindex_current_l2 = int(config['VSCP']['sensorindex_current_l2'])
        if bVerbose:
            print("sensorindex_current_l2 =", sensorindex_current_l2)

    if 'sensorindex_current_l3' in config['VSCP']:        
        sensorindex_current_l3 = int(config['VSCP']['sensorindex_current_l3'])
        if bVerbose:
            print("sensorindex_current_l3 =", sensorindex_current_l3)

    if 'sensorindex_phase_factor_l1' in config['VSCP']:        
        sensorindex_phase_factor_l1 = int(config['VSCP']['sensorindex_phase_factor_l1'])
        if bVerbose:
            print("sensorindex_phase_factor_l1 =", sensorindex_phase_factor_l1)

    if 'sensorindex_phase_factor_l2' in config['VSCP']:        
        sensorindex_phase_factor_l2 = int(config['VSCP']['sensorindex_phase_factor_l2'])
        if bVerbose:
            print("sensorindex_phase_factor_l2 =", sensorindex_phase_factor_l2)

    if 'sensorindex_phase_factor_l3' in config['VSCP']:        
        sensorindex_phase_factor_l3 = int(config['VSCP']['sensorindex_phase_factor_l3'])
        if bVerbose:
            print("sensorindex_phase_factor_l3 =", sensorindex_phase_factor_l3)            
    
    if 'zone' in config['VSCP']:        
        zone = int(config['VSCP']['zone'])
        if bVerbose:
            print("zone =", zone)

    if 'subzone' in config['VSCP']:        
        subzone = int(config['VSCP']['subzone'])
        if bVerbose:
            print("subzone =", subzone)
    
    if 'id_sum_active_energy_out' in config['VSCP']:        
        id_sum_active_energy_out = int(config['VSCP']['id_sum_active_energy_out'])
        if bVerbose:
            print("id_temperature =", id_sum_active_energy_out)
    
    if 'id_sum_active_energy_in' in config['VSCP']:        
        id_sum_active_energy_in = int(config['VSCP']['id_sum_active_energy_in'])
        if bVerbose:
            print("id_temperature =", id_sum_active_energy_out)

    if 'id_sum_reactive_energy_out' in config['VSCP']:        
        id_sum_reactive_energy_out = int(config['VSCP']['id_sum_reactive_energy_out'])
        if bVerbose:
            print("id_sum_reactive_energy_out =", id_sum_reactive_energy_out)

    if 'id_sum_reactive_energy' in config['VSCP']:        
        id_sum_reactive_energy_in = int(config['VSCP']['id_sum_reactive_energy_in'])
        if bVerbose:
            print("id_sum_reactive_energy_in =", id_sum_reactive_energy_in)                

    if 'id_momentan_active_energy_out' in config['VSCP']:        
        id_momentan_active_energy_out = int(config['VSCP']['id_momentan_active_energy_out'])
        if bVerbose:
            print("id_momentan_active_energy_out =", id_momentan_active_energy_out)

    if 'id_momentan_active_energy_in' in config['VSCP']:        
        id_momentan_active_energy_in = int(config['VSCP']['id_momentan_active_energy_in'])
        if bVerbose:
            print("id_momentan_active_energy_in =", id_momentan_active_energy_in)

    if 'id_momentan_reactive_energy_out' in config['VSCP']:        
        id_momentan_reactive_energy_out = int(config['VSCP']['id_momentan_reactive_energy_out'])
        if bVerbose:
            print("id_momentan_reactive_energy_out =", id_momentan_reactive_energy_out)

    if 'id_momentan_reactive_energy_in' in config['VSCP']:        
        id_momentan_reactive_energy_in = int(config['VSCP']['id_momentan_reactive_energy_in'])
        if bVerbose:
            print("id_temperature =", id_momentan_reactive_energy_in)

    if 'id_momentan_active_energy_l1_out' in config['VSCP']:        
        id_momentan_active_energy_l1_out = int(config['VSCP']['id_momentan_active_energy_l1_out'])
        if bVerbose:
            print("id_momentan_active_energy_l1_out =", id_momentan_active_energy_l1_out)

    if 'id_momentan_active_energy_l1_out' in config['VSCP']:        
        id_momentan_active_energy_l1_out = int(config['VSCP']['id_momentan_active_energy_l1_out'])
        if bVerbose:
            print("id_momentan_active_energy_l1_out =", id_momentan_active_energy_l1_out)

    if 'id_momentan_active_energy_l2_out' in config['VSCP']:        
        id_momentan_active_energy_l2_out = int(config['VSCP']['id_momentan_active_energy_l2_out'])
        if bVerbose:
            print("id_momentan_active_energy_l2_out =", id_momentan_active_energy_l2_out)

    if 'id_momentan_active_energy_l3_out' in config['VSCP']:        
        id_momentan_active_energy_l3_out = int(config['VSCP']['id_momentan_active_energy_l3_out'])
        if bVerbose:
            print("id_momentan_active_energy_l3_out =", id_momentan_active_energy_l3_out)

    if 'id_momentan_reactive_energy_l1_out' in config['VSCP']:        
        id_momentan_reactive_energy_l1_out = int(config['VSCP']['id_momentan_reactive_energy_l1_out'])
        if bVerbose:
            print("id_momentan_reactive_energy_l1_out =", id_momentan_reactive_energy_l1_out)

    if 'id_momentan_reactive_energy_l1_in' in config['VSCP']:        
        id_momentan_reactive_energy_l1_in = int(config['VSCP']['id_momentan_reactive_energy_l1_in'])
        if bVerbose:
            print("id_momentan_reactive_energy_l1_in =", id_momentan_reactive_energy_l1_in)

    if 'id_momentan_reactive_energy_l2_out' in config['VSCP']:        
        id_momentan_reactive_energy_l2_out = int(config['VSCP']['id_momentan_reactive_energy_l2_out'])
        if bVerbose:
            print("id_momentan_reactive_energy_l2_out =", id_momentan_reactive_energy_l2_out)

    if 'id_momentan_reactive_energy_l3_in' in config['VSCP']:        
        id_momentan_reactive_energy_l3_in = int(config['VSCP']['id_momentan_reactive_energy_l3_in'])
        if bVerbose:
            print("id_momentan_reactive_energy_l3_in =", id_momentan_reactive_energy_l3_in)

    if 'id_voltage_l1' in config['VSCP']:        
        id_voltage_l1 = int(config['VSCP']['id_voltage_l1'])
        if bVerbose:
            print("id_voltage_l1 =", id_voltage_l1)

    if 'id_voltage_l1' in config['VSCP']:        
        id_voltage_l2 = int(config['VSCP']['id_voltage_l2'])
        if bVerbose:
            print("id_voltage_l2 =", id_voltage_l2)

    if 'id_voltage_l3' in config['VSCP']:        
        id_voltage_l3 = int(config['VSCP']['id_voltage_l3'])
        if bVerbose:
            print("id_voltage_l3 =", id_voltage_l3)

    if 'id_current_l1' in config['VSCP']:        
        id_current_l1 = int(config['VSCP']['id_current_l1'])
        if bVerbose:
            print("id_current_l1 =", id_current_l1)                                    

    if 'id_current_l2' in config['VSCP']:        
        id_current_l2 = int(config['VSCP']['id_current_l2'])
        if bVerbose:
            print("id_current_l2 =", id_current_l2)  

    if 'id_current_l3' in config['VSCP']:        
        id_current_l3 = int(config['VSCP']['id_current_l3'])
        if bVerbose:
            print("id_current_l3 =", id_current_l3)  

    if 'id_phase_factor_l1' in config['VSCP']:        
        id_current_l1 = int(config['VSCP']['id_phase_factor_l1'])
        if bVerbose:
            print("id_phase_factor_l1 =", id_phase_factor_l1)                          

    if 'id_phase_factor_l2' in config['VSCP']:        
        id_current_l2 = int(config['VSCP']['id_phase_factor_l2'])
        if bVerbose:
            print("id_phase_factor_l2 =", id_phase_factor_l2) 

    if 'id_phase_factor_l3' in config['VSCP']:        
        id_current_l3 = int(config['VSCP']['id_phase_factor_l3'])
        if bVerbose:
            print("id_phase_factor_l3 =", id_phase_factor_l3) 
    
    # ----------------- MQTT -----------------
    if 'host' in config['MQTT']:        
        host = config['MQTT']['host']
        if bVerbose:
            print("host =", host)

    if 'port' in config['MQTT']:        
        port = int(config['MQTT']['port'])
        if bVerbose:
            print("port =", port)

    if 'user' in config['MQTT']:        
        user = config['MQTT']['user']
        if bVerbose:
            print("user =", user)
    
    if 'password' in config['MQTT']:        
        password = config['MQTT']['password']
        if bVerbose:
            print("password =", "***********")
            #print("password =", password)

    if 'topic' in config['MQTT']:        
        topic = config['MQTT']['topic']
        if bVerbose:
            print("topic =", password)
    
    if 'note_sum_active_energy_out' in config['MQTT']:        
        note_sum_active_energy_out = config['MQTT']['note_sum_active_energy_out']
        if bVerbose:
            print("note_sum_active_energy_out =", note_sum_active_energy_out)
    
    if 'note_sum_active_energy_in' in config['MQTT']:        
        note_sum_active_energy_in = config['MQTT']['note_sum_active_energy_in']
        if bVerbose:
            print("note_sum_active_energy_in =", note_sum_active_energy_in)

    if 'note_sum_reactive_energy_out' in config['MQTT']:        
        note_sum_reactive_energy_out = config['MQTT']['note_sum_reactive_energy_out']
        if bVerbose:
            print("note_sum_reactive_energy_out =", note_sum_reactive_energy_out)

    if 'note_sum_reactive_energy_in' in config['MQTT']:        
        note_sum_reactive_energy_in = config['MQTT']['note_sum_reactive_energy_in']
        if bVerbose:
            print("note_sum_reactive_energy_in =", note_sum_reactive_energy_in)

    if 'note_momentan_active_effect_out' in config['MQTT']:        
        note_momentan_active_effect_out = config['MQTT']['note_momentan_active_effect_out']
        if bVerbose:
            print("note_momentan_active_effect_out =", note_momentan_active_effect_out)

    if 'note_momentan_active_effect_in' in config['MQTT']:        
        note_momentan_active_effect_in = config['MQTT']['note_momentan_active_effect_in']
        if bVerbose:
            print("note_momentan_active_effect_in =", note_momentan_active_effect_in)

    if 'note_momentan_reactive_effect_out' in config['MQTT']:        
        note_momentan_reactive_effect_out = config['MQTT']['note_momentan_reactive_effect_out']
        if bVerbose:
            print("note_momentan_reactive_effect_out =", note_momentan_reactive_effect_out)

    if 'note_momentan_reactive_effect_in' in config['MQTT']:        
        note_momentan_reactive_effect_in = config['MQTT']['note_momentan_reactive_effect_in']
        if bVerbose:
            print("note_momentan_reactive_effect_in =", note_momentan_reactive_effect_in)

    if 'note_momentan_active_effect_l1_out' in config['MQTT']:        
        note_momentan_active_effect_l1_out = config['MQTT']['note_momentan_active_effect_l1_out']
        if bVerbose:
            print("note_momentan_active_effect_l1_out =", note_momentan_active_effect_l1_out)

    if 'note_momentan_active_effect_l1_in' in config['MQTT']:        
        note_momentan_active_effect_l1_in = config['MQTT']['note_momentan_active_effect_l1_in']
        if bVerbose:
            print("note_momentan_active_effect_l1_in =", note_momentan_active_effect_l1_in)

    if 'note_momentan_active_effect_l2_out' in config['MQTT']:        
        note_momentan_active_effect_l2_out = config['MQTT']['note_momentan_active_effect_l2_out']
        if bVerbose:
            print("note_momentan_active_effect_l2_out =", note_momentan_active_effect_l2_out)

    if 'note_momentan_active_effect_l2_in' in config['MQTT']:        
        note_momentan_active_effect_l2_in = config['MQTT']['note_momentan_active_effect_l2_in']
        if bVerbose:
            print("note_momentan_active_effect_l2_in =", note_momentan_active_effect_l2_in)

    if 'note_momentan_active_effect_l3_out' in config['MQTT']:        
        note_momentan_active_effect_l3_out = config['MQTT']['note_momentan_active_effect_l3_out']
        if bVerbose:
            print("note_momentan_active_effect_l3_out =", note_momentan_active_effect_l3_out)

    if 'note_momentan_active_effect_l3_in' in config['MQTT']:        
        note_momentan_active_effect_l3_in = config['MQTT']['note_momentan_active_effect_l3_in']
        if bVerbose:
            print("note_momentan_active_effect_l3_in =", note_momentan_active_effect_l3_in)

    if 'note_momentan_reactive_effect_l1_out' in config['MQTT']:        
        note_momentan_reactive_effect_l1_out = config['MQTT']['note_momentan_reactive_effect_l1_out']
        if bVerbose:
            print("note_momentan_reactive_effect_l1_out =", note_momentan_reactive_effect_l1_out)

    if 'note_momentan_reactive_effect_l1_in' in config['MQTT']:        
        note_momentan_reactive_effect_l1_in = config['MQTT']['note_momentan_reactive_effect_l1_in']
        if bVerbose:
            print("note_momentan_reactive_effect_l1_in =", note_momentan_reactive_effect_l1_in)

    if 'note_momentan_reactive_effect_l2_out' in config['MQTT']:        
        note_momentan_reactive_effect_l2_out = config['MQTT']['note_momentan_reactive_effect_l2_out']
        if bVerbose:
            print("note_momentan_reactive_effect_l2_out =", note_momentan_reactive_effect_l2_out)

    if 'note_momentan_reactive_effect_l2_in' in config['MQTT']:        
        note_momentan_reactive_effect_l2_in = config['MQTT']['note_momentan_reactive_effect_l2_in']
        if bVerbose:
            print("note_momentan_reactive_effect_l2_in =", note_momentan_reactive_effect_l2_in)

    if 'note_momentan_reactive_effect_l3_out' in config['MQTT']:        
        note_momentan_reactive_effect_l3_out = config['MQTT']['note_momentan_reactive_effect_l3_out']
        if bVerbose:
            print("note_momentan_reactive_effect_l3_out =", note_momentan_reactive_effect_l3_out)

    if 'note_momentan_reactive_effect_l3_in' in config['MQTT']:        
        note_momentan_reactive_effect_l3_in = config['MQTT']['note_momentan_reactive_effect_l3_in']
        if bVerbose:
            print("note_momentan_reactive_effect_l3_in =", note_momentan_reactive_effect_l3_in)        

    if 'note_voltage_l1' in config['MQTT']:        
        note_voltage_l1 = config['MQTT']['note_voltage_l1']
        if bVerbose:
            print("note_voltage_l1 =", note_voltage_l1) 

    if 'note_voltage_l2' in config['MQTT']:        
        note_voltage_l2 = config['MQTT']['note_voltage_l2']
        if bVerbose:
            print("note_voltage_l2 =", note_voltage_l2) 

    if 'note_voltage_l3' in config['MQTT']:        
        note_voltage_l3 = config['MQTT']['note_voltage_l3']
        if bVerbose:
            print("note_voltage_l3 =", note_voltage_l3) 

    if 'note_current_l1' in config['MQTT']:        
        note_current_l1 = config['MQTT']['note_current_l1']
        if bVerbose:
            print("note_current_l1 =", note_current_l1)                         

    if 'note_current_l2' in config['MQTT']:        
        note_current_l2 = config['MQTT']['note_current_l2']
        if bVerbose:
            print("note_current_l2 =", note_current_l2)  

    if 'note_current_l3' in config['MQTT']:        
        note_current_l3 = config['MQTT']['note_current_l3']
        if bVerbose:
            print("note_current_l3 =", note_current_l3)  

    if 'note_phase_factor_l1' in config['MQTT']:        
        note_phase_factor_l1 = config['MQTT']['note_phase_factor_l1']
        if bVerbose:
            print("note_phase_factor_l1 =", note_phase_factor_l1)  

    if 'note_phase_factor_l2' in config['MQTT']:        
        note_phase_factor_l2 = config['MQTT']['note_phase_factor_l2']
        if bVerbose:
            print("note_phase_factor_l2 =", note_phase_factor_l2)   

    if 'note_phase_factor_l3' in config['MQTT']:        
        note_phase_factor_l3 = config['MQTT']['note_phase_factor_l3']
        if bVerbose:
            print("note_phase_factor_l3 =", note_phase_factor_l3)                    
    

# -----------------------------------------------------------------------------

# define message callback
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

# define connect callback
def on_connect(client, userdata, flags, rc):
    print("Connected =",str(rc))

client= mqtt.Client()

# bind callback function
client.on_message=on_connect
client.on_message=on_message

client.username_pw_set(user, password)

if bVerbose :
    print("\n\nConnection in progress...", host)
client.connect(host,port)    

client.loop_start()     # start loop to process received messages

# Initialize VSCP event content
def initEvent(ex, id, vscpClass, vscpType):
    # Dumb node, priority normal
    ex.head = vscp.VSCP_PRIORITY_NORMAL | vscp.VSCP_HEADER16_DUMB
    g = vscp.guid()
    if ("" == guid):
        g.setFromString(guid)
    else :
        g.setGUIDFromMAC(id)
    ex.guid = g.guid
    ex.vscpclass = vscpClass
    ex.vscptype = vscpType
    return g

# -----------------------------------------------------------------------------

# Send measurement event
#   line - One p1 line
#   type - VSCP measurement type 
#   unit - VSCP unit
#   id   - Configured id for event
#   sensorindex - Configured sensor index for event
#   note - Note to send with event
#   zone - zone for event
#   subzone - subzone for event
def sendMeasurementEvent(line, type, unit=0, id=0, sensorindex=0, note="", zone=0, subzone=0):

    if bVerbose :
        print("Sending...", note)

    if bDebug :
        print("[" + line + "] " + line[11:-5] + " " + line[-4])

    posUnit = line.find('*')    # Find unit separator
    strvalue = line[11:posUnit-len(line)]

    if bDebug :
        print("Value: ", "[" + strvalue + "]", "unit:", line[posUnit+1:])

    ex = vscp.vscpEventEx()
    g = initEvent(ex, id, vc.VSCP_CLASS2_MEASUREMENT_STR, type)

    # Size is predata + string length + terminating zero
    ex.sizedata = 4 + len(strvalue) + 1
    ex.data[0] = sensorindex
    ex.data[1] = zone
    ex.data[2] = subzone
    ex.data[3] = unit
    b = strvalue.encode()
    for idx in range(len(b)):
        ex.data[idx + 4] = b[idx]
        ex.data[4 + len(strvalue)] = 0  # optional terminating zero

    j = ex.toJSON()
    j["vscpNote"] = note
    # Add extra measurement information
    j["measurement"] = { 
        "value" : float(strvalue),
        "unit" : 1,
        "sensorindex" : sensorindex,
        "zone" : zone,
        "subzone" : subzone
    }

    ptopic = topic.format( xguid=g.getAsString(), xclass=ex.vscpclass, xtype=ex.vscptype)
    if ( len(ptopic) ):
        client.publish(ptopic, json.dumps(j))

# -----------------------------------------------------------------------------

# Connect to serial device
sio = serial.Serial(
    port='/dev/ttyUSB1',\
    baudrate=115200,\
    parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    bytesize=serial.EIGHTBITS,\
    timeout=12)

if bVerbose :
    print("connected to: " + sio.portstr)

while True:

    # Read one line of data
    line = sio.readline().decode('ascii')    

    # -----------------------------------------------------------------------------
    #                             Active energy out
    # -----------------------------------------------------------------------------

    if (-1 != line.find("0-0:1.0.0")):
        # Date and time
        print(line)
    elif (-1 != line.find("1-0:1.8.0")):
        # Meter reading active energy out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ENERGY, 
                                1, # kWh
                                id_sum_active_energy_out, 
                                sensorindex_sum_active_energy_out, 
                                note_sum_active_energy_out, 
                                zone, 
                                subzone)
    elif(-1 != line.find("1-0:2.8.0")):
        # Meter reading active energy in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ENERGY, 
                                1, # kWh
                                id_sum_active_energy_in, 
                                sensorindex_sum_active_energy_in, 
                                note_sum_active_energy_in, 
                                zone, 
                                subzone)
    elif(-1 != line.find("1-0:3.8.0")):
        # Meter reading reactive energy out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ENERGY, # VSCP_TYPE_MEASUREMENT_REACTIVE_ENERGY,
                                0, # kVArh
                                id_sum_reactive_energy_out, 
                                sensorindex_sum_reactive_energy_out, 
                                note_sum_reactive_energy_out, 
                                zone, 
                                subzone)                            
    elif(-1 != line.find("1-0:4.8.0")):
        # Meter reading reactive energy in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kVArh
                                id_sum_reactive_energy_in, 
                                sensorindex_sum_reactive_energy_in, 
                                note_sum_reactive_energy_in, 
                                zone, 
                                subzone)
    elif(-1 != line.find("1-0:1.7.0")):
        # Active effect out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kVAr
                                id_momentan_active_effect_out, 
                                sensorindex_momentan_active_effect_out, 
                                note_momentan_active_effect_out, 
                                zone, 
                                subzone)                                 
    elif(-1 != line.find("1-0:2.7.0")):
        # Active effect in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_REACTIVE_POWER,
                                0, # kVAr
                                id_momentan_active_effect_out, 
                                sensorindex_momentan_active_effect_out, 
                                note_momentan_active_effect_out, 
                                zone, 
                                subzone)                                 
    elif(-1 != line.find("1-0:3.7.0")):
        # Reactive effect out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_REACTIVE_POWER,
                                0, # kVAr
                                id_momentan_reactive_effect_out, 
                                sensorindex_momentan_reactive_effect_out, 
                                note_momentan_reactive_effect_out, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:4.7.0")):
        # Reactive effect in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_REACTIVE_POWER,
                                0, # kVAr
                                id_momentan_reactive_effect_in, 
                                sensorindex_momentan_reactive_effect_in, 
                                note_momentan_reactive_effect_in, 
                                zone, 
                                subzone) 

    elif(-1 != line.find("1-0:21.7.0")):
        # Active effect L1 out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_active_effect_l1_out, 
                                sensorindex_momentan_active_effect_l1_out,
                                note_momentan_active_effect_l1_out, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:22.7.0")):
        # Active effect L1 in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_active_effect_l1_in, 
                                sensorindex_momentan_active_effect_l1_in, 
                                note_momentan_active_effect_l1_in, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:41.7.0")):
        # Active effect L2 out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_active_effect_l2_out, 
                                sensorindex_momentan_active_effect_l2_out,
                                note_momentan_active_effect_l2_out, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:42.7.0")):
        # Active effect L2 in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_active_effect_l2_in,
                                sensorindex_momentan_active_effect_l2_in, 
                                note_momentan_active_effect_l2_in, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:61.7.0")):
        # Active effect L3 out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_active_effect_l3_out, 
                                sensorindex_momentan_active_effect_l3_out,
                                note_momentan_active_effect_l3_out, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:62.7.0")):
        # Active effect L3 in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_active_effect_l3_in,
                                sensorindex_momentan_active_effect_l3_in, 
                                note_momentan_active_effect_l3_in, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:23.7.0")):
        # Recative effect L1 out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_reactive_effect_l1_out, 
                                sensorindex_momentan_reactive_effect_l1_out,
                                note_momentan_reactive_effect_l1_out, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:24.7.0")):
        # Recative effect L1 in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_reactive_effect_l1_in, 
                                sensorindex_momentan_reactive_effect_l1_in, 
                                note_momentan_reactive_effect_l1_in, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:43.7.0")):
        # Recative effect L2 out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_reactive_effect_l2_out, 
                                sensorindex_momentan_reactive_effect_l2_out,
                                note_momentan_reactive_effect_l2_out, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:44.7.0")):
        # Recative effect L2 in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_reactive_effect_l2_in, 
                                sensorindex_momentan_reactive_effect_l2_in, 
                                note_momentan_reactive_effect_l2_in, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:63.7.0")):
        # Recative effect L3 out
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_reactive_effect_l3_out, 
                                sensorindex_momentan_reactive_effect_l3_out,
                                note_momentan_reactive_effect_l3_out, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:64.7.0")):
        # Recative effect L3 in
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_POWER,
                                0, # kW
                                id_momentan_reactive_effect_l3_in, 
                                sensorindex_momentan_reactive_effect_l3_in, 
                                note_momentan_reactive_effect_l3_in, 
                                zone, 
                                subzone) 

    elif(-1 != line.find("1-0:32.7.0")):
        # Voltage for phase L1
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ELECTRICAL_POTENTIAL,
                                0, # V
                                id_voltage_l1, 
                                sensorindex_voltage_l1, 
                                note_voltage_l1, 
                                zone, 
                                subzone) 

    elif(-1 != line.find("1-0:52.7.0")):
        # Voltage for phase L2
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ELECTRICAL_POTENTIAL,
                                0, # V
                                id_voltage_l2, 
                                sensorindex_voltage_l2, 
                                note_voltage_l2, 
                                zone, 
                                subzone) 

    elif(-1 != line.find("1-0:72.7.0")):
        # Voltage for phase L3
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ELECTRICAL_POTENTIAL,
                                0, # V
                                id_voltage_l3, 
                                sensorindex_voltage_l3, 
                                note_voltage_l3, 
                                zone, 
                                subzone)   

    elif(-1 != line.find("1-0:31.7.0")):
        # Current for phase L1
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ELECTRIC_CURRENT,
                                0, # A
                                id_current_l1, 
                                sensorindex_current_l1, 
                                note_current_l1, 
                                zone, 
                                subzone)

    elif(-1 != line.find("1-0:51.7.0")):
        # Current for phase L2
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ELECTRIC_CURRENT,
                                0, # A
                                id_current_l2, 
                                sensorindex_current_l2, 
                                note_current_l2, 
                                zone, 
                                subzone) 

    elif(-1 != line.find("1-0:71.7.0")):
        # Current for phase L3
        sendMeasurementEvent(line, 
                                vt.VSCP_TYPE_MEASUREMENT_ELECTRIC_CURRENT,
                                0, # A
                                id_current_l3, 
                                sensorindex_current_l3, 
                                note_current_l3, 
                                zone, 
                                subzone)                                 
# -----------------------------------------------------------------------------

# Close the serial port
sio.close();

client.disconnect() 
client.loop_stop() 

if bVerbose :
    print("-------------------------------------------------------------------------------")
    print("Closed")

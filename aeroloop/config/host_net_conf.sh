#!/bin/bash

brctl stp ns-edge1 off
brctl stp ns-uav1 off

ifconfig  ns-edge1 up 
ifconfig ns-uav1 up 

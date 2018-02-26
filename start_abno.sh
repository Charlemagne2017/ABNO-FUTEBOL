#!/bin/bash

cd logs
rm *out
cd ../ABNOOrchestrator
nohup python ABNOMain.py ABNOArch > ../logs/ABNO.out &
cd ../TopologyModule
nohup python TMMain.py ABNOArch > ../logs/TM.out &
cd ../ProvisioningManager
nohup python PMMain.py ABNOArch > ../logs/PM.out &
cd ../PCE
nohup python PCEMain.py ABNOArch > ../logs/PCE.out &
cd ../OAMHandler
#nohup python OAMMain.py ABNOArch > ../logs/OAM.out &
cd ../MonitoringToolAllODL
nohup python Main.py ABNOArch > ../logs/Monitor.out &
cd ..

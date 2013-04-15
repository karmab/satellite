satellite
=========

satellite.py script to interact with a satellite5.X/spacewalk server
can list machines,software and configuration channels,schedules file deployment and command execution, view last command executed, retrieves and uploads configuration files,...
needs a .satelliterc (will possibly be changed to satellite.ini or something like that in the future) to define credentials (and also custominfo that you want to be retrieved when running satellite.py -m)

Examples
#clone a AK
satellite.py --clonekey --activationkey 1-base-6.4 prout
satellite.py --clonekey -8 6_4 -9 6_3 --activationkey 1-base-6_4 base-6_3

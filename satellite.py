#!/usr/bin/python

#
#  Copyright Red Hat, Inc. 2002-2004, 2012
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 2, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; see the file COPYING.  If not, write to the
#  Free Software Foundation, Inc.,  675 Mass Ave, Cambridge,
#  MA 02139, USA.

"""
interacts with satellite api
(based on http://spacewalk.redhat.com/documentation/api/1.8 )
"""

import bz2
import ConfigParser
import xmlrpclib
import optparse
import os
import sys 
import time,datetime

__author__ = "Karim Boumedhel"
__credits__ = ["Karim Boumedhel","Pablo Iranzo"]
__license__ = "GPL"
__version__ = "2.2"
__maintainer__ = "Karim Boumedhel"
__email__ = "karimboumedhel@gmail.com"
__status__ = "Production"

#-1-handle arguments
usage="satellite.py [OPTION] [ARGS]"
version="2.2"
parser = optparse.OptionParser(usage=usage,version=version)

executegroup = optparse.OptionGroup(parser, "Execute options")
executegroup.add_option("-e", "--execute",dest="execute", type="string", help="Execute given command")
executegroup.add_option("-f", "--deploy",dest="deploy", type="string", help="Deploy specified file")
executegroup.add_option("-H", "--history",dest="history", type="string", help="Retrieve last command run on the machine")
parser.add_option_group(executegroup)

channelgroup = optparse.OptionGroup(parser, "Channel options")
channelgroup.add_option("-b", "--basechannel",dest="basechannel", type="string", help="Set basechannel for specified machine")
channelgroup.add_option("-P", "--parentchannel", dest="parentchannel", type="string", help="When cloning, use this parent channel")
channelgroup.add_option("-w", "--clonechannel", action="store_true", dest="clonechannel", help="Clone software channel")
channelgroup.add_option("-x", "--children", action="store_true", dest="children", help="Handle children when cloning,deleting software channels or listing a machine")
channelgroup.add_option("-E", "--checkerratas", action="store_true", dest="checkerratas", help="Check erratas within software channel after cloning, to remove rpms from other releases")
channelgroup.add_option("-I", "--channelsummary", dest="destchannelname", type="string", help="When cloning, channel name and summary.will default to channel label if not present")
channelgroup.add_option("-S", "--softwarechannel", dest="softwarechannel", type="string", help="Use this software channel")
channelgroup.add_option("-4", "--channelname", dest="channelname", type="string", help="Change channel name(not label)")
channelgroup.add_option("-5", "--channelnameclean", action="store_true", dest="channelnameclean", help="Clean channel names for channel and all its children,removing trailing x possibly set when cloning channel")
channelgroup.add_option("--removenewer", dest="removenewer", type="string", help="Delete packages with newer dates than the one provided as argument(using YYYY-MM-DD ) for channel provided with -S. Usefull to be sure than child channels for a given minor release created cloning from red hat channels dont have newer packages")
parser.add_option_group(channelgroup)

configgroup = optparse.OptionGroup(parser, "Configuration options")
configgroup.add_option("-C", "--configchannel", dest="configchannel", type="string", help="Use this config channel")
configgroup.add_option("-r", "--revision", dest="revision", type="int", default=0, help="When showing contents with -s , get specific revision")
configgroup.add_option("-s", "--showcontents", action="store_true", dest="showcontents",help="When getting file with -z, show contents")
configgroup.add_option("-t", "--getfile",  action="store_true", dest="getfile", help="Get config file")
configgroup.add_option("-U", "--uploadfile", action="store_true", dest="uploadfile", help="Upload text config file to specified channel and path, which need to be passed as arguments")
configgroup.add_option("-Y", "--yes", action="store_true", dest="yes", help="Create file when uploading config file to specified channel and path, if they dont exist")
configgroup.add_option("-Z", "--createfile", action="store_true", dest="createfile", help="Create file when uploading config file. Channel and path will be retrieved from the line with NOTE within the orifile passed as argument")
parser.add_option_group(configgroup)

listinggroup = optparse.OptionGroup(parser, "Listing options")
listinggroup.add_option("-g", "--groups", action="store_true", dest="groups", help="List System Groups")
listinggroup.add_option("-l", "--clients", action="store_true", dest="clients", help="List Available clients")
listinggroup.add_option("-m", "--machines", action="store_true", dest="machines", help="List Machines or move them to destination channel upon cloning")
listinggroup.add_option("-p", "--package", type="string", dest="package", help="List all channels where indicated package can be found")
listinggroup.add_option("-k", "--profiles", action="store_true", dest="profiles", help="List Profiles")
listinggroup.add_option("-K", "--extendedprofiles", action="store_true", dest="extendedprofiles", help="List Profiles,along with their scripts")
listinggroup.add_option("-A", "--activationkeys", action="store_true", dest="activationkeys", help="List activation keys")
listinggroup.add_option("-F", "--configs", action="store_true", dest="configs", help="List config channels")
listinggroup.add_option("-G", "--extendedconfigs", action="store_true", dest="extendedconfigs", help="List config channels,and systems subscribed to them")
listinggroup.add_option("-L", "--channels", action="store_true", dest="channels", help="List software channels")
listinggroup.add_option("-T", "--tasks", action="store_true",dest="tasks", help="List tasks")
listinggroup.add_option("-u", "--users", action="store_true", dest="users", help="List Users")
parser.add_option_group(listinggroup)

connectiongroup = optparse.OptionGroup(parser, "Connection options")
connectiongroup.add_option("-c", "--client",dest="client", type="string", help="Specify Client")
connectiongroup.add_option("-1", "--sathost", dest="sathost", type="string", help="Satellite Host, if not defined in conf file")
connectiongroup.add_option("-2", "--satuser", dest="satuser", type="string", help="Satellite User, if not defined in conf file")
connectiongroup.add_option("-3", "--satpassword", dest="satpassword", type="string", help="Satellite Password, if not defined in conf file. Note a path can also be specified in conjunction with passwordfile=True in the ini file, to use a bz2-encrypted file containing password")
parser.add_option_group(connectiongroup)

deletegroup = optparse.OptionGroup(parser, "Delete options")
deletegroup.add_option("-d", "--deletechannel", action="store_true", dest="deletechannel", help="Delete software channel")
deletegroup.add_option("-R", "--removechildchannel", dest="removechildchannel", type="string", help="Child channel to remove from machine")
deletegroup.add_option("-X", "--delete", action="store_true", dest="deletesystem", help="Delete specified system. A confirmation will be asked")
deletegroup.add_option("-D", "--duplicatescripts", action="store_true", dest="duplicatescripts", help="Duplicate scripts from this profile")
deletegroup.add_option("-6", "--deleteak", action="store_true", dest="deleteak", help="Delete activation key")
deletegroup.add_option("-7", "--deleteprofile", action="store_true", dest="deleteprofile", help="Delete profile")
parser.add_option_group(deletegroup)

miscellaneousgroup = optparse.OptionGroup(parser, "Miscellaneous options")
miscellaneousgroup.add_option("--cloneak", action="store_true", dest="cloneak", help="Clone activation key")
miscellaneousgroup.add_option("-a", "--ak", type="string", dest="ak", help="Activation Key to use")
miscellaneousgroup.add_option("-8", "--filterori", type="string", dest="filterori", help="Reemplacement of this string in all information related to the original activation key when cloning. Allows customizing the destination key when you have a homogeneous channel structure")
miscellaneousgroup.add_option("-9", "--filterdest", type="string", dest="filterdest", help="The reemplacement  string in all information related to the original activation key when cloning. Allows customizing the destination key when you have a homogeneous channel structure")
miscellaneousgroup.add_option("--cloneprofile", action="store_true", dest="cloneprofile", help="Clone profile")
miscellaneousgroup.add_option("--advancedoption", type="choice", dest="advancedoption", choices = ["reboot", "poweroff", "skipx", "text", "zerombr" ], help="set advanced option for given profile. can be reboot,poweroff,skipx,text,zerombr")
miscellaneousgroup.add_option("--profile", type="string", dest="profile", help="Use this profile")
parser.add_option_group(miscellaneousgroup)

(options, args)=parser.parse_args()
basechannel=options.basechannel
client=options.client
clients=options.clients
machines=options.machines
groups=options.groups
profiles=options.profiles
extendedprofiles=options.extendedprofiles
users=options.users
channels=options.channels
activationkeys=options.activationkeys
softwarechannel=options.softwarechannel
parentchannel=options.parentchannel
configchannel=options.configchannel
deletechannel=options.deletechannel
clonechannel=options.clonechannel
children=options.children
removechildchannel=options.removechildchannel
destchannelname=options.destchannelname
configs=options.configs
extendedconfigs=options.extendedconfigs
getfile=options.getfile
showcontents=options.showcontents
revision=options.revision
uploadfile=options.uploadfile
createfile=options.createfile
yes=options.yes
custominfo=None
checkerratas=options.checkerratas
sathost=options.sathost
satuser=options.satuser
satpassword=options.satpassword
satpasswordfile=False
satellites=None
duplicatescripts=options.duplicatescripts
tasks=options.tasks
deletesystem=options.deletesystem
execute=options.execute
channelname=options.channelname
channelnameclean=options.channelnameclean
deploy=options.deploy
history=options.history
mac=True
ak=options.ak
cloneak=options.cloneak
deleteak=options.deleteak
deleteprofile=options.deleteprofile
filterori=options.filterori
filterdest=options.filterdest
cloneprofile=options.cloneprofile
advancedoption=options.advancedoption
profile=options.profile
package=options.package
removenewer=options.removenewer

def checksoftwarechannel(sat,key,softwarechannel):
 allsoftwarechannels = sat.channel.listAllChannels(key)
 for chan in allsoftwarechannels:
  if chan["label"]==softwarechannel:return True
 print "Channel %s not found" % softwarechannel
 sys.exit(1)


def checkak(sat,key,ak):
 allaks = sat.activationkey.listActivationKeys(key) 
 for key in allaks:
  if key["key"]==ak:return True
 print "Activation Key %s not found" % ak
 sys.exit(1)



def checkprofile(sat,key,profile):
 kickstarts=sat.kickstart.listKickstarts(key)
 found=False
 for k in kickstarts:
  if k["name"]==profile:
   treelabel=k["tree_label"]
   active=k["active"]
   found=True
   advanced_mode=k["advanced_mode"]
   break
 if not found:
  print "Profile %s not found" % (profile)
  sys.exit(0)
 return treelabel,active,advanced_mode

def getscripts(sat,key,name,advanced_mode):
 if not advanced_mode:
  scripts=sat.kickstart.profile.listScripts(key,name)
  for script in scripts:
   if script != []:
    template=""
    if script.has_key("template"):template=script["template"]
    print "Template:%s;Chroot:%s;Type:%s;Interpreter:%s" % (template,script["chroot"],script["script_type"],script["interpreter"])
    print "%s\n" % (script["contents"])

def copyprofile(sat,key,oriprofile,destprofile):
  oriscripts=sat.kickstart.profile.listScripts(key,oriprofile)
  #for script in destscripts:
  # sat.kickstart.profile.removeScript(key,destprofile,script["id"])
  addscripts={}
  print oriscripts
  for script in oriscripts:
    addscripts[script["id"]]=[script["contents"],script["interpreter"],script["script_type"],script["chroot"],script["template"]]
  for scriptid in sorted(addscripts,reverse=True):
    contents,interpreter,script_type,chroot,template=addscripts[scriptid][0],addscripts[scriptid][1],addscripts[scriptid][2],addscripts[scriptid][3],addscripts[scriptid][4]
    sat.kickstart.profile.addScript(key,destprofile,contents,interpreter,script_type,chroot,template)
    time.sleep(5)
  print "Scripts copied from %s to %s" % (oriprofile,destprofile)
 

def gettasks(sat,key):
 now=datetime.datetime.now().strftime("%Y%m%d")
 progresstasks=sat.schedule.listInProgressActions(key)
 completedtasks=sat.schedule.listCompletedActions(key)
 failedtasks=sat.schedule.listFailedActions(key)
 tasktypes=["completed","progress","failed"]
 tasktypecount=0
 for tasks in completedtasks,progresstasks,failedtasks:
   tasktype=tasktypes[tasktypecount]
   tasktypecount=tasktypecount+1
   for t in tasks:
    taskdate=str(t["earliest"]).split("T")[0]
    if taskdate==now:print "%s;%s;completed %s; progress %s; failed %s;date %s" % (tasktype,t["name"],t["completedSystems"],t["inProgressSystems"],t["failedSystems"],taskdate)
    id=t["id"]
    #progresssystems=sat.schedule.listInProgressSystems(key,id)
    completedsystems=sat.schedule.listCompletedSystems(key,id)
    #failedsystems=sat.schedule.listFailedSystems(key,id)
    print completedsystems
    sys.exit(0)

def delsystem(sat,key,name):
 id=[]
 for machine in sat.system.listSystems(key):
  if machine["name"]==name:
   id.append(int(machine["id"]))
 if len(id) ==0:
  print "Machine %s not found" % (name)
  sys.exit(1)
 elif len(id) >1:
  print "Several profiles found for Machine %s" % (name)
 confirmation=raw_input("Confirm you want to delete profile of %s(Y|N):" % name)
 if confirmation =="Y":
  sat.system.deleteSystems(key,id)
  print "Machine deleted"
 else:
  print "Not doing anything"
  sys.exit(1)

def getinfo(sat,key,machine,machines,ids,custominfo,groups=False,children=children,softwarechannel=None):
 #machine=args[0]
 ids=ids[machine]
 for id in ids:
  ips=[]
  if groups:
   groups=[]
   for gr in sat.system.listGroups(key,id):
    if gr["subscribed"]==1:groups.append(gr["system_group_name"])
  customvalues=sat.system.getCustomValues(key,id)
  network=sat.system.getNetworkDevices(key,id)
  dmi=sat.system.getDmi(key,id)
  channel=sat.system.getSubscribedBaseChannel(key,id)["label"]
  if softwarechannel and channel!=softwarechannel:return
  checked=str(sat.system.getId(key,machine)[0]["last_checkin"]).split("T")[0]
  if not dmi:
   product=""
  else:
   product=dmi["product"]
  for net in network:
   if net.has_key("ip") and net["ip"] !="127.0.0.1" and net["ip"] !="":
    ips.append(net["ip"])
    if mac:ips.append(net['hardware_address'])
  machines[machine]=[product,channel,checked,";".join(ips)]
  if custominfo:
   for cus in custominfo:
    if customvalues.has_key(cus):
     machines[machine].append(customvalues[cus])
  info=machines[machine]
  print "%s;%s;%s;%s;%s;%s" % (machine,info[0],info[1],info[2],info[3],";".join(info[4:]))
  #if groups:print "GROUPS: %s" % (" ".join(groups))
  if children:
   childreninfo=sat.system.listSubscribedChildChannels(key,id)
   childchannels=[]
   for child in childreninfo:childchannels.append(child["label"])
   print ";".join(childchannels)

if clients or not sathost or not satuser or not satpassword:
 satelliterc="%s/satellite.ini" % (os.environ['HOME'])
 if not os.path.exists(satelliterc):
  print "Missing %s in your home directory or in current directory.Check documentation" % satelliterc
  sys.exit(1)
 try:
  c = ConfigParser.ConfigParser()
  c.read(satelliterc)
  defaults={}
  satellites={}
  for cli in c.sections():
   for option in c.options(cli):
    if cli=="default":
     defaults[option]=c.get(cli,option)
     continue
    if not satellites.has_key(cli):
     satellites[cli]={option : c.get(cli,option)}
    else:
     satellites[cli][option]=c.get(cli,option)
  if not client and defaults.has_key("client"):client=defaults["client"]
 except KeyError, e:
  print "Missing Key %s" % e
  os._exit(1)


if clients:
 for cli in sorted(satellites.keys()):print cli
 sys.exit(0)

if sathost and satuser and satpassword:
 client="XXX"

if not client:
 print "Select Client within this list:"
 for cli in sorted(satellites.keys()):print cli
 client=raw_input("Enter Client: ")
 if client != "XXX" and client not in satellites.keys():
  print "Client not found"
  sys.exit(1)


if not sathost and not satuser and not satpassword:
 try:
  if not sathost:sathost=satellites[client]["host"]
  if not satuser:satuser=satellites[client]["user"]
  if not satpassword:satpassword=satellites[client]["password"]
  if satellites and satellites[client].has_key("passwordfile") and satellites[client]["passwordfile"]:satpasswordfile=satpassword
  if satellites and satellites[client].has_key("custominfo"):custominfo=satellites[client]["custominfo"].split(";")
 except KeyError,e:
  print "Missing key %s" % e
  os._exit(1)
saturl="http://%s/rpc/api" % sathost

sat=xmlrpclib.Server(saturl, verbose=0)
#if satpasswordfile equals satpassword, use satpassword as a path to the encrypted password
if satpasswordfile == satpassword:
 try:
  satpasswordfile = open(satpasswordfile, "r")
  satpassword = bz2.decompress(satpasswordfile.read())
  satpasswordfile.close()
 except IOError:
  print "file containing crypted password file couldnt be opened"
  os._exit(1)
 
key=sat.auth.login(satuser, satpassword)
if users:
 users = sat.user.list_users(key)
 for user in users:print user.get('login')
 sys.exit(0)

if groups:
 allgroups = sat.systemgroup.listAllGroups(key)
 groups={}
 for g in allgroups:groups[g["name"]]=[g["id"],g["description"],g["system_count"]]
 for group in sorted(groups): print "%s;%s;%s;%s" % (group,groups[group][0],groups[group][1],groups[group][2])
 sys.exit(0)


if activationkeys:
 for k in sat.activationkey.listActivationKeys(key):
  print "%s;%s;%s" % (k["key"],k["description"],k["base_channel_label"])
  #print k
 sys.exit()

if machines and not clonechannel:
 results=[]
 ids={}
 machines={}
 for machine in sat.system.listSystems(key):
  if not ids.has_key(machine["name"]): 
   ids[machine["name"]]=[int(machine["id"])]
  else:
   ids[machine["name"]].append(int(machine["id"]))
 if len(args)== 1:
  if args[0] not in ids.keys():
   print "Machine %s not found" % args[0]
   sys.exit(1)
  else:
   machine=args[0]
   getinfo(sat,key,machine,machines,ids,custominfo,groups=True,children=children,softwarechannel=softwarechannel)
   sys.exit(0)
 for machine in sorted(ids.keys()):getinfo(sat,key,machine,machines,ids,custominfo,children=children,softwarechannel=softwarechannel)
 sys.exit(0)

if channels:
 if len(args)==1:softwarechannel=args[0]
 channels={}
 for chan in sorted(sat.channel.listAllChannels(key)):
  channels[chan["label"]]=[chan["name"],chan["packages"],chan["systems"],chan["id"]]
 print "LABEL;NAME;PACKAGES;SYSTEMS"
 if softwarechannel:
  if channels.has_key(softwarechannel):
   print "%s;%s;%s;%s" % (softwarechannel,channels[softwarechannel][0],channels[softwarechannel][1],channels[softwarechannel][2])
   if children:
     childchannels=[]
     childreninfo=sat.channel.software.listChildren(key,softwarechannel)
     if len(childreninfo) >=1:
      print "CHILDCHANNELS:"
      for child in sorted(childreninfo):
       childlabel=child["label"]
       childname=child["name"]
       numsystems=sat.channel.software.listSubscribedSystems(key,childlabel)
       numpackages=sat.channel.software.listAllPackages(key,childlabel)
       print "%s;%s;%s;%d" % (childlabel,childname,len(numpackages),len(numsystems))
   sys.exit(0)
  else:
   print "Channel not found"
   sys.exit(1)
 for chan in sorted(channels.keys()):
  print "%s;%s;%s;%s" % (chan,channels[chan][0],channels[chan][1],channels[chan][2])
  if children:
    childchannels=[]
    childreninfo=sat.channel.software.listChildren(key,chan)
    if len(childreninfo) >=1:
     for child in childreninfo:childchannels.append(child["label"])
     print "CHILDCHANNELS:"+";".join(childchannels)
 sys.exit(0)

if configs or extendedconfigs:
 if configchannel:
  confs=sat.configchannel.listFiles(key,configchannel)
  for f in confs:print f["path"]
  sys.exit(0)
 for conf in sorted(sat.configchannel.listGlobals(key)):
  print conf["label"]
  machines=[]
  if extendedconfigs:
   for el in sorted(sat.configchannel.listSubscribedSystems(key,conf["label"])): machines.append(el["name"])
   print ";".join(machines)

if getfile or showcontents:
 if len(args)!=1:
  print "Usage:%s -z configfile" % (sys.argv[0])
  sys.exit(1)
 else:
  getfile=args[0]
 confs=sat.configchannel.listGlobals(key)
 for conf in confs:
  conffiles=sat.configchannel.listFiles(key,conf["label"])
  for conffile in conffiles:
   if getfile in conffile["path"] and conffile["type"] =="file":
    label,path=conf["label"],conffile["path"]
    if showcontents:
     revisions=sat.configchannel.getFileRevisions(key,label,path)
     if revision ==0:
      for rev in  revisions:
       if rev["revision"] >= revision:revision=rev["revision"]
     content=sat.configchannel.getFileRevision(key,conf["label"],conffile["path"],revision)
     print label,path,revision
     print content["contents"]
    else:
     print label,path


if createfile:
 if len(args)!=1:
  print "Usage:%s -Z configfile" % (sys.argv[0])
  sys.exit(1)
 else:
  orifile=args[0]
 #TEST ORIFILE EXISTS
 if not os.path.exists(orifile):
  print "Input file doesnt exist"
  sys.exit(1)
 #GRAB filepath and configchannel from fileheader
 filecontent=open(orifile).readlines()
 headerfound=False
 for line in filecontent:
  if "NOTE" in line and "automatically" in line and "generated" in line:
   headerfound=True
   configchannel,configfile,configfileowner,configfilegroup,configfilepermissions=line.split(" ")[-5],line.split(" ")[-4],line.split(" ")[-3],line.split(" ")[-2],line.split(" ")[-1].replace("\n","")
   break
 if not headerfound:
  print "Headers not found.File cant be created"
  print "You need a line with the following content"
  print "# NOTE: This file is automatically generated by satellite configchannel filepath owner group permissions"
  sys.exit(1)
 #TEST SPECIFIED CHANNEL EXISTS
 channelexists=sat.configchannel.channelExists(key,configchannel)
 if channelexists == 0:
  print "Channel doesnt exist"
  sys.exit(0)
 #pathinfo={"owner":"root","group":"root","permissions":"755"}
 pathinfo={"owner":configfileowner,"group":configfilegroup,"permissions":configfilepermissions}
 #AT THIS POINT, WE ARE READY TO UPLOAD NEW REVISION
 pathinfo["contents"]=open(orifile).read()
 updatefile=sat.configchannel.createOrUpdatePath(key,configchannel,configfile,False,pathinfo)
 print "Created revision %s for file %s" % (updatefile["revision"],configfile)
 sys.exit(0)
  
if uploadfile:
 if len(args)!=2 or not configchannel:
  print "Usage:%s -U -C channelname configfile orifile" % (sys.argv[0])
  sys.exit(1)
 else:
  configfile=args[0]
  orifile=args[1]
 #TEST ORIFILE EXISTS
 if not os.path.exists(orifile):
  print "Input file doesnt exist"
  sys.exit(1)
 #TEST SPECIFIED CHANNEL EXISTS
 channelexists=sat.configchannel.channelExists(key,configchannel)
 if channelexists == 0:
  print "Channel doesnt exist"
  print "Usage:%s -U channelname configfile orifile" % (sys.argv[0])
  sys.exit(0)
 #TEST CONFIGFILE EXISTS WITHIN SPECIFIED CHANNEL
 filefound=False
 conffiles=sat.configchannel.listFiles(key,configchannel)
 for f in  conffiles: 
  if configfile==f["path"]:
   revisions=sat.configchannel.getFileRevisions(key,configchannel,configfile)
   revision ==0
   for rev in  revisions:
    if rev["revision"] >= revision:revision=rev["revision"]
   content=sat.configchannel.getFileRevision(key,configchannel,configfile,revision)
   pathinfo={"owner":content["owner"],"group":content["group"],"permissions":str(content["permissions"])}
   filefound=True 
   break
 if not filefound:
  if not yes:
   print "File not found within channel"
   sys.exit(1)
  else:
   pathinfo={"owner":"root","group":"root","permissions":"755"}
 #AT THIS POINT, WE ARE READY TO UPLOAD NEW REVISION
 pathinfo["contents"]=open(orifile).read()
 updatefile=sat.configchannel.createOrUpdatePath(key,configchannel,configfile,False,pathinfo)
 print "Created revision %s for file %s" % (updatefile["revision"],configfile)


if checkerratas: 
 if not softwarechannel:
  print "Software channel not indicated.Use -S"
  sys.exit(1)
 checksoftwarechannel(sat,key,softwarechannel)
 erratas=sat.channel.software.listErrata(key,softwarechannel)
 badpackages={}
 for err in erratas:
  errata=err["advisory_name"]
  packages=sat.errata.listPackages(key,errata)
  for package in packages:
   # FIND CRITERIA TO MARK PACKAGE AS BAD.MEANS SHOULD BE REMOVED FROM ERRATA LIST
   #if package["release"]
   badpackages[package["name"]]=[package["id"],package["release"]]
 for badp in badpackages:print badp

if duplicatescripts:
 if len(args) !=2:
  print "Usage: %s -D oriprofile destprofile" % (sys.argv[0]) 
  sys.exit(1)
 else:
  oriprofile=args[0]
  destprofile=args[1]
  checkprofile(sat,key,oriprofile)
  checkprofile(sat,key,destprofile)
  copyprofile(sat,key,oriprofile,destprofile)

if clonechannel: 
 childmapping={}
 basechannel=False
 setchannelname=False
 if not softwarechannel:
  softwarechannel=raw_input("Enter original channel:\n")
  if softwarechannel =="":
   print "Software channel cant be blank"
   sys.exit(1)
 checksoftwarechannel(sat,key,softwarechannel)
 childrenlist=[]
 if sat.channel.software.getDetails(key,softwarechannel)["parent_channel_label"]=="":basechannel=True
 for child in sat.channel.software.listChildren(key,softwarechannel):childrenlist.append(child["label"])
 if len(args)==1:
  destchannel=args[0]
 else:
  destchannel=raw_input("Enter Destination channel:\n")
 if destchannel =="" or len(destchannel) < 6:
   print "Destination channel cant be blank or less than 6 characters"
   sys.exit(1)
 if not destchannelname:
  destchannelname=destchannel
  setchannelname=True
  orichannelname=sat.channel.software.getDetails(key,softwarechannel)["name"]
 destchannelinfo={"name":destchannelname,"label":destchannel,"summary":destchannelname}
 if machines:
  systems={}
  systeminfo=sat.channel.software.listSubscribedSystems(key,softwarechannel)
  for item in systeminfo:
   systemid=item["id"]
   systems[systemid]=[] 
   name=sat.system.getName(key,systemid)["name"]
   print "Machine %s will be moved to new channels" % name
   for element in sat.system.listSubscribedChildChannels(key,systemid):systems[systemid].append(element["label"])
 if parentchannel:
  checksoftwarechannel(sat,key,parentchannel)
  destchannelinfo["parent_label"]=parentchannel
 else:
  softwarechanneldetails=sat.channel.software.getDetails(key,softwarechannel)
  if softwarechanneldetails["parent_channel_label"] !="":destchannelinfo["parent_label"]=softwarechanneldetails["parent_channel_label"]
 sat.channel.software.clone(key,softwarechannel,destchannelinfo,False)
 print "Channel %s successfully cloned to %s" % (softwarechannel,destchannel)
 if setchannelname:
  #change name afterwards
  channelinfo={}
  channelinfo["name"]="x"+sat.channel.software.getDetails(key,softwarechannel)["name"]
  destchannelid=sat.channel.software.getDetails(key,destchannel)["id"]
  sat.channel.software.setDetails(key,destchannelid,channelinfo)
 if children:
  for child in childrenlist:
   destchildchannel=raw_input("Enter Destination channel for %s\n" % child)
   if destchildchannel =="" or len(destchildchannel) < 6:
    print "Destination channel cant be blank or less than 6 characters"
    sys.exit(1) 
   destchildchannelname=sat.channel.software.getDetails(key,child)["name"]
   childmapping[child]=destchildchannel
   destchildchannelinfo={"name":destchildchannel,"label":destchildchannel,"summary":destchildchannel,"parent_label":destchannel}
   sat.channel.software.clone(key,child,destchildchannelinfo,False)
   print "Channel %s successfully cloned to %s" % (child,destchildchannel)
   #change name afterwards
   channelinfo={}
   channelinfo["name"]="x"+sat.channel.software.getDetails(key,child)["name"]
   destchildchannelid=sat.channel.software.getDetails(key,destchildchannel)["id"]
   sat.channel.software.setDetails(key,destchildchannelid,channelinfo)
 if machines:
  for systemid in systems:
   name=sat.system.getName(key,systemid)["name"]
   if basechannel:
    destchannelid=sat.channel.software.getDetails(key,destchannel)["id"]
    sat.system.setBaseChannel(key,systemid,destchannel)
    print "Channel %s set as basechannel for %s" % (destchannel,name)
    newchildren=[]
    for channel in systems[systemid]:newchildren.append(childmapping[channel])
    sat.system.setChildChannels(key,systemid,newchildren)
    print "Child channels changed for System %s" % (name)
   else:
    newchildren=[]
    for channel in systems[systemid]:
     if channel !=softwarechannel:newchildren.append(channel)
    newchildren.append(destchannel)
    #sat.system.setChildChannels(key,systemid,systems[systemid])
    sat.system.setChildChannels(key,systemid,newchildren)
    print "Child channels changed for System %s" % (name)
 sys.exit(0)
   
if deletechannel: 
 if len(args)==1:softwarechannel=args[0]
 if not softwarechannel:
  softwarechannel=raw_input("Enter original channel:\n")
  if softwarechannel =="":
   print "Software channel cant be blank"
   sys.exit(1)
 checksoftwarechannel(sat,key,softwarechannel)
 systems=sat.channel.software.listSubscribedSystems(key,softwarechannel)
 if len(systems) >=1:
  print "Note the following machines will be unsubscribed from this channel!!!:"
  for system in systems:print system["name"]
 confirmation=raw_input("Confirm you want to delete Destination channel %s(Y|N):\n" % softwarechannel)
 if confirmation !="Y":
   print "Leaving"
   sys.exit(1)
 childrenlist=[]
 for child in sat.channel.software.listChildren(key,softwarechannel):childrenlist.append(child["label"])
 if len(childrenlist) >= 1:
  for children in childrenlist:
   sat.channel.software.delete(key,children)
   print "Child Channel %s sucessfully deleted" % (children)
 result=sat.channel.software.delete(key,softwarechannel)
 if result==1:
  print "Channel %s successfully deleted" % (softwarechannel)
  sys.exit(0)

if profiles or extendedprofiles:
 if len(args)==1:
  profile=args[0]
  treelabel,active,advanced_mode=checkprofile(sat,key,profile)
  print "%s;Treelabel:%s;Active:%s;AdvancedMode:%s" % (profile,treelabel,active,advanced_mode)
  if not advanced_mode:
   scripts=sat.kickstart.profile.listScripts(key,profile)
   for script in scripts:
    if script != []:
     template=""
     if script.has_key("template"):template=script["template"]
     print "Template:%s;Chroot:%s;Type:%s;Interpreter:%s" % (template,script["chroot"],script["script_type"],script["interpreter"])
     print "%s\n" % (script["contents"])
  elif extendedprofiles:
   print sat.kickstart.profile.downloadRenderedKickstart(key,profile)
  sys.exit(0)
 for k in sorted(sat.kickstart.listKickstarts(key)):
  profile=k["name"]
  treelabel=k["tree_label"]
  active=k["active"]
  advanced_mode=k["advanced_mode"]
  print "%s;Treelabel:%s;Active:%s;AdvancedMode:%s" % (profile,treelabel,active,advanced_mode)
  if not extendedprofiles:continue
  if not advanced_mode:
   scripts=sat.kickstart.profile.listScripts(key,profile)
   for script in scripts:
    if script != []:
     template=""
     if script.has_key("template"):template=script["template"]
     print "Template:%s;Chroot:%s;Type:%s;Interpreter:%s" % (template,script["chroot"],script["script_type"],script["interpreter"])
     print "%s\n" % (script["contents"])
  else:
   print "N/A:Use %s -K %s to get all kickstart details" % (sys.argv[0],profile)
  
if tasks:
 gettasks(sat,key)

if deletesystem:
 if len(args)!=1:
  print "Usage:%s -X system_name" % (sys.argv[0])
  sys.exit(1)
 else:
  system=args[0]
  delsystem(sat,key,system)
  
if execute:
 if len(args)!=1:
  print "Usage:%s -e commands system_list" % (sys.argv[0])
  sys.exit(1)
 ids={}
 idsexec=[]
 systemlist=args[0].split(",")
 machines={}
 for machine in sat.system.listSystems(key):ids[machine["name"]]=int(machine["id"])
 for system in systemlist:
  if system not in ids.keys():
   print "Machine %s not found" % system
  else:
   idsexec.append(ids[system])
 if len(idsexec) == 0:
   print "No Machine to launch commands...Aborting"
   sys.exit(0)
 else:
  #generate a date with the iso8601
  now=datetime.datetime.now()
  if not execute.startswith("#!/"):execute="#!/bin/sh\n%s" % execute
  sat.system.scheduleScriptRun(key,idsexec,"root","root",0,execute,now)
  print "Action scheduled for %s" % system
 sys.exit(0)


if history:
 ids={}
 systemfoundlist=[]
 systemlist=history.split(",")
 machines={}
 for machine in sat.system.listSystems(key):ids[machine["name"]]=int(machine["id"])
 for system in systemlist:
  if system not in ids.keys():
   print "Machine %s not found" % system
  else:
   systemfoundlist.append(system)
 if len(systemfoundlist) == 0:
   print "No Machine to retrieve history from...Aborting"
   sys.exit(0)
 else:
  for system in systemfoundlist:
   print "Info for %s:" % system
   event=sat.system.listSystemEvents(key,ids[system])[-1:][0]
   if event['action_type'] in ["Run an arbitrary script","Deploy config files to system scheduled by Administrador"]:
    if event.has_key("pickup_date"):print "DATE:%s %s" % (str(event["pickup_date"]).split("T")[0], str(event["pickup_date"]).split("T")[1])
    eventid=event['id']
    result=sat.system.getScriptActionDetails(key,eventid)
    content=result["content"]
    detailedresults=result["result"]
    output="N/A(Might need to wait)"
    if len(detailedresults)>=1:output=detailedresults[0]["output"]
    print "INPUT:\n%s" % content
    print "OUTPUT:\n%s" % output
   else:
    print event
  sys.exit(0)


if deploy:
 if len(args)!=1 or not configchannel:
  print "Usage:%s -C config_channel -f file_to_deploy system_list" % (sys.argv[0])
  sys.exit(1)
 ids={}
 idsexec=[]
 systemlist=args[0].split(",")
 #TEST config channel exists
 channelexists=sat.configchannel.channelExists(key,configchannel)
 if channelexists == 0:
  print "Channel doesnt exist"
  sys.exit(0)
 #TEST machines exist
 machines={}
 for machine in sat.system.listSystems(key):ids[machine["name"]]=int(machine["id"])
 for system in systemlist:
  if system not in ids.keys():
   print "Machine %s not found" % system
  else:
   idsexec.append(ids[system])
 if len(idsexec) == 0:
   print "No Machine to deploy file...Aborting"
   sys.exit(0)
 else: 
  #TEST configfile exists within the config channel
  filefound=False
  conffiles=sat.configchannel.listFiles(key,configchannel)
  for f in  conffiles:
   if deploy in f["path"]:
    #if we allready found a matching file within this directory, exits stating there are too man
    if filefound:
     print "Several files matching found within this configchannel, not doing anything...."
     print f["path"]
     sys.exit(1)
    else:
     filefound=True
     deploypath=f["path"]
  if not filefound:
   print "Config file not found within this config channel"
   sys.exit(1) 
  #at this point, we are ready to deploy
  #generate a date with the iso8601
  now=datetime.datetime.now()
  deploy="#!/bin/sh\nrhncfg-client get %s" % deploypath
  sat.system.scheduleScriptRun(key,idsexec,"root","root",0,deploy,now)
  print "Deployment of %s scheduled for %s" % (deploypath,system)
 sys.exit(0)

#subscribe given machine to indicated configchannel
if configchannel and len(args)==1:
 name=args[0]
 #TEST SPECIFIED CHANNEL EXISTS
 channelexists=sat.configchannel.channelExists(key,configchannel)
 if channelexists == 0:
  print "Channel %s doesnt exist..." % configchannel
  sys.exit(0)
 ids={}
 machines={}
 for machine in sat.system.listSystems(key):
  if not ids.has_key(machine["name"]): 
   ids[machine["name"]]=[int(machine["id"])]
  else:
   ids[machine["name"]].append(int(machine["id"]))
 if name not in ids.keys():
  print "Machine %s not found" % args[0]
  sys.exit(1)
 for id in ids[name]:
  configchannels=[]
  for chan in sat.system.config.listChannels(key,id):configchannels.append(chan["label"])
  if configchannel in configchannels:
   print "%s allready in Config Channel %s" % (name,configchannel)
  else: 
   configchannels.append(configchannel)
   sat.system.config.setChannels(key,[id],configchannels)
   print "%s added to Config Channel %s" % (name,configchannel)
 

#subscribe given machine to indicated basechannel
if basechannel and len(args)==1:
 name=args[0]
 #TEST SPECIFIED CHANNEL EXISTS
 checksoftwarechannel(sat,key,basechannel)
 systemid=sat.system.getId(key,name)
 if not systemid or len(systemid)>1:
  print "Machine %s not found or duplicated.Not doing anything" % (name)
  sys.exit(0)
 systemid=systemid[0]["id"]
 sat.system.setBaseChannel(key,systemid,basechannel)
 print "channel %s set as basechannel for %s" % (basechannel,name)
 if children:
  childrenselected=[]
  childreninfo=sat.channel.software.listChildren(key,basechannel)
  if len(childreninfo) >=1:
   for child in childreninfo:
    childname=child["label"]
    add=raw_input("Add %s as chilchannel for this machine(y/N):\n" % childname)
    if add=="Y":childrenselected.append(childname)
  if len(childrenselected) >=1:
    sat.system.setChildChannels(key,systemid,childrenselected)
    print "The following Child channels were added to %s:" % (name)
    for child in sorted(childrenselected):print child

#subscribe given machine to indicated childchannel
if softwarechannel and len(args)==1:
 name=args[0]
 #TEST SPECIFIED CHANNEL EXISTS
 checksoftwarechannel(sat,key,softwarechannel)
 systemid=sat.system.getId(key,name)
 if not systemid or len(systemid)>1:
  print "Machine %s not found or duplicated.Not doing anything" % (name)
  sys.exit(0)
 systemid=systemid[0]["id"]
 childreninfo=sat.system.listSubscribedChildChannels(key,systemid)
 childchannels=[]
 for child in childreninfo:
  label=child["label"]
  if label==softwarechannel:
   print "Machine allready subscribed to child channel %s.Not doing anything" % (softwarechannel)
   sys.exit(1)
  else:
   childchannels.append(child["label"])
 childchannels.append(softwarechannel)
 sat.system.setChildChannels(key,systemid,childchannels)
 print "Child channel %s added to %s" % (softwarechannel,name)


#remove  given childchannel of indicated machine
if removechildchannel and len(args)==1:
 name=args[0]
 #TEST SPECIFIED CHANNEL EXISTS
 checksoftwarechannel(sat,key,removechildchannel)
 systemid=sat.system.getId(key,name)
 if not systemid or len(systemid)>1:
  print "Machine %s not found or duplicated.Not doing anything" % (name)
  sys.exit(0)
 systemid=systemid[0]["id"]
 childreninfo=sat.system.listSubscribedChildChannels(key,systemid)
 childchannels=[]
 childfound=False
 for child in childreninfo:
  label=child["label"]
  if label==removechildchannel:
   childfound=True
   continue
  childchannels.append(child["label"])
 if not childfound:
  print "Machine allready subscribed to child channel %s.Not doing anything" % (removechildchannel)
  sys.exit(1)
 sat.system.setChildChannels(key,systemid,childchannels)

if softwarechannel and channelname:
 #TEST SPECIFIED CHANNEL EXISTS
 checksoftwarechannel(sat,key,softwarechannel)
 channelinfo={}
 channelinfo["name"]=channelname
 destchannelid=sat.channel.software.getDetails(key,softwarechannel)["id"]
 sat.channel.software.setDetails(key,destchannelid,channelinfo)
 print "Channel name changed for %s" % (softwarechannel)

if softwarechannel and channelnameclean:
 #TEST SPECIFIED CHANNEL EXISTS
 checksoftwarechannel(sat,key,softwarechannel)
 channelinfo=sat.channel.software.getDetails(key,softwarechannel)
 channelid=channelinfo["id"]
 channelname=channelinfo["name"]
 if channelname.startswith("x"):
  channelinfo={}
  channelinfo["name"]=channelname[1:]
  sat.channel.software.setDetails(key,channelid,channelinfo)
  print "Channel name changed for %s" % (softwarechannel)
 else:
  print "No need to change Channel for %s" % (softwarechannel)
 for child in sat.channel.software.listChildren(key,softwarechannel):
  childlabel=child["label"]
  childid=child["id"]
  childname=child["name"]
  if childname.startswith("x"):
   channelinfo={}
   channelinfo["name"]=childname[1:]
   sat.channel.software.setDetails(key,childid,channelinfo)
   print "Channel name changed for %s" % (childlabel)
   

if cloneak: 
 if len(args)==1:
  destak=args[0]
 else:
  print "Usage:satellite.py --cloneak --ak oriak destak"
  sys.exit(0)
 if not ak:
  ak=raw_input("Enter original activation key:\n")
  if ak =="":
   print "Activation Key cant be blank"
   sys.exit(1)
 checkak(sat,key,ak)
 oriak=sat.activationkey.getDetails(key,ak)
 oriconf=sat.activationkey.listConfigChannels(key,ak)
 confchannels=[]
 for conf in oriconf:confchannels.append(conf["label"])
 packages=oriak["packages"]
 description=oriak["description"]
 base_channel_label=oriak["base_channel_label"]
 child_channel_labels=oriak["child_channel_labels"]
 server_group_ids=oriak["server_group_ids"]
 entitlements=oriak["entitlements"]
 universal_default=oriak["universal_default"]
 usage_limit=oriak["usage_limit"]
 if filterori and filterdest:
  description=description.replace(filterori,filterdest)
  base_channel_label=base_channel_label.replace(filterori,filterdest) 
  child_channel_labels2,server_group_ids2=[],[]
  for child in child_channel_labels:child_channel_labels2.append(child.replace(filterori,filterdest))
  for gid in server_group_ids:
   gname=sat.systemgroup.getDetails(key,gid)["name"]
   gname2=gname.replace(filterori,filterdest)
   if gname2!=gname:
    newgid=sat.systemgroup.getDetails(key,gname2)["id"]
   else:
    newgid=gid    
   server_group_ids2.append(newgid)    
  child_channel_labels,server_group_ids=child_channel_labels2,server_group_ids2 
 destak=sat.activationkey.create(key,destak,description,base_channel_label,entitlements,universal_default)
 sat.activationkey.addPackages(key,destak,packages)
 sat.activationkey.addServerGroups(key,destak,server_group_ids)
 sat.activationkey.addChildChannels(key,destak,child_channel_labels)
 sat.activationkey.addConfigChannels(key,[destak],confchannels,True)
 print "Activation Key %s successfully cloned to %s" % (ak,destak)
 sys.exit(0)

if deleteak: 
 if len(args)==1:
  ak=args[0]
 else:
  print "Usage:satellite.py --deleteak ak"
  sys.exit(0)
 checkak(sat,key,ak)
 result=sat.activationkey.delete(key,ak)
 if result==1:
  print "Activation Key %s successfully deleted" % (ak)
 else:
  print "Problem deleting Activation Key %s" % (ak)
 sys.exit(0)

if advancedoption:
    if not profile and len(args)==1:
     profile=args[0]
    elif not profile:
     profile=raw_input("Enter original activation key:\n")
    if profile =="":
     print "Profile cant be blank"
     sys.exit(1)
    checkprofile(sat,key,profile)
    advancedoptions = sat.kickstart.profile.getAdvancedOptions(key,profile)
    newoptions = []
    for option in advancedoptions:
        if option["name"]==advancedoption:
            print "option allready set"
            sys.exit(0)
        elif advancedoption == "reboot" and option["name"]=="poweroff":
            continue
        elif advancedoption == "poweroff" and option["name"]=="reboot":
            continue
        else:
            newoptions.append(option)
    newoptions.append( {'name': advancedoption} ) 
    #result = sat.kickstart.profile.setAdvancedOptions(key,profile,[lang,keyboard,bootloader,auth,rootpw,timezone,url,advanced])
    result = sat.kickstart.profile.setAdvancedOptions(key,profile,newoptions)
    if result==1:
     print "Profile %s successfully set with %s option" % (profile, advancedoption)
    else:
     print "Problem"
    sys.exit(0)


if cloneprofile:
    if len(args)==1:
     destprofile=args[0]
    else:
     print "Usage:satellite.py --cloneprofile --profile oriprofile destprofile"
     sys.exit(0)
    if not profile:
     profile=raw_input("Enter original activation key:\n")
    if profile =="":
     print "Profile cant be blank"
     sys.exit(1)
    checkprofile(sat,key,profile)
    result=sat.kickstart.cloneProfile(key,profile,destprofile)
    if result==1:
     print "Profile %s successfully cloned to %s" % (profile,destprofile)
    else:
     print "Problem cloning"
    if filterori and filterdest:
     childchannels=sat.kickstart.profile.getChildChannels(key,profile)
     #replace kickstart and url using filters
     #ksfilterori=filterori.replace("_",".")
     #ksfilterdest=filterdest.replace("_",".")
     kstree=sat.kickstart.profile.getKickstartTree(key,profile)
     #handle rhel5 weird ks trees up to rhel5.6"
     major,minor=filterdest.split("_")
     if int(major)==5 and int(minor)<=6:
      newkstree="ks-rhel-x86_64-server-%s-u%s" % (major,minor)
     else: 
      newkstree="ks-rhel-x86_64-server-%s-%s.%s" % (major,major,minor)
      #newkstree=kstree.replace(ksfilterori,ksfilterdest)
     if newkstree!=kstree:
      sat.kickstart.profile.setKickstartTree(key,destprofile,newkstree)
     advancedoptions=sat.kickstart.profile.getAdvancedOptions(key,profile)
     newoptions = []
     for option in advancedoptions:
        if option["name"]=="url":
            url=option["arguments"]
            continue
        else:
            newoptions.append(option)
     newurl=url.replace(kstree,newkstree)
     if newurl!=url:
         newoptions.append({'name': 'url', 'arguments': newurl})
         sat.kickstart.profile.setAdvancedOptions(key,destprofile,newoptions)
     #replace activation keys using filters
     aks=sat.kickstart.profile.keys.getActivationKeys(key,destprofile)
     newaks=[]
     deleteaks=[]
     for ak in aks:
      oldak=ak["key"]
      newak=ak["key"].replace(filterori,filterdest)
      if oldak!=newak:
       newaks.append(newak)
       deleteaks.append(oldak)
     if deleteaks!=[]:
      for ak in deleteaks:
       sat.kickstart.profile.keys.removeActivationKey(key,destprofile,ak)
     if newaks!=[]:
      for ak in newaks:
       sat.kickstart.profile.keys.addActivationKey(key,destprofile,ak)
    sys.exit(0)

if deleteprofile: 
 if len(args)==1:
  profile=args[0]
 else:
  print "Usage:satellite.py --deleteprofile profile"
  sys.exit(0)
 checkprofile(sat,key,profile)
 result=sat.kickstart.deleteProfile(key,profile)
 if result==1:
  print "Profile %s successfully deleted" % (profile)
 else:
  print "Problem deleting Profile %s" % (profile)
 sys.exit(0)

if package:
    packinfo = sat.packages.search.name(key,package)
    channelslist=[]
    for info in packinfo:
        packageid = info["id"]
        packagechannels = sat.packages.listProvidingChannels(key,packageid)
        for chan in sorted(packagechannels):
            if chan["name"] not in channelslist:
                channelslist.append(chan["name"])
    for chan in sorted(channelslist):
        print chan
    sys.exit(0)

if removenewer:
    if not softwarechannel:
        print "Usage:satellite.py -S channel --removenewer YYYY-MM-DD"
        sys.exit(0)
    checksoftwarechannel(sat,key,softwarechannel)
    try:
        year,month,day=removenewer.split("-")
    except:    
        print "Usage:satellite.py -S channel --removenewer YYYY-MM-DD"
        os._exit(1)
    maxdate = datetime.datetime(int(year) , int(month), int(day) ,23 ,59 )
    badpackages=sat.channel.software.listAllPackages(key,softwarechannel,maxdate)
    removelist=[]
    if len(badpackages) > 0:
        print "Following packages will be removed" 
        for pack in badpackages:
            packageid=int(pack["id"])
            removelist.append(packageid)
            print "%s-%s-%s.%s" % (pack["name"], pack["version"], pack["release"], pack["arch_label"])
        sat.channel.software.removePackages(key,softwarechannel,removelist)
        print "\n"
        print "%d packages removed from channel %s" % (len(removelist),softwarechannel)
    else:
        print "No packages to remove"
    sys.exit(0)



if not machines and not users and not clients and not groups and not profiles and not extendedprofiles and not channels and not configs and not extendedconfigs and not getfile and not uploadfile and not clonechannel and not deletechannel and not checkerratas  and not duplicatescripts and not tasks and not deletesystem and not execute and not deploy and not history and activationkeys and not basechannel and not softwarechannel and not removechildchannel and not channelname and not cloneak and deleteak and not cloneprofile and not package and not removenewer and not advancedoption:
     print "No action specified"
     sys.exit(1)

sat.auth.logout(key)
sys.exit(0)

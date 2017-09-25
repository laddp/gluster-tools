#!/usr/bin/python
# $Id$
import sys,os,re
from datetime import datetime, timedelta
import string

def usage():
    print "Usage:\n" + sys.argv[0] + " {-h | --help} | [-d] {layout} {georep_status_f1} {georep_status_f2}"
    print "\n=== Gluster geo-replication status check comparison tool ==="
    print "* Parse output for two geo-replication status reports"
    print "* Report the time difference between the two, as well as the progress rates"
    print "* Report any errors identified"
    print "\nArguments:"
    print "  -h|--help            Display this help text"
    print "  -d[dbg_level]        Enable debugging"
    print "  {layout}             Volume layout (i.e. 4x3)"
    print "  {georep_status_f1/2} Files containing geo-replication status output for a single session"
    print "                         - time is taken either from modification time of file, or from single"
    print "                           line timestamp of format yyyy-mm-dd hh:mm:ss on a line in file"
    print "--- v1.0 --- pmladd@gmail.com"

#####################
# Argument processing
#####################
args=sys.argv[1:]

if len(args) < 3 or args[0] == "-h" or args[0] == "--help":
    usage()
    exit(0)

dbgarg = re.match("^-d(\d*)", args[0])
dbg_lvl = 0
if dbgarg:
    if dbgarg.group(1):
        dbg_lvl = int(dbgarg.group(1))
    else:
        dbg_lvl = 1
    args=args[1:]

if len(args) != 3:
    usage()
    exit(1)

layout = args[0].split('x');
args=args[1:]


######################
# Print debug messages
######################
def debug(*args):
    if dbg_lvl >= args[0]:
        for i in args[1:]:
            print i,
        print

######################################
# Convert timestamp to datetime object
######################################
def ts_to_datetime(ts):
    if ts == "N/A":
        return None
    else:
#        tstamp_line = re.compile("^\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\s*$")
#        return datetime(int(time_match.group(1)),int(time_match.group(2)),int(time_match.group(3)),int(time_match.group(4)),int(time_match.group(5)),int(time_match.group(6)))
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

###################################
# Read through status file
# Return parsed array and timestamp
###################################
def parse_file(f):
    parsed_file = []
    blank_line  = re.compile("^\s*$")
    header_line = re.compile("^\s*MASTER NODE\s+MASTER VOL\s+MASTER BRICK\s+SLAVE USER\s+SLAVE\s+SLAVE NODE\s+STATUS\s+CRAWL STATUS\s+LAST_SYNCED\s+$")
    sep_line    = re.compile("^\s*-+\s*$")
    tstamp_line = re.compile("^\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\s*$")
    status_line = re.compile("^\s*\
(?P<master_node>\S+)\s+\
(?P<master_vol>\S+)\s+\
(?P<master_brick>\S+)\s+\
(?P<slave_user>\S+)\s+\
(?P<slave>\S+)\s+\
(?P<slave_node>\S+)\s+\
(?P<status>Active|Passive|Faulty|Stopped|Intitializing...)\s+\
(?P<crawl_status>N/A|Changelog Crawl|History Crawl|Hybrid Crawl)\s+\
(?P<last_synced>(N/A)|(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2}))\s*$")

    file_time = datetime.fromtimestamp(os.path.getmtime(f.name))

    for line in f:
        debug(4,line)
        if blank_line.match(line):
            debug(3,"blank line")
            continue
        if header_line.match(line):
            debug(3, "header line")
            continue
        if sep_line.match(line):
            debug(3, "sep line")
            continue
        time_match = tstamp_line.match(line)
        if time_match != None:
            debug(3, "time line")
            file_time = ts_to_datetime(string.strip(line))
            continue

        parsed_line = status_line.match(line)
        if parsed_line == None:
            print "Unable to parse line:\n"+line
            exit(2)
        else:
            debug(3, "status line: ", parsed_line.groupdict())
            parsed_file.append(parsed_line.groupdict())
    return parsed_file,file_time

#######################
# Build dict of volumes
#######################
def volumes_for(lines):
    volumes = {}
    for line in lines:
        volume = line['master_vol']
        if not volume in volumes:
            volumes[volume] = [ line ]
        else:
            newval = volumes[volume] + [line]
            volumes[volume] = newval
    return volumes

######################
# Build dict of sessions
######################
def sessions_for_volume(lines):
    sessions = {}
    for line in lines:
        slave = line['slave']
        if not slave in sessions:
            sessions[slave] = [line]
        else:
            newval = sessions[slave] + [line]
            sessions[slave] = newval
    return sessions

######################
# Build dict of masters
######################
def masters_for_session(lines):
    masters = {}
    for line in lines:
        master = (line['master_node'], line['master_brick'])
        if not master in masters:
            masters[master] = line
        else:
            print "[E] **** Error: duplicate master/brick combination!"
            print "        Master: ", line['master_node'], " Brick: ", line['master_brick']
            exit(5)
    return masters

######################
# Print node counts
######################
def print_nodereport():
    print "\n===== Nodes ====="
    print "Subvolumes: ", subvol_count
    print "Replication factor: ", replica_count
    print "Total bricks: ", brick_count
    print "now  # nodes: ", now_nodecount
    print "prev # nodes: ", be4_nodecount
    noderpt_printed = True

######################
# Print volume details
######################
def print_volume(volume, lines):
    print "Volume ", volume, ": ============"
    sessions = sessions_for_volume(lines)
    for session, lines in sessions.items():
        print "Session: ", session
        masters = masters_for_session(lines)
        for master, line in sorted(masters.items()):
            print "\tNode: ",           line['master_node'], \
                  " ||| Brick:",        line['master_brick'],\
                  " ||| Slave:",        line['slave_node'], \
                  " ||| Status:",       line['status'], \
                  " ||| Crawl Status:", line['crawl_status']
            #, "||| Last Sync: ", line['last_synced']

########################
# Main line code
########################
f1 = open(args[0])
f1_parsed = parse_file(f1)
debug(2,f1_parsed)

f2 = open(args[1])
f2_parsed = parse_file(f2)
debug(2,f2_parsed)

# Time calculations
print "===== Times ====="
elapsed_time = abs(f1_parsed[1] - f2_parsed[1])
print "F1 time: ", f1_parsed[1]
print "F2 time: ", f2_parsed[1]
print "Elapsed time: ", elapsed_time

now_file   = None
now_parsed = None
now_time   = None

be4_file   = None
be4_parsed = None
be4_time  = None

if f1_parsed[1] > f2_parsed[1]:
    now_file   = f1
    now_parsed = f1_parsed
    now_time   = f1_parsed[1]
    be4_file   = f2
    be4_parsed = f2_parsed
    be4_time   = f2_parsed[1]
elif f1_parsed[1] < f2_parsed[1]:
    now_file   = f2
    now_parsed = f2_parsed
    now_time   = f2_parsed[1]
    be4_file   = f1
    be4_parsed = f1_parsed
    be4_time   = f1_parsed[1]
else:
    "[E] Times on both files are the same.  Comparison not possible"
    exit(6)

#############
# Node checks
#############
# Note: These checks assume that there is only one session contained in both files
#       Another way to get the volume topology other than as a command line argument
#       will be needed if this code is enhanced to handle multiple volumes or sessions
subvol_count=int(layout[0])
replica_count=int(layout[1])
brick_count = subvol_count * replica_count
expected_active_count=subvol_count
expected_passive_count=brick_count - subvol_count

now_nodecount = len(now_parsed[0])
be4_nodecount = len(be4_parsed[0])

node_errors = ""
if now_nodecount != be4_nodecount:
    node_errors += "[W] **** Warning: node counts not equal ****\n"
if now_nodecount != brick_count:
    node_errors += "[E] **** Error: now nodecount not equal to brick count ****\n"
if be4_nodecount != brick_count:
    node_errors += "[W] **** Warning: previous nodecount not equal to brick count ****\n"
if len(node_errors) > 0 or dbg_lvl >= 1:
    print_nodereport()
    print node_errors

# Session details
now_volumes = volumes_for(now_parsed[0])
if dbg_lvl >= 1:
    print "\n===== Sessions ====="
    for volume, lines in now_volumes.items():
        print_volume(volume, lines)

be4_volumes = volumes_for(be4_parsed[0])
if dbg_lvl >= 1:
    for volume, lines in be4_volumes.items():
        print_volume(volume, lines)

####################
# Correlate Sessions
####################
if len(now_volumes.keys()) != 1 or len(be4_volumes.keys()) != 1:
    print "Correlating sessions with multiple volumes not currently supported"
    exit(2)

now_volume, now_vol_lines = now_volumes.items()[0]
be4_volume, be4_vol_lines = be4_volumes.items()[0]

debug(2, "volumes: ", now_volume, be4_volume)

if now_volume != be4_volume:
    print "[E] Status files contain sessions from different volumes"
    exit(3)

now_sessions = sessions_for_volume(now_vol_lines)
be4_sessions = sessions_for_volume(be4_vol_lines)
if len(now_sessions.keys()) != 1 or len(now_sessions.keys()) != 1:
    print "Correlating sessions with multiple sessions is not currently supported"
    exit(2)

now_session, now_session_lines = now_sessions.items()[0]
be4_session, be4_session_lines = be4_sessions.items()[0]

debug(2, "slave sessions: ", now_session, be4_session)

if now_session != be4_session:
    print "[E] Status files contain sessions to different slaves"
    exit(4)

now_masters = masters_for_session(now_session_lines)
be4_masters = masters_for_session(be4_session_lines)

debug(3, "now masters: ", now_masters.keys())
debug(3, "be4 masters: ", be4_masters.keys())

now_actives = {}
be4_actives = {}

now_passives = {}
be4_passives = {}

now_others = {}
be4_others = {}

# Separate out by type
for master, line in now_masters.items():
    if line['status'] == "Active":
        now_actives[master] = line
    elif line['status'] == "Passive":
        now_passives[master] = line
    else:
        now_others[master] = line

for master, line in be4_masters.items():
    if line['status'] == "Active":
        be4_actives[master] = line
    elif line['status'] == "Passive":
        be4_passives[master] = line
    else:
        be4_others[master] = line

# Check active count == subvolume count
if len(now_actives) != expected_active_count:
    print "[E] Error: Current active count (", len(now_actives), ") not equal to subvolume count (", expected_active_count, ")"
if len(be4_actives) != expected_active_count:
    print "[W] Warning: Previous active count (", len(be4_actives), ") not equal to subvolume count (", expected_active_count, ")"

# Check passive count == (brick count - subvolume count)
if len(now_passives) != expected_passive_count:
    print "[E] Error: Current passive count (", len(now_passives), ") not equal to subvolume count (", expected_passive_count, ")"
if len(be4_passives) != expected_passive_count:
    print "[W] Warning: Previous passive count (", len(be4_passives), ") not equal to subvolume count (", expected_passive_count, ")"

# Report on any nodes not in active or passive
if len(now_others) != 0:
    print "[E] Error: Some current bricks not in Active/Passive status:"
    for master, line in sorted(now_others.items()):
        print "Brick: ", master, " Status: ", line['status']
if len(be4_others) != 0:
    print "[W] Warning: Some previous bricks not in Active/Passive status:"
    for master, line in sorted(be4_others.items()):
        print "\tBrick: ", master, " Status: ", line['status']

for master, line in now_actives.items():
    if master in sorted(be4_actives):
        last_sync = ts_to_datetime(line['last_synced'])
        behind_time = now_time - last_sync
        progress =  last_sync - ts_to_datetime(be4_actives[master]['last_synced'])
        progress_ratio = progress.total_seconds() / elapsed_time.total_seconds()
        print "Node:", master, "Current:", last_sync, "||| Behind:", behind_time, "||| Progress:", progress, "||| Progress Ratio:", "%.4f" % progress_ratio
        if progress_ratio < 0.95:
            print "[E] Error: Progress ratio is signifigantly less than 1.0 - geo-replication is falling behind"

    else:
        print master, "not matched in be4"

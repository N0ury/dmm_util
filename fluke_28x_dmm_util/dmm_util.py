#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

import serial
import time
from time import gmtime, strftime
import struct
import sys
import datetime
from calendar import timegm
import argparse
import fluke_28x_dmm_util
import binascii

def version():
  print ('version:',fluke_28x_dmm_util.__version__)

def usage():
  print ('version:',version())
  print ("Usage: python -m [OPTIONS] fluke_28x_dmm_util] command")
  print ("Options:")
  print ("  -p|--port <usb port>       Mandatory port name (ex: COM3)")
  print ("  -s|--separator <separator> Separator for lists and recorded values, defaults to tab '\\t',")
  print ("  -t|--timeout <timeout>     Read timeout. Defaults to 0.09. Be careful changing this value,")
  print ("                             the effect on the total time is important.")
  print ("")
  print ("Command:")
  print ("")
  print ("get")
  print ("  get recordings {name | index} [, {name | index}...]")
  print ("  get minmax {name | index} [, {name | index}...]")
  print ("  get peak {name | index} [, {name | index}...]")
  print ("  get measurements {name | index} [, {name | index}...]")
  print ("")
  print ("  'name' is the name used for a recording, 'index' is a number")
  print ("  These data can be displayed with 'list' command,")
  print ("  'name' can be surrounded by quotes in case it contains spaces.")
  print ("  If this parameter contains only digits, it is assumed to be an index,")
  print ("  otherwise, it will be taken as a name. Multiple names or indexes are permitted, they must be comma separated.")
  print ("")
  print ("set")
  print ("  set company <value>: set DMM company name")
  print ("  set operator <value>: set DMM operator name")
  print ("  set site <value>: set DMM site name")
  print ("  set contact <value>: set DMM contact name")
  print ("  set datetime: set DMM date and time to those of the PC")
  print ("  set names index name: set the name of index recording name")
  print ("")
  print ("  'index' is a value between 1 and 8. List can be obtained using 'show names'.")
  print ("")
  print ("show")
  print ("  show names: display available recording names")
  print ("  show info: display DMM configuration")
  print ("")
  print ("list")
  print ("  list recordings: list recording type recordings")
  print ("  list minmax: list min/max type recordings")
  print ("  list peak: list peak type recordings")
  print ("  list all: list all the recordins")
  print ("")
  print ("display")
  print ("  Use this command to display DMM realtime value.")
  print ("")
  sys.exit()

def start_serial(port):
  global ser
  #serial port settings
  try:
    ser = serial.Serial(port=port, \
          baudrate=115200, bytesize=8, parity='N', stopbits=1, \
          timeout=timeout, rtscts=False, dsrdtr=False)
  except serial.serialutil.SerialException as err:
    print ('Serial port ' + port + ' does not respond')
    print (err)
    sys.exit()
  
def do_sync_time():
  lt = timegm(datetime.datetime.now().utctimetuple())
  cmd = 'mp clock,' + str(lt)
  ser.write(cmd.encode()+b'\r')
  time.sleep (0.1)
  res=ser.read(2)
  if res == b'0\r': print ("Successfully synced the clock of the DMM")
  
def do_current():
  start_serial(port)
  while True:
    try:
      res = qddb()
      print (time.strftime('%Y-%m-%d %H:%M:%S',res['readings']['LIVE']['ts']), \
            ":", \
            res['readings']['LIVE']['value'], \
            res['readings']['LIVE']['unit'], \
            "=>", \
            res['prim_function'])
    except KeyboardInterrupt:
      sys.exit()

def format_duration(start_time, end_time):
  seconds = time.mktime(end_time) - time.mktime(start_time)
  m, s = divmod(int(seconds), 60)
  h, m = divmod(m, 60)
  d, h = divmod(h, 24)
  return f'{d:02d}:{h:02d}:{m:02d}:{s:02d}'
  

def do_list(type):
  start_serial(port)
  nb = qsls()
  nbr  = int(nb['nb_recordings'])
  nbmm = int(nb['nb_min_max'])
  nbp  = int(nb['nb_peak'])

  items = {}
  if type == 'recordings': items[type] = {'cmd':'qrsi','nb':nbr,'lib':'Recording'}
  elif type == 'minmax': items[type] = {'cmd':'qmmsi','nb':nbmm,'lib':'MinMax'}
  elif type == 'peak': items[type] = {'cmd':'qpsi','nb':nbp,'lib':'Peak'}
  else: items = { 'minmax':{'cmd':'qmmsi','nb':nbmm,'lib':'MinMax'},
           'peak':{'cmd':'qpsi','nb':nbp,'lib':'Peak'},
           'recordings':{'cmd':'qrsi','nb':nbr,'lib':'Recording'}}

  for item in items:
    cmd = items[item]['cmd']
    nb = items[item]['nb']
    lib = items[item]['lib']
    if item in ['minmax','peak']:
      print ('Index','Name','Type','Start','End','Duration',sep=sep)
      for i in range (1,nb+1):
        mm = do_min_max_cmd(cmd, str(i-1))
        duration = format_duration(mm['start_ts'], mm['end_ts'])
        name = mm['name'].decode()
        debut_d = time.strftime('%Y-%m-%d %H:%M:%S',mm['start_ts'])
        fin_d = time.strftime('%Y-%m-%d %H:%M:%S',mm['end_ts'])
        print(f'{i:d}',name,lib,debut_d,fin_d,
              duration,sep=sep)
      print ('')

    if item == 'recordings':
      print ('Index','Name','Type','Start','End','Duration','Measurements',sep=sep)
      for i in range (1,nb + 1):
        recording = qrsi(str(i-1))
        duration = format_duration(recording['start_ts'], recording['end_ts'])
        name = recording['name'].decode()
        sample_interval = recording['sample_interval']
        num_samples = recording['num_samples']
        debut_d = time.strftime('%Y-%m-%d %H:%M:%S',recording['start_ts'])
        fin_d = time.strftime('%Y-%m-%d %H:%M:%S',recording['end_ts'])
        print(f'{i:d}',name,lib,debut_d,fin_d,
              duration,num_samples,sep=sep)
      print ('')

def qddb():
  bytes = meter_command("qddb")

  reading_count = get_u16(bytes, 32)
  if len(bytes) != reading_count * 30 + 34:
    raise ValueError('By app: qddb parse error, expected %d bytes, got %d' % ((reading_count * 30 + 34),len(bytes)))
  tsval = get_double(bytes, 20)
  # all bytes parsed
  return {
    'prim_function' : get_map_value('primfunction', bytes, 0),
    'sec_function' : get_map_value('secfunction', bytes, 2),
    'auto_range' : get_map_value('autorange', bytes, 4),
    'unit' : get_map_value('unit', bytes, 6),
    'range_max' : get_double(bytes, 8),
    'unit_multiplier' : get_s16(bytes, 16),
    'bolt' : get_map_value('bolt', bytes, 18),
#    'ts' : (tsval < 0.1) ? nil : parse_time(tsval), # 20
    'ts' : 0,
    'mode' : get_multimap_value('mode', bytes, 28),
    'un1' : get_u16(bytes, 30),
    # 32 is reading count
    'readings' : parse_readings(bytes[34:])
  }

def do_set(parameter):
  start_serial(port)
  property = parameter[0]
  match property:
    case 'company' | 'site' | 'operator' | 'contact':
      if len(parameter) != 2: usage()
      value = parameter[1]
      cmd = 'mpq ' + property + ",'" + value + "'\r"
      res = meter_command(cmd)
    case 'datetime':
      if len(parameter) != 1: usage()
      do_sync_time()
    case 'autohold_threshold':
      if len(parameter) != 2: usage()
      value = parameter[1]
    case 'names':
      if len(parameter) != 3: usage()
      if not parameter[1].isdigit(): usage()
      index = int(parameter[1])
      name = parameter[2]
      cmd = 'savname ' + str(index-1) + ',"' + name + '"\r'
      res = meter_command(cmd)
    case _:
      usage()
  print ("Successfully set",property, "value")

def do_show(conf_item):
  start_serial(port)
  if conf_item == 'info':
    info = id()
    print ("Model:",info['model_number'])
    print ("Software Version:",info['software_version'])
    print ("Serial Number:",info['serial_number'])
    print ("Current meter time:",time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(int(clock()))))
    print ("Company:",meter_command("qmpq company")[0].lstrip("'").rstrip("'"))
    print ("Contact:",meter_command("qmpq contact")[0].lstrip("'").rstrip("'"))
    print ("Operator:",meter_command("qmpq operator")[0].lstrip("'").rstrip("'"))
    print ("Site:",meter_command("qmpq site")[0].lstrip("'").rstrip("'"))
    print ("Autohold Threshold:",meter_command("qmp aheventTh")[0].lstrip("'").rstrip("'"))
    print ("Language:",meter_command("qmp lang")[0].lstrip("'").rstrip("'"))
    print ("Date Format:",meter_command("qmp dateFmt")[0].lstrip("'").rstrip("'"))
    print ("Time Format:",meter_command("qmp timeFmt")[0].lstrip("'").rstrip("'"))
    print ("Digits:",meter_command("qmp digits")[0].lstrip("'").rstrip("'"))
    print ("Beeper:",meter_command("qmp beeper")[0].lstrip("'").rstrip("'"))
    print ("Temperature Offset Shift:",meter_command("qmp tempOS")[0].lstrip("'").rstrip("'"))
    print ("Numeric Format:",meter_command("qmp numFmt")[0].lstrip("'").rstrip("'"))
    print ("Auto Backlight Timeout:",meter_command("qmp ablto")[0].lstrip("'").rstrip("'"))
    print ("Auto Power Off:",meter_command("qmp apoffto")[0].lstrip("'").rstrip("'"))
  elif conf_item == 'names':
    names()
  else: usage()

def id():
  res = meter_command("ID")
  return {'model_number' : res[0], 'software_version' : res[1], 'serial_number' : res[2]}

def qsls():
  res = meter_command("qsls")
  return {'nb_recordings':res[0],'nb_min_max':res[1],'nb_peak':res[2],'nb_measurements':res[3]}

def clock():
  res = meter_command("qmp clock")
  return res[0]

def qsrr(reading_idx, sample_idx):
  retry_count = 0
  while retry_count < 20:
#    print ("in qsrr reading_idx=",reading_idx,",sample_idx",sample_idx)
    res = meter_command("qsrr " + reading_idx + "," + sample_idx)
#    print('qsrr',binascii.hexlify(res))
    if len(res) == 146:
      return {
        'start_ts' :  parse_time(get_double(res, 0)),
        'end_ts' :  parse_time(get_double(res, 8)),
        'readings' : parse_readings(res[16:16 + 30*3]),
        'duration' : round(get_u16(res, 106),5),
        'un2' : get_u16(res, 108),
        'readings2' : parse_readings(res[110:110 +30]),
        'record_type' :  get_map_value('recordtype', res, 140),
        'stable'   : get_map_value('isstableflag', res, 142),
        'transient_state' : get_map_value('transientstate', res, 144)
      }
    else:
#      print ('============== RETRY ===============')
      retry_count += 1

  raise ValueError('By app: Invalid block size: %d should be 146' % (len(res)))

def parse_readings(reading_bytes):
  #print ("in parse_readings,reading_bytes=",reading_bytes,"lgr:",len(reading_bytes))
  readings = {}
  chunks, chunk_size = len(reading_bytes), 30
  l = [ reading_bytes[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
  for r in l:
    readings[get_map_value('readingid', r, 0)] = {
                           'value' : get_double(r, 2),
                           'unit' : get_map_value('unit', r, 10),
                           'unit_multiplier' : get_s16(r, 12),
                           'decimals' : get_s16(r, 14),
                           'display_digits' : get_s16(r, 16),
                           'state' : get_map_value('state', r, 18),
                           'attribute' : get_map_value('attribute', r, 20),
                           'ts' : get_time(r, 22)
    }
#  print ('------',readings)
  return readings

def get_map_value(map_name, string, offset):
#  print "map_name",map_name,"in map_cache",map_name in map_cache
  if map_name in map_cache:
    map = map_cache[map_name]
  else:
    map = qemap(map_name)
    map_cache[map_name] = map
  value = str(get_u16(string, offset))
  if value not in map:
    raise ValueError('By app: Can not find key %s in map %s' % (value, map_name))
  #print ("--->",map_name,value,map[value])
  return map[value]

def get_multimap_value(map_name, string, offset):
#  print "in get_multimap_value,map_name=",map_name
#  print "map_name",map_name,"in map_cache",map_name in map_cache
  if map_name in map_cache:
    map = map_cache[map_name]
  else:
    map = qemap(map_name)
    map_cache[map_name] = map
#  print "in get_multimap_value,map=",map
  value = str(get_u16(string, offset))
#  print "in get_multimap_value,value=",value
  if value not in map:
    raise ValueError('By app: Can not find key %s in map %s' % (value, map_name))
  ret = []
  ret.append(map[value])
#  print "in get_multimap_value,ret=",ret
#  print "+++>",value,map[value],"ret",ret
  return ret

def qemap(map_name):
  res = meter_command("qemap " + str(map_name))
#  print "Traitement de la map: ",map_name
#  print "res dans qemap=",res
#  print "in qemap. Longueur=",len(res)
  entry_count = int(res.pop(0))
#  print "in qemap. entry_count=",entry_count
  if len(res) != entry_count *2:
    raise ValueError('By app: Error parsing qemap')
  map = {}
  for i in range(0, len(res), 2):
    map[res[i]]=res[i+1]
#  print "map dans qemap:",map
  return map

def get_s16(string, offset): # Il faut valider le portage de cette fonction
  val = get_u16(string, offset)
#  print "val in get_s16 avant: ",val
#  print "val in get_s16 pendant: ",val & 0x8000
  if val & 0x8000 != 0:
    val = -(0x10000 - val)
#  print "val in get_s16 ares: ",val
  return val

def get_u16(string, offset):
  endian = string[offset+1:offset-1:-1] if offset > 0 else string[offset+1::-1]
  return struct.unpack('!H', endian)[0]

def get_double(string, offset):
  endian_l = string[offset+3:offset-1:-1] if offset > 0 else string[offset+3::-1]
  endian_h = string[offset+7:offset+3:-1]
  endian = endian_l + endian_h
  return round(struct.unpack('!d', endian)[0],8)

def get_time(string, offset):
  return parse_time(get_double(string, offset))

def parse_time(t):
  return time.gmtime(t)

def qrsi(idx):
#  print ('IDX',idx)
  res = meter_command('qrsi '+idx)
#  print('res',binascii.hexlify(res))
  reading_count = get_u16(res, 76)
#  print ("reading_count",reading_count)
  if len(res) < reading_count * 30 + 78:
    raise ValueError('By app: qrsi parse error, expected at least %d bytes, got %d' % (reading_count * 30 + 78, len(res)))
  return {
    'seq_no' : get_u16(res, 0),
    'un2' : get_u16(res, 2),
    'start_ts' : parse_time(get_double(res, 4)),
    'end_ts' : parse_time(get_double(res, 12)),
    'sample_interval' : get_double(res, 20),
    'event_threshold' : get_double(res, 28),
    'reading_index' : get_u16(res, 36), # 32 bits?
    'un3' : get_u16(res, 38),
    'num_samples' : get_u16(res, 40),  # Is this 32 bits? Whats in 42
    'un4' : get_u16(res, 42),
    'prim_function' : get_map_value('primfunction', res, 44),
    'sec_function' : get_map_value('secfunction', res, 46), # sec?
    'auto_range' : get_map_value('autorange', res, 48),
    'unit' : get_map_value('unit', res, 50),
    'range_max ' : get_double(res, 52),
    'unit_multiplier' : get_s16(res, 60),
    'bolt' : get_map_value('bolt', res, 62),  #bolt?
    'un8' : get_u16(res, 64),  #ts3?
    'un9' : get_u16(res, 66),  #ts3?
    'un10' : get_u16(res, 68),  #ts3?
    'un11' : get_u16(res, 70),  #ts3?
    'mode' : get_multimap_value('mode', res, 72),
    'un12' : get_u16(res, 74),
    # 76 is reading count
    'readings' : parse_readings(res[78:78+reading_count * 30]),
    'name' : res[(78 + reading_count * 30):]
    }

def qsmr(idx):
  # Get saved measurement
  res = meter_command('qsmr '+idx)
  reading_count = get_u16(res, 36)

  if len(res) < reading_count * 30 + 38:
    raise ValueError('By app: qsmr parse error, expected at least %d bytes, got %d' % (reading_count * 30 + 78, len(res)))

  return { '[seq_no' : get_u16(res,0),
    'un1' : get_u16(res,2),   # 32 bit?
    'prim_function' :  get_map_value('primfunction', res,4), # prim?
    'sec_function' : get_map_value('secfunction', res,6), # sec?
    'auto_range' : get_map_value('autorange', res, 8),
    'unit' : get_map_value('unit', res, 10),
    'range_max' : get_double(res, 12),
    'unit_multiplier' : get_s16(res, 20),
    'bolt' : get_map_value('bolt', res, 22),
    'un4' : get_u16(res,24),  # ts?
    'un5' : get_u16(res,26),
    'un6' : get_u16(res,28),
    'un7' : get_u16(res,30),
    'mode' : get_multimap_value('mode', res,32),
    'un9' : get_u16(res,34),
    # 36 is reading count
    'readings' : parse_readings(res[38:38 + reading_count * 30]),
    'name' : res[(38 + reading_count * 30):]
  }

def do_min_max_cmd(cmd, idx):
  res = meter_command(cmd + " " + idx)
  # un8 = 0, un2 = 0, always bolt
  reading_count = get_u16(res, 52)
  if len(res) < reading_count * 30 + 54:
    raise ValueError('By app: qsmr parse error, expected at least %d bytes, got %d' % (reading_count * 30 + 54, len(res)))

  # All bytes parsed
  return { 'seq_no' : get_u16(res, 0),
    'un2' : get_u16(res, 2),      # High byte of seq no?
    'start_ts' : parse_time(get_double(res, 4)),
    'end_ts' : parse_time(get_double(res, 12)),
    'prim_function' : get_map_value('primfunction', res, 20),
    'sec_function' : get_map_value('secfunction', res, 22),
    'autorange' : get_map_value('autorange', res, 24),
    'unit' : get_map_value('unit', res, 26),
    'range_max ' : get_double(res, 28),
    'unit_multiplier' : get_s16(res, 36),
    'bolt' : get_map_value('bolt', res, 38),
    'ts3' : parse_time(get_double(res, 40)),
    'mode' : get_multimap_value('mode', res, 48),
    'un8' : get_u16(res, 50),
    # 52 is reading_count
    'readings' : parse_readings(res[54:54 + reading_count * 30]),
    'name' : res[(54 + reading_count * 30):]
    }

def do_saved_peak(records):
  do_saved_min_max_peak(records, 'nb_peak', 'qpsi')

def do_saved_min_max(records):
  do_saved_min_max_peak(records, 'nb_min_max', 'qmmsi')

def do_saved_min_max_peak(records, field, cmd):
  start_serial(port)
  nb_min_max = int(qsls()[field])
  interval = []
  for i in range(1,nb_min_max+1):
    interval.append(str(i))
  found = False
  if len(records) == 0:
    series = interval
  else:
    series = records

  for i in series:
    if i.isdigit():
      measurement = do_min_max_cmd(cmd,str(int(i)-1))
      print_min_max_peak(measurement)
      found = True
    else:
      for j in interval:
        measurement = do_min_max_cmd(cmd,str(int(j)-1))
        if measurement['name'] == i.encode():
          found = True
          print_min_max_peak(measurement)
          break
  if not found:
    print ("Saved names not found")
    sys.exit()

def print_min_max_peak(measurement):
  print ((measurement['name']).decode('utf-8'), 'start', time.strftime('%Y-%m-%d %H:%M:%S',measurement['start_ts']), measurement['autorange'], 'Range', int(measurement['range_max ']), measurement['unit'])
  print_min_max_peak_detail(measurement, 'PRIMARY')
  print_min_max_peak_detail(measurement, 'MAXIMUM')
  print_min_max_peak_detail(measurement, 'AVERAGE')
  print_min_max_peak_detail(measurement, 'MINIMUM')
  print ((measurement['name']).decode('utf-8'), 'end', time.strftime('%Y-%m-%d %H:%M:%S',measurement['end_ts']))

def print_min_max_peak_detail(measurement, detail):
  print ('\t',detail, \
        measurement['readings'][detail]['value'], \
        measurement['readings'][detail]['unit'], \
        time.strftime('%Y-%m-%d %H:%M:%S',measurement['readings'][detail]['ts']),sep=sep)

def do_saved_measurements(records):
  start_serial(port)
  nb_measurements = int(qsls()['nb_measurements'])
  if len(records) != 0:
    if records[0] == 'list':
      print ('list: invalid option')
      sys.exit()
  interval = []
  for i in range(1,nb_measurements + 1):
    interval.append(str(i))
  found = False
  if len(records) == 0:
    series = interval
  else:
    series = records

  for i in series:
    if i.isdigit():
      measurement = qsmr(str(int(i)-1))
      print ((measurement['name']).decode('utf-8'), \
          time.strftime('%Y-%m-%d %H:%M:%S',measurement['readings']['PRIMARY']['ts']), \
          measurement['readings']['PRIMARY']['value'], \
          measurement['readings']['PRIMARY']['unit'],sep=sep)
      found = True
    else:
      for j in interval:
        measurement = qsmr(str(int(j)-1))
        if measurement['name'] == i.encode():
          found = True
          print ((measurement['name']).decode('utf-8'), \
              time.strftime('%Y-%m-%d %H:%M:%S',measurement['readings']['PRIMARY']['ts']), \
              ":", \
              measurement['readings']['PRIMARY']['value'], \
              measurement['readings']['PRIMARY']['unit'],sep=sep)
          break
  if not found:
    print ("Saved names not found")
    sys.exit()

def do_recordings(records):
  start_serial(port)
  nb_recordings = int(qsls()['nb_recordings'])
  interval = []
  for i in range(1,nb_recordings + 1):
    interval.append(str(i))
  found = False
  if len(records) == 0:
    series = interval
  else:
    series = records

  for i in series:
    if i.isdigit():
      recording = qrsi(str(int(i)-1))
      #print ('recording digit',recording)
      duration = format_duration(recording['start_ts'], recording['end_ts'])
      print ('Index %s, Name %s, Start %s, End %s, Duration %s, Measurements %s' \
            % (str(i), (recording['name']).decode(),time.strftime('%Y-%m-%d %H:%M:%S',recording['start_ts']),time.strftime('%Y-%m-%d %H:%M:%S',recording['end_ts']), duration, recording['num_samples']))
      print ('Start Time','Primary','','Maximum','','Average','','Minimum','','#Samples','Type',sep=sep)

      for k in range(0,recording['num_samples']):
        measurement = qsrr(str(recording['reading_index']), str(k))
        #print ('measurement',measurement)
        duration = str(round(measurement['readings']['AVERAGE']['value'] \
            / measurement['duration'],measurement['readings']['AVERAGE']['decimals'])) \
            if measurement['duration'] != 0 else 0
        print (time.strftime('%Y-%m-%d %H:%M:%S', measurement['start_ts']), \
              str(measurement['readings2']['PRIMARY']['value']), \
              measurement['readings2']['PRIMARY']['unit'], \
              str(measurement['readings']['MAXIMUM']['value']), \
              measurement['readings']['MAXIMUM']['unit'], \
              duration, \
              measurement['readings']['AVERAGE']['unit'], \
              str(measurement['readings']['MINIMUM']['value']), \
              measurement['readings']['MINIMUM']['unit'], \
              str(measurement['duration']),sep=sep,end=sep)
        print ('INTERVAL' if measurement['record_type'] == 'INTERVAL' else measurement['stable'])
      print
      found = True
    else:
      for j in interval:
        recording = qrsi(str(int(j)-1))
        #print ('recording non digit',recording)
        if recording['name'] == i.encode():
          found = True
          duration = format_duration(recording['start_ts'], recording['end_ts'])
          print ('Index %s, Name %s, Start %s, End %s, Duration %s, Measurements %s' \
            % (str(j), (recording['name']).decode(),time.strftime('%Y-%m-%d %H:%M:%S',recording['start_ts']),time.strftime('%Y-%m-%d %H:%M:%S',recording['end_ts']), duration, recording['num_samples']))
          print ('Start Time','Primary','','Maximum','','Average','','Minimum','','#Samples','Type',sep=sep)
          for k in range(0,recording['num_samples']):
            measurement = qsrr(str(recording['reading_index']), str(k))
#            print ('measurement',measurement)
            duration = str(round(measurement['readings']['AVERAGE']['value'] \
                / measurement['duration'],
                  measurement['readings']['AVERAGE']['decimals'])) \
                if measurement['duration'] != 0 else 0
            print (time.strftime('%Y-%m-%d %H:%M:%S', measurement['start_ts']), \
                  str(measurement['readings2']['PRIMARY']['value']), \
                  measurement['readings2']['PRIMARY']['unit'], \
                  str(measurement['readings']['MAXIMUM']['value']), \
                  measurement['readings']['MAXIMUM']['unit'], \
                  duration, \
                  measurement['readings']['AVERAGE']['unit'], \
                  str(measurement['readings']['MINIMUM']['value']), \
                  measurement['readings']['MINIMUM']['unit'], \
                  str(measurement['duration']),sep=sep,end=sep)
            print ('INTERVAL' if measurement['record_type'] == 'INTERVAL' else measurement['stable'])
          print
          break
  if not found:
    print ("Saved names not found")
    sys.exit()

def data_is_ok(data):
  # No status code yet
  if len(data) < 2: return False

  # Non-OK status
  if len(data) == 2 and chr(data[0]) == '0' and chr(data[1]) == "\r": return True

  # Non-OK status with extra data on end
  if len(data) > 2 and chr(data[0]) != '0': return False

  # We should now be in OK state
  if not data.startswith(b"0\r"): return False

  return len(data) >= 4 and chr(data[-1]) == '\r'

def read_retry(cmd):
  retry_cmd_count = 0
  retry_read_count = 0
  data = b''

  while retry_cmd_count < 20 and not data_is_ok(data):
    ser.write(cmd.encode()+b'\r')
    while retry_read_count < 20 and not data_is_ok(data):
      bytes_read = ser.read(ser.in_waiting)
      data += bytes_read
      if data_is_ok(data): return data,True
      time.sleep (0.01)
      retry_read_count += 1
    retry_cmd_count += 1
#    print ("========== read_retry ===========")
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.close()
    ser.open()
    time.sleep (0.01)

    return data, False

def meter_command(cmd):
#  print ("cmd=",cmd)
  retry_count = 0
  while retry_count < 20:
    data,result_ok = read_retry(cmd)
    if data == b'':
      print ('Did not receive data from DMM')
      sys.exit(1)
    status = chr(data[0])
    if status == '0' and chr(data[1]) == '\r': break
    if result_ok: break
    retry_count += 1
#    print ("========== meter_command ===========")

  if status != '0':
#    print ("Command: %s failed. Status=%c" % (cmd, status))
    print ("Invalid value")
    sys.exit()
  if chr(data[1]) != '\r':
    print ('Did not receive complete reply from DMM')
    sys.exit(1)

  binary = data[2:4] == b'#0'

  if binary:
    return data[4:-1]
  else:
    data = [i for i in data[2:-1].decode().split(',')]
    return data

def main():
  argc = len(sys.argv)
  if argc <= 2:
     usage();
     exit
  
  global sep
  global map_cache
  global timeout
  global port
  sep = '\t'
  ser = None
  timeout = 0.09
  map_cache = {}
  
  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--port", help="usb port used (Mandatory)")
  parser.add_argument("-s", "--separator", help="custom separator (defaults to \\t")
  parser.add_argument("-t", "--timeout", help="custom timeout (defaults to 0.09)")
  parser.add_argument("-v", "--version", help="show version and exit", action="store_true")
  parser.add_argument("command", nargs="*", help="command used")
  args = parser.parse_args()
  
  port = args.port

  if args.separator:
    sep = args.separator

  if args.timeout:
    timeout = float(args.timeout)

  if args.version:
    version()
    sys.exit()

  if len(args.command) == 0:
    usage()

  match args.command[0]:
    case "get":
      if len(args.command[1:]) == 2:
        series = args.command[2].split(",")
      match args.command[1]:
        case "recordings":
          if len(args.command[1:]) != 2: usage()
          do_recordings(series)
        case "measurements":
          if len(args.command[1:]) != 2: usage()
          do_saved_measurements(series)
        case "minmax":
          if len(args.command[1:]) != 2: usage()
          do_saved_min_max(series)
        case "peak":
          if len(args.command[1:]) != 2: usage()
          do_saved_peak(series)
        case "current":
          if len(args.command[1:]) != 1: usage()
          do_current()
        case _:
          usage()
    case "show":
      if len(args.command[1:]) != 1: usage()
      if args.command[1] not in ['info','names']: usage()
      do_show(args.command[1])
    case "set":
      if len(args.command[1:]) not in [1,2,3]: usage()
      do_set(args.command[1:])
    case "display":
      do_display()
    case "list":
      if len(args.command[1:]) != 1: usage()
      if args.command[1] not in ['recordings','minmax','peak','all']: usage()
      do_list(args.command[1])
    case _:
      usage()

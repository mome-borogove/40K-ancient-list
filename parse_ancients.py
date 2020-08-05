#!/usr/bin/env python3

SHOW_ALL = True

from xml.etree import ElementTree as ETree
from enum import Enum
import re
import sys

from fsm import FSM
from parse_langs import parse_langs
from parse_enchants import parse_enchants

def parse_ancients(file):
  root = ETree.parse(file)
  artifacts = root.find('Artifacts')
  ancients = artifacts.find('Ancient')
  amap = {}
  for ancient in ancients:
    if str.lower(ancient.tag) in amap:
      print('AARGH!',ancient.tag)
    adjective = ancient.find('eng').text
    if adjective is None:
      adjective = '[No adjective]'
    amap[str.lower(ancient.tag)] = adjective
  return amap

_S = Enum('_S','TOP ITEM_START ITEM INNER')

def store_name(M,D):
  k = str.lower(M[0])
  D['name'] = k
  D['items'][k] = {}
  return _S.ITEM_START

def store_value(M,D):
  D['items'][D['name']][M[0]] = M[1]
  return None

machine = {
  _S.TOP: [
    (r'([^\s]+)', store_name),
    (r' *', None),
  ],
  _S.ITEM_START: [
    (r'{', lambda: _S.ITEM ),
  ],
  _S.ITEM: [
    (r'{', lambda: _S.INNER ),
    (r'}', lambda: _S.TOP ),
    (r'(.*)=(.*)', store_value),
    (r'.*', None),
  ],
  _S.INNER: [
    (r'}', lambda: _S.ITEM),
    (r'.*', None),
  ],
}

def parse_inventory(file):
  fsm = FSM(_S, _S.TOP, [_S.TOP], machine)
  fsm.reset()
  fsm.data = {'name': None, 'items': {}}
  #fsm.tracing(True)

  while True:
    rawline = file.readline()
    if rawline=='':
      fsm.terminate()
      return fsm.data['items']
    line = rawline.strip()
    fsm(line)
  raise Exception('Unknown error: file parsing failed.')

def format(s, prop, value):
  # *sigh* Neocore apparently doesn't fill in some properties, but they use
  # 'artifact_enchant' in the strings which don't have Property set correctly.
  if prop=='null' or prop=='undefined':
    prop = 'artifact_enchant'

  # I have no idea what nembonusz; is, but I'm removing it. =p
  s = re.sub(r'\{nembonusz;', r'{', s)

  # Replace the actual numeric property
  if re.search(r'{'+prop,s):
    decimal_places = 2 
    s = re.sub(r'\{'+prop+r'\}',
               str(round(value,decimal_places)), s)
    s = re.sub(r'\{'+prop+r',100\}',
               str(round(100*value,decimal_places))+'%', s)
  return s

if __name__=='__main__':
  with open('Lang_Artifacts.xml') as f:
    ancient_map = parse_ancients(f)
    #print(str(len(ancient_map))+' ancients mapped')

  with open('Lang_Artifacts.xml') as f:
    str_map = parse_langs(f)
    #print(str(len(str_map))+' strings mapped')

    #for k,v in ancient_map.items():
    #  print(k,v)

  with open('enchantments.cfg') as f:
    _, enchants = parse_enchants(f)
    #print(str(len(enchants)),'enchants mapped')
  enchant_map = {str.lower(e.name):(e.desc,e.desc_repl,e.range[1]) for e in enchants}
  #print(enchant_map)
  
  with open('inventoryitems.cfg') as f:
    items = parse_inventory(f)
    #print(str(len(items)),'items mapped')

    #for k,v in items.items():
    #  print(k,v)

  # Should be 1-to-1
  item_map = {}
  for name,vals in items.items():
    if 'AncientName' in vals:
      k = vals['AncientName']
      if SHOW_ALL:
        if k not in item_map:
          item_map[k] = vals
          item_map[k]['Type'] = [item_map[k]['Type']]
        else:
          item_map[k]['Type'].append(vals['Type'])
      else:
        item_map[k] = vals

  #print('Item map',len(item_map))

  item_map = {str.lower(k):v for k,v in item_map.items()}

  for ancient,adjective in sorted(ancient_map.items(),key=lambda x:x[1]):
    item = item_map[ancient]
    #print(ancient,item)
    if SHOW_ALL:
      item_types = ', '.join(sorted(list(set(item['Type']))))
    else:
      item_type = item['Type']
    enchant = str.lower(item['FixEnchants'].split(';')[0])
    desc,prop,val = enchant_map[enchant]
    s = str_map[desc]
    # strip colors
    s = re.sub(r'\[[0-9A-Fa-f]{8}\]',r'',s)
    s = re.sub(r'\[/[0-9A-Fa-f]{8}\]',r'',s)
    # substitute value
    s = format(s, prop, val)
    if SHOW_ALL:
      print(' - **'+str(adjective)+'**: "'+s+'"\\\nItem types: '+str(item_types))
    else:
      print(' - **'+str(adjective)+'** (ex: '+str(item_type)+'): "'+s+'"')


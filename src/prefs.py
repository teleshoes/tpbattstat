#!/usr/bin/env python
##########################################################################
# TPBattStatApplet v0.1
# Copyright 2011 Elliot Wolk
##########################################################################
# This file is part of TPBattStatApplet.
#
# TPBattStatApplet is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# TPBattStatApplet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TPBattStatApplet. If not, see <http://www.gnu.org/licenses/>.
##########################################################################

import os
import sys
import re
from subprocess import Popen, PIPE

def enum(*sequential, **named):
  enums = dict(zip(sequential, sequential), **named)
  enums['valueOf'] = dict(enums)
  enums['names'] = sequential
  return type('Enum', (), enums)

State = enum('CHARGING', 'DISCHARGING', 'IDLE')
DischargeStrategy = enum('SYSTEM', 'LEAPFROG', 'CHASING')
ChargeStrategy = enum('SYSTEM', 'LEAPFROG', 'CHASING', 'BRACKETS')
Interface = enum('ACPI', 'SMAPI', 'ACPI_OLD')
BalanceInterface = enum('THINKPAD_ACPI', 'SMAPI', 'TPACPI')
PowerUsage = enum('NOW', 'AVERAGE', 'OFF')

def getPrefs():
  return [
  Pref("delay", "int", 1000,
    "Delay in ms between updates"),
  Pref("interface", "enum", "SMAPI",
    "Battery info interface (smapi/acpi)",
    Interface),
  Pref("balanceInterface", "enum", "THINKPAD_ACPI",
    "Interface for balancing batteries",
    BalanceInterface),

  Pref("dischargeStrategy", "enum", "LEAPFROG",
    "Strategy for selecting battery to discharge",
    DischargeStrategy),
  Pref("dischargeLeapfrogThreshold", "int", 5,
    "Threshold to justify switching currently discharging battery"),
  Pref("chargeStrategy", "enum", "BRACKETS",
    "Strategy for selecting battery to charge",
    ChargeStrategy),
  Pref("chargeLeapfrogThreshold", "int", 10,
    "Threshold to justify switching currently charging battery"),
  Pref("chargeBrackets", "list-int", [10, 20, 80, 90, 95, 100],
    "Brackets to ensure even charge in charge_strategy=brackets."),
  Pref("chargeBracketsPrefBattery", "int", 0,
    "Battery to charge when both batteries are in the same bracket"),

  Pref("displayPowerUsage", "enum", "NOW",
    "Display power rate in watts, instantaneous or average over the last 60s",
    PowerUsage),
  Pref("displayColoredText", "bool", True,
    "Green/red for charging/discharging"),
  Pref("iconSize", "string", "36x36",
    "Icon WxH in px; (scales in GTK gui, but only exact sizes work in markup printing)"),
  Pref("displayIcons", "bool", True,
    "Show battery icon(s)"),
  Pref("displayOnlyOneIcon", "bool", True,
    "Show one icon with the sum of remaining charge of both batteries"),
  Pref("displayBlinkingIndicator", "bool", True,
    "Alternate separator color every time the display updates"),
  Pref("ledPatternsCharging", "list-string", [],
    "Patterns for the battery LED when charging"),
  Pref("ledPatternsDischarging", "list-string", [],
    "Patterns for the battery LED when charging"),
  Pref("ledPatternsIdle", "list-string", [],
    "Patterns for the battery LED when idle")
  ]

class Pref():
  def __init__(self, name, valType, default, shortDesc, enum=None):
    self.name = name
    self.valType = valType
    self.default = default
    self.shortDesc = shortDesc
    self.enum = enum
    self.longDesc = None

class Prefs():
  def __init__(self):
    self.prefsDir = os.environ['HOME'] + '/' + '.config'
    self.prefsFile = self.prefsDir + '/' + 'tpbattstat.conf'

    self.prefsArr = getPrefs()
    self.prefNames = list(map(lambda p: p.name, self.prefsArr))
    self.prefsByName = dict(zip(self.prefNames, self.prefsArr))
    defVals = list(map(lambda p: p.default, self.prefsArr))
    self.defaultPrefs = dict(zip(self.prefNames, defVals))

    longDescs = getPrefsLongDescriptions()
    for (k, v) in iter(longDescs.items()):
      self.prefsByName[k].longDesc = v

    self.curPrefs = dict(self.defaultPrefs)
    self.lastMod = -1
  def __getitem__(self, prefName):
    if prefName not in self.curPrefs:
      raise Exception("Unknown preference requested: " + prefName)
    return self.curPrefs[prefName]
  def __setitem__(self, prefName, val):
    if prefName not in self.curPrefs:
      raise Exception("Unknown preference requested: " + prefName)
    p = self.prefsByName[prefName]
    self.curPrefs[prefName] = self.readVal(p.name, p.valType, str(val), p.enum)
  def getDefaultPrefsFile(self):
    s = ''
    for p in self.prefsArr:
      s += p.name + " = " + str(p.default)
      s += ' #' + p.shortDesc + "\n"
    return s
  def ensurePrefsFile(self):
    if not os.path.isdir(self.prefsDir):
      os.makedirs(self.prefsDir, 0o755)
    if not os.path.isfile(self.prefsFile):
      f = open(self.prefsFile, 'w')
      f.write(self.getDefaultPrefsFile())
      f.close()
  def checkPrefsFileChanged(self):
    if not os.path.isfile(self.prefsFile):
      return True
    mod = os.path.getmtime(self.prefsFile)
    if self.lastMod != mod:
      self.lastMod = mod
      return True
    return False
  def readPrefsFile(self):
    self.ensurePrefsFile()
    d = dict(self.defaultPrefs)
    f = open(self.prefsFile, 'r')
    lines = f.readlines()
    f.close()
    for line in lines:
      line = line.partition('#')[0]
      line = line.strip()
      if len(line) > 0:
        keyVal = line.split('=', 1)
        if len(keyVal) != 2:
          raise Exception("Error parsing config line: " + line)
        key = keyVal[0].strip()
        val = keyVal[1].strip()
        if key not in self.prefNames:
          raise Exception("Unknown pref: " + key)
        p = self.prefsByName[key]
        d[p.name] = self.readVal(p.name, p.valType, val, p.enum)
    return d
  def writePrefsFile(self):
    s = ''
    for name in self.prefNames:
      val = self.curPrefs[name]
      if val != self.defaultPrefs[name]:
        if self.prefsByName[name].valType[:5] == "list-":
          val = self.listToString(val)
        else:
          val = str(val)
        s += name + " = " + val + "\n"
    f = open(self.prefsFile, 'w')
    f.write(s)
    f.close()
  def listToString(self, xs):
    return '[' + ','.join(map(str, xs)) + ']'
  def readVal(self, prefName, valType, valStr, enumVals):
    valStr = valStr.strip()
    if valType == 'int':
      try:
        return int(valStr)
      except ValueError:
        raise Exception("%s must be an integer: %s" % (prefName, valStr))
    elif valType == 'bool':
      if valStr.lower() == "true":
        return True
      elif valStr.lower() == "false":
        return False
      else:
        raise Exception("%s must be true/false: %s" % (prefName, valStr))
    elif valType == 'string':
      return valStr
    elif valType == 'enum':
      if enumVals == None:
        raise Exception("No enum defined for pref " + prefName)
      valStr = valStr.upper()
      if valStr.upper() not in enumVals.names:
        raise Exception("%s must be one of (%s): %s" %
          (prefName, str(enumVals.names), valStr))
      return enumVals.valueOf[valStr]
    elif valType[:5] == "list-":
      listType = valType[5:]
      if valStr == '':
        valStr = '[]'
      if valStr[0] == '[' and valStr[-1] == ']':
        valStr = valStr[1:-1]
      else:
        raise Exception("%s must be a list (e.g.:[v, v]): %s'" %
          (prefName, valStr))
      valList = []
      if len(valStr) > 0:
        for val in valStr.split(','):
          val = val.strip()
          valList.append(self.readVal(prefName, listType, val, enumVals))
      return valList
  def update(self):
    if self.checkPrefsFileChanged():
      self.curPrefs.update(self.readPrefsFile())

def getPrefsLongDescriptions():
  ledDescription = """
  A list of led-pattern-strings to pass to led-batt.
  There are three lists of led-pattern-strings, one for
    charging, discharging, and idle.
  Patterns are chosen based on the current total remaining battery percent;
    The patterns divide up the percentage ranges,
      based on how many patterns there are.
    {the left-most pattern is always used at 0% and the right-most at 100%}
    e.g.: if there are four patterns: 0-24%, 25-49%, 50-74%, 75-100%

  led-batt controls green/orange battery LEDs and the power LED
    (and any named LED, see `led` command for usage)
  led-batt a list of commands to run in a loop
  some command-lists have synonyms below (see `led-batt --help` for usage)
    fastblink-pgo fastblink-p fastblink-g fastblink-o fastblink-pg fastblink-po fastblink-gp
        blink-pgo     blink-p     blink-g     blink-o     blink-pg     blink-po     blink-gp
    slowblink-pgo slowblink-p slowblink-g slowblink-o slowblink-pg slowblink-po slowblink-gp

  examples:
    1) [blink-o, blink-go, blink-g]
       0% -  33% : blink orange light
      34% -  66% : blink both lights
      67% - 100% : blink green light
    2) [fastblink-po, all, "o G 5 g O 5", green]
       0% -  24% : blink power+orange LEds quickly
      25% -  49% : show power, green, and orange lights steady
      50% -  74% : cycle between orange and green every 5 seconds
      75% - 100% : show green light steady
  """

  return {
    "interface": """
      Interface for obtaining battery information.
      acpi:
        read values from /sys/class/power_supply
      smapi:
        read values from /sys/devices/platform/smapi
      acpi_old:
        read values from /proc/acpi/battery
    """,
    "ledPatternsCharging": ledDescription,
    "ledPatternsDischarging": ledDescription,
    "ledPatternsIdle": ledDescription
  }

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

from prefs import Prefs
from gui import Gui
from gtkmod import GTK_MOD
from battstatus import BattStatus
from guimarkup import GuiMarkupPrinter
from actions import Actions
import sys

class TPBattStat():
  def __init__(self, mode, forceDelay=None, forceIconSize=None):
    self.mode = mode
    self.forceDelay = forceDelay

    self.prefs = Prefs()
    self.battStatus = BattStatus(self.prefs)
    self.actions = Actions(self.prefs, self.battStatus)
    if self.mode == "gtk" or self.mode == "prefs":
      self.gui = Gui(self.prefs, self.battStatus)
    elif self.mode == "json" or self.mode == "dzen":
      self.guiMarkupPrinter = GuiMarkupPrinter(
        self.prefs, self.battStatus, forceIconSize)

  def getGui(self):
    return self.gui
  def startUpdate(self):
    self.curDelay = -1
    self.update()
  def onClickEvent(self, widget, event):
    if event.button == 1:
      self.getGui().showPreferencesDialog()
  def update(self):
    try:
      self.prefs.update()
    except Exception as e:
      print('ignoring prefs')
      print(str(e))
    if self.forceDelay != None:
      self.prefs['delay'] = self.forceDelay
    self.battStatus.update(self.prefs)

    self.actions.performActions()
    if self.mode == "gtk":
      self.gui.update()
    elif self.mode == "json" or self.mode == "dzen":
      try:
        if self.mode == "json":
          markup = self.guiMarkupPrinter.getMarkupJson()
        elif self.mode == "dzen":
          markup = self.guiMarkupPrinter.getMarkupDzen()
        print(markup)
        sys.stdout.flush()
      except IOError:
        sys.stderr.write("STDOUT is broken, assuming external gui is dead" + "\n")
        sys.exit(1)

    if self.prefs['delay'] != self.curDelay:
      self.curDelay = self.prefs['delay']
      if self.curDelay <= 0:
        self.curDelay = 1000
      GTK_MOD.TIMEOUT_ADD_FCT(self.curDelay, self.update)
      return False
    else:
      return True

def showAndExit(gtkElem):
  gtkElem.connect("destroy", GTK_MOD.GTK.main_quit)
  gtkElem.show_all()
  GTK_MOD.GTK.main()
  sys.exit()

def formatCmd(cmdArr):
  return "|".join(cmdArr)
def usage(name, cmds):
  return ("Usage:\n"
    + " " + name + " " + formatCmd(cmds['help']) + "\n"
    + " " + name + " " + formatCmd(cmds['window']) + "\n"
    + " " + name + " " + formatCmd(cmds['json']) + " [delay-ms] [icon-size]\n"
    + " " + name + " " + formatCmd(cmds['dzen']) + " [delay-ms] [icon-size]\n"
    + " " + name + " " + formatCmd(cmds['prefs']) + "\n"
    + "\n"
    + "   delay-ms: override the delay in prefs\n"
    + "   icon-size: override the icon-size in prefs\n"
    )
def getCommand(arg, commands):
  for key in commands:
    if arg in commands[key]:
      return key


def main():
  commands = {
    "help": ["-h", "--help", "help"],
    "window": ["-w", "--window", "window"],
    "json": ["-j", "--json", "json"],
    "dzen": ["-d", "--dzen", "dzen"],
    "prefs": ["-p", "--prefs", "prefs"]
  }

  if len(sys.argv) >= 2:
    cmd = getCommand(sys.argv[1], commands)
    args = sys.argv[2:]
  else:
    print(usage(sys.argv[0], commands))

  if cmd == 'window' and len(args) == 0:
    window = GTK_MOD.GTK.Window(GTK_MOD.WINDOW_TOPLEVEL)
    window.set_title("TPBattStat")
    tpbattstat = TPBattStat("gtk")
    tpbattstat.startUpdate()
    window.add(tpbattstat.gui.getGtkWidget())
    window.add_events(GTK_MOD.BUTTON_PRESS_MASK)
    window.connect("button_press_event", tpbattstat.onClickEvent)
    showAndExit(window)
  elif cmd == 'prefs' and len(args) == 0:
    prefsDialog = TPBattStat("prefs").getGui().getPreferencesDialog()
    showAndExit(prefsDialog)
  elif cmd == 'dzen' or cmd == 'json' and 0 <= len(args) and len(args) <= 2:
    delay = None
    iconSize = None

    if len(args) > 0:
      delay = args[0]
    if len(args) > 1:
      iconSize = args[1]

    tpbattstat = TPBattStat(cmd, forceDelay=delay, forceIconSize=iconSize)
    tpbattstat.startUpdate()
    GTK_MOD.GTK.main()
    sys.exit()
  else:
    print(usage(sys.argv[0], commands))

if __name__ == "__main__":
  sys.exit(main())


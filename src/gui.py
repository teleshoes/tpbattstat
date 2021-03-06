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

from battstatus import State
from guiprefs import GuiPrefs
from gtkmod import GTK_MOD
import re

IMAGE_DIR = '/usr/share/pixmaps/tpbattstat-applet/svg'

class Gui():
  def __init__(self, prefs, battStatus, orientation='horizontal'):
    self.prefs = prefs
    self.battStatus = battStatus
    self.label = GTK_MOD.GTK.Label("<?>")
    self.batt0img = GTK_MOD.GTK.Image()
    self.batt1img = GTK_MOD.GTK.Image()
    self.counter = 0
    self.orientation = orientation
    self.pixbufSize = None

    self.container = GTK_MOD.GTK.HBox()
    self.box = None
    self.resetLayout()

    self.guiPrefs = None
  def getGtkWidget(self):
    return self.container
  def resetLayout(self):
    if self.box != None:
      self.container.remove(self.box)

    if self.isVertical():
      self.box = GTK_MOD.GTK.VBox()
    else:
      self.box = GTK_MOD.GTK.HBox()

    self.box.add(self.batt0img)
    self.box.add(self.label)
    self.box.add(self.batt1img)

    self.container.add(self.box)
    self.container.show_all()

  def parseSize(self, size):
    size = re.match('^(\\d+)x(\\d+)$', size)
    if size != None:
      return(int(size.group(1)), int(size.group(2)))
    else:
      return (36, 36)
  def initPixbufs(self, size):
    (w, h) = self.parseSize(size)
    self.none = self.newPixbuf(w, h, 'none.svg')
    self.idle = []
    self.charging = []
    self.discharging = []
    for i in [0,10,20,30,40,50,60,70,80,90,100]:
      img = str(i) + '.svg'
      self.idle.append(self.newPixbuf(w, h, 'idle/' + img))
      self.charging.append(self.newPixbuf(w, h, 'charging/' + img))
      self.discharging.append(self.newPixbuf(w, h, 'discharging/' + img))

  def newPixbuf(self, w, h, filename):
    return GTK_MOD.PIXBUF_MOD_NEW_FCT(
      IMAGE_DIR + '/' + filename, w, h)
  def selectPixbufByBattId(self, batt_id):
    battInfo = self.battStatus.getBattInfo(batt_id)
    return self.selectPixbuf(battInfo.isInstalled(), battInfo.state,
      int(float(battInfo.remaining_percent)))
  def selectPixbuf(self, installed, state, percent):
    if not installed:
      return self.none

    if state == State.CHARGING:
      imgs = self.charging
    elif state == State.DISCHARGING:
      imgs = self.discharging
    else:
      imgs = self.idle

    i = int(percent / 10)
    if i < 0 or len(imgs) <= 0:
      return self.none
    elif i >= len(imgs):
      return imgs[len(imgs)-1]
    else:
      return imgs[i]
  def updateImages(self):
    size = self.prefs['iconSize']
    if self.pixbufSize == None or self.pixbufSize != size:
      self.initPixbufs(size)
      self.pixbufSize = size

    if self.prefs['displayIcons']:
      if self.prefs['displayOnlyOneIcon']:
        installed = self.battStatus.isEitherInstalled()
        percent = self.battStatus.getTotalRemainingPercent()
        if self.battStatus.isEitherCharging():
          state = State.CHARGING
        elif self.battStatus.isEitherDischarging():
          state = State.DISCHARGING
        else:
          state = State.IDLE
        self.batt0img.set_from_pixbuf(
          self.selectPixbuf(installed, state, percent))
        self.batt0img.set_child_visible(True)
        self.batt1img.set_child_visible(False)
      else:
        self.batt0img.set_from_pixbuf(self.selectPixbufByBattId(0))
        self.batt1img.set_from_pixbuf(self.selectPixbufByBattId(1))
        self.batt0img.set_child_visible(True)
        self.batt1img.set_child_visible(True)
    else:
      self.batt0img.set_child_visible(False)
      self.batt1img.set_child_visible(False)

  def getBattMarkup(self, batt_id):
    battInfo = self.battStatus.getBattInfo(batt_id)
    if not battInfo.isInstalled():
      return '<span size="small">X</span>'
    percent = battInfo.remaining_percent

    if percent == '100':
      size = ' size="xx-small" '
    else:
      size = ' size="small" '

    if not self.prefs['displayColoredText'] or battInfo.state == State.IDLE:
      color = ''
    elif battInfo.state == State.CHARGING:
      color = ' foreground="#60FF60" '
    elif battInfo.state == State.DISCHARGING:
      color = ' foreground="#FF6060" '

    return '<b><span' + size + color + '>' + percent + '</span></b>'
  def getSeparatorMarkup(self):
    if self.prefs['displayBlinkingIndicator'] and self.counter % 2 == 0:
      color = ' foreground="blue" '
    else:
      color = ''

    sep = '<span size="x-small"' + color + '>|</span>'
    if self.isVertical():
      return sep + '\n'
    else:
      return sep
  def isVertical(self):
    return self.orientation == "vertical"
  def getPowerMarkup(self):
    powW = self.battStatus.getPowerDisplay()
    return '\n<span size="xx-small">' + powW + '</span>'
  def updateLabel(self):
    self.label.set_markup(
      self.getBattMarkup(0) +
      self.getSeparatorMarkup() +
      self.getBattMarkup(1) +
      self.getPowerMarkup())

  def update(self):
    self.counter = self.counter + 1
    self.updateImages()
    self.updateLabel()

  def ensurePreferencesDialog(self):
    if self.guiPrefs == None or self.guiPrefs.get_window() == None:
      self.guiPrefs = GuiPrefs(self.prefs)
      self.prefsDialog = GTK_MOD.GTK.Window(GTK_MOD.WINDOW_TOPLEVEL)
      self.prefsDialog.set_title('TPBattStat Preferences')
      self.prefsDialog.add(self.guiPrefs)
    self.guiPrefs.update()
  def getPreferencesDialog(self):
    self.ensurePreferencesDialog()
    return self.prefsDialog
  def showPreferencesDialog(self, *arguments, **keywords):
    self.getPreferencesDialog().show_all()

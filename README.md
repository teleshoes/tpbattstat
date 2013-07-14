[![Flattr this git repo](http://api.flattr.com/button/flattr-badge-large.png)](https://flattr.com/submit/auto?user_id=wolke&url=https://github.com/teleshoes/tpbattstat&title=tpbattstat&language=en_GB&tags=github&category=software) 

````
Copyright 2011,2013 Elliot Wolk
This project is licensed under the GPLv3. See COPYING for details.


TPBattStat runs in a standalone gtk window, outputs JSON markup,
or dzen2 markup.

It incorporates tp_smapi and tpacpi-bat, which provide access to certain
battery controls on Lenovo/IBM ThinkPads.
TPBattStat provides:
 -smart battery balancing
 -percent remaining, image meters, charge/discharge current
 -configurable graphical display
 -led controls


Requires:
tp_smapi
  see: http://www.thinkwiki.org/wiki/Tp_smapi#Installation_from_source
       the ubuntu installation script should take care of this for most users.

For led controls, you need to have the thinkpad_acpi module.
To install led controls, run ./led-controls/install.sh
This copies the two perl execs and adds setuid to led.

In case anyone feels overwhelmed with an urge to thank me:
https://flattr.com/thing/289178/ThinkPad-Battery-Status-Applet
```

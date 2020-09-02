import sys

class GTK_MOD():
  PYTHON2 = sys.version_info < (3, 0)
  PYTHON3 = sys.version_info >= (3, 0)

  GTK = None
  GDK = None
  BUTTON_PRESS_MASK = None
  WINDOW_TOPLEVEL = None
  PIXBUF_MOD_NEW_FCT = None
  TIMEOUT_ADD_FCT = None

  if PYTHON2:
    import gtk
    import gobject

    GTK = gtk
    GDK = gtk.gdk
    BUTTON_PRESS_MASK = gtk.gdk.BUTTON_PRESS_MASK
    WINDOW_TOPLEVEL = gtk.WINDOW_TOPLEVEL
    STATE_NORMAL = gtk.STATE_NORMAL
    PIXBUF_MOD_NEW_FCT = gtk.gdk.pixbuf_new_from_file_at_size
    TIMEOUT_ADD_FCT = gobject.timeout_add
    NEW_COMBO_BOX_FCT = gtk.combo_box_new_text

  if PYTHON3:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

    GTK = Gtk
    GDK = Gdk
    BUTTON_PRESS_MASK = Gdk.EventMask.BUTTON_PRESS_MASK
    WINDOW_TOPLEVEL = Gtk.WindowType.TOPLEVEL
    STATE_NORMAL = Gtk.StateFlags.NORMAL
    PIXBUF_MOD_NEW_FCT = GdkPixbuf.Pixbuf.new_from_file_at_size
    TIMEOUT_ADD_FCT = GLib.timeout_add
    NEW_COMBO_BOX_FCT = Gtk.ComboBoxText

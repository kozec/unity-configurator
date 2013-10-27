#!/usr/bin/env python2

"""
Universal Unity (engine) Configurator
Copyright (C) 2013 Kozec

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

HELP = """
Usage:
  %(exe)s [-h|--help]
  %(exe)s [-f] config_location
Searchs for configuration files of unity-based applications and lets    
user to configure their graphics settings

  config_location  specify this parameter to run in single app mode. In
                   this mode, application list is not shown and only
                   settings for specified application are presented
  -h, --help       displays this help screen
  -f               creates default pref file, if it doesn't already
                   exists in config_location
""".strip("\n")

APP_NAME = "Universal Unity (engine) Configurator"
APP_NAME_SHORT = "UUC"

import os, sys, thread
from threading import Thread
from subprocess import Popen, PIPE
from xml.etree import ElementTree
# Imports GTK, little down after display_error definition

XRANDR = "/usr/bin/xrandr"
DEFAULT_CONFIG = """
<unity_prefs version_major="1" version_minor="0">
	<pref name="Screenmanager Resolution Width" type="int">800</pref>
	<pref name="Screenmanager Resolution Height" type="int">600</pref>
	<pref name="Screenmanager Is Fullscreen mode" type="int">0</pref>
</unity_prefs>
"""

def display_error(message):
	"""
	Displays error message using most common tools for doing so in
	user-friendly way and falls back to old-fashioned console if there
	is no too available.
	"""
	is_exec = lambda x : os.path.isfile(x) and os.access(x, os.X_OK)
	if is_exec("/usr/bin/yad") :
		Popen(['/usr/bin/yad', '--title', 'Error', '--image=error', '--button=Ok', '--text', message]).communicate()
	elif is_exec("/usr/bin/zenity") :
		Popen(['/usr/bin/zenity', '--error', '--text', message])
	elif is_exec("/usr/bin/kdialog") :
		Popen(['/usr/bin/kdialog', '--error', message])
	elif is_exec("/usr/bin/Xdialog") :
		Popen(['/usr/bin/Xdialog', '--msgbox', message, '10', '100'])
	elif is_exec("/usr/bin/gdialog") :
		Popen(['/usr/bin/gdialog', '--msgbox', message])
	print >>sys.stderr, message

try:
	import gtk, pango
except ImportError:
	display_error("GTK2 bindings for python not found. Please, use your package manager to install pygtk package")
	sys.exit(1)
_ = lambda x : x

class App(gtk.Window):
	""" Main window / application interface """
	def __init__(self):
		gtk.Window.__init__(self)
		self.set_title(_(APP_NAME))
		self.set_position(gtk.WIN_POS_CENTER)
		self.config_data = None
		# Containers
		vb = gtk.VBox()
		sw = gtk.ScrolledWindow()
		hb = gtk.HBox()
		tab = gtk.Table()
		bb = gtk.HBox()
		
		# Labels
		self.lb_pick_game  = BoldLabel(_("Pick a game from list:"))
		self.lb_resolution = BoldLabel(_("Screen resolution"))
		self.lb_custom_res = BoldLabel(_("Custom resolution"))
		self.lb_custom_w   = BoldLabel("<span color='red'>%s</span>" % _("Warning: Using custom fullscreen resolution may make \n your screen unusable or even crash your desktop."))
		self.lb_game_info  = BoldLabel(_("Game info"))
		self.lb_x = gtk.Label("x")
		
		# Usable stuff
		self.lv = gtk.TreeView()
		self.setup_listview(self.lv)
		self.but_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		self.but_save = gtk.Button(stock=gtk.STOCK_SAVE)
		self.but_save.set_sensitive(False)
		self.resolution = gtk.combo_box_new_text()
		self.resolution_w = gtk.Entry()
		self.resolution_h = gtk.Entry()
		self.fullscreen = gtk.CheckButton(_("Fullscreen"))
		self.game_info  = gtk.Label(_("(select something)"))
		self.game_info.set_alignment(0, 0)
		self.link = gtk.LinkButton("file:///")
		self.link.set_alignment(0, 0)
		
		# Connect signals
		self.connect("destroy", gtk.main_quit)
		self.but_close.connect("clicked", gtk.main_quit)
		self.but_save.connect("clicked", self.on_save)
		self.lv.connect("cursor-changed", self.on_game_selected)
		self.resolution.connect("changed", self.on_resolution_changed)
		self.resolution_w.connect("changed", self.on_custom_res_changed)
		self.resolution_h.connect("changed", self.on_custom_res_changed)
		self.fullscreen.connect("toggled", self.on_fullscreen_changed)
		
		# Pack it together
		self.but_close.set_size_request(100, 30)
		self.but_save.set_size_request(100, 30)
		bb.pack_end(self.but_save, False, True)
		bb.pack_end(self.but_close, False, True)
		sw.add(self.lv)
		sw.set_size_request(300, 200)
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		tab.attach(sw, 0, 1, 1, 12)
		tab.attach(self.lb_pick_game,	0, 1, 0, 1,  yoptions=gtk.FILL, xpadding=5)
		tab.attach(self.lb_resolution,	1, 3, 1, 2,  xoptions=gtk.EXPAND|gtk.FILL, yoptions=0, xpadding=10)
		tab.attach(self.resolution,		1, 5, 2, 3,  yoptions=0, xpadding=30)
		tab.attach(self.fullscreen,		1, 5, 4, 5,  yoptions=0, xpadding=30)
		tab.attach(self.lb_custom_res,	1, 5, 5, 6,  yoptions=0, xpadding=10)
		tab.attach(self.resolution_w,	1, 2, 6, 7,  yoptions=0, xpadding=30)
		tab.attach(self.lb_x,			2, 3, 6, 7,  xoptions=0, yoptions=0, xpadding=2)
		tab.attach(self.resolution_h,	4, 5, 6, 7,  yoptions=0, xpadding=30)
		tab.attach(self.lb_custom_w,	1, 5, 7, 8,  yoptions=0, xpadding=30)
		tab.attach(self.lb_game_info,	1, 5, 8, 9,  yoptions=0, xpadding=10)
		tab.attach(self.game_info,		1, 5, 9, 10,  xoptions=gtk.EXPAND|gtk.FILL, yoptions=0, xpadding=30)
		tab.attach(self.link,			1, 5, 10, 11,  xoptions=gtk.EXPAND|gtk.FILL, yoptions=0, xpadding=30)
		tab.attach(gtk.Label(""),		1, 5, 11, 12, xoptions=gtk.EXPAND, yoptions=gtk.EXPAND)
		vb.pack_start(tab, True, True, 3)
		vb.pack_end(bb, False, True, 3)
		vb.set_border_width(5)
		self.add(vb)
		self.show_all()
		self.lb_custom_w.set_visible(False)
		self.set_settings_enabled(False)
		self.set_custom_res_enabled(False)
	
	def set_game_list_enabled(self, e):
		""" Enables/Disables list of games on left side of window """
		for x in ( self.lb_pick_game, self.lv.get_parent()):
			x.set_visible(e)
	
	def set_settings_enabled(self, e):
		""" Enables/Disables list of options on right side of window """
		for x in ( self.lb_resolution,  self.resolution, self.fullscreen, self.game_info, self.lb_game_info, self.lb_x, self.link ):
			x.set_sensitive(e)
	
	def set_custom_res_enabled(self, v):
		""" Enables/Disables custom resolution fields """
		for x in ( self.lb_custom_res, self.resolution_w, self.resolution_h, self.lb_x):
			x.set_sensitive(v)

	def setup_listview(self, lv):
		""" Setups... well, listview. That's that gamelist on left side """
		lv.set_model(gtk.ListStore(str, str, str))	# config, name, company
		r = gtk.CellRendererText()
		col = gtk.TreeViewColumn("Game", r, text=1)
		lv.append_column(col)
		lv.set_headers_visible(False)
		lv.set_search_column(1)
	
	def is_custom_res(self):
		""" Returns True if resolution is set to custom """
		return self.resolution.get_active_text() == _("custom")
	
	def set_resolutions(self, rlist):
		""" Called from another thread when list of available resolutions is determined """
		gtk.threads_enter()
		if len(rlist) == 0:
			self.resolution.append_text("%sx%s" % (gtk.gdk.screen_width(), gtk.gdk.screen_height()))
		else:
			for x in rlist:
				self.resolution.append_text(x)
		self.resolution.append_text(_("custom"))
		self.resolution.set_active(0)
		self.set_settings_enabled(False)
		self.but_save.set_sensitive(False)
		gtk.threads_leave()
	
	def add_game(self, config, name, company):
		""" Called from another thread for every game found """
		gtk.threads_enter()
		self.lv.get_model().append((config, name, company))
		gtk.threads_leave()
	
	def load_config(self, filename):
		""" Loads game configuration from specified file """
		try:
			tree = ElementTree.parse(filename)
		except Exception, e:
			self.set_settings_enabled(False)
			self.set_custom_res_enabled(False)
			md = gtk.MessageDialog(self, 
				gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
				gtk.BUTTONS_CLOSE, _("Failed to parse game configuration") + "\n" + str(e))
			md.run()
			md.destroy()
			return
		self.config_data = (filename, tree)
		res_w = 0
		res_h = 0
		for child in tree.getroot():
			try:
				if child.tag == "pref" and "name" in child.attrib:
					if child.attrib["name"] == "Screenmanager Is Fullscreen mode":
						self.fullscreen.set_active(child.text.strip(" \t\r\n") != "0")
					elif child.attrib["name"] == "Screenmanager Resolution Height":
						res_h = int(child.text.strip(" \t\r\n"))
					elif child.attrib["name"] == "Screenmanager Resolution Width":
						res_w = int(child.text.strip(" \t\r\n"))
			except Exception:
				continue
		if res_w == 0 or res_h == 0:
			# Resolution is not set, fallback to screen resolution
			self.resolution.set_active(0)
			self.set_custom_res_enabled(False)
		else:
			model = self.resolution.get_model()
			res = "%sx%s" % (res_w, res_h)
			index = 0
			found = False
			for i in model:
				if i[0] == res:
					self.resolution.set_active(index)
					self.set_custom_res_enabled(False)
					found = True
					break
				index += 1
			if not found:
				self.resolution.set_active(len(model) - 1)
				self.set_custom_res_enabled(True)
				self.resolution_w.set_text(str(res_w))
				self.resolution_h.set_text(str(res_h))
		self.but_save.set_sensitive(False)
		self.set_settings_enabled(True)
	
	def save_config(self, filename, tree):
		""" Saves game configuration. Tree parameter should contain previously parsed XML data """
		def build_element(tag, text, **rest):
			""" Used only to save some lines """
			e = ElementTree.Element(tag, **rest)
			e.text = text
			e.tail = "\n\t"
			return e
		filename, tree = self.config_data
		root = tree.getroot()
		# Remove values to be overwritten
		removing = True
		while removing:
			removing = False
			for child in root:
				if child.tag == "pref" and "name" in child.attrib:
					if child.attrib["name"] in ("Screenmanager Is Fullscreen mode",
							"Screenmanager Resolution Height", "Screenmanager Resolution Width"):
						root.remove(child)
						removing = True
						break
		# Add new values
		root.append(build_element("pref", "1" if self.fullscreen.get_active() else "0", name="Screenmanager Is Fullscreen mode", type="int"))
		res = self.resolution.get_active_text()
		if self.is_custom_res():
			root.append(build_element("pref", self.resolution_w.get_text(), name="Screenmanager Resolution Width", type="int"))
			root.append(build_element("pref", self.resolution_h.get_text(), name="Screenmanager Resolution Height", type="int"))
		else:
			root.append(build_element("pref", res.split("x")[0], name="Screenmanager Resolution Width", type="int"))
			root.append(build_element("pref", res.split("x")[1], name="Screenmanager Resolution Height", type="int"))
		# Write XML file
		try:
			tree.write(filename)
		except Exception, e:
			self.set_settings_enabled(False)
			self.set_custom_res_enabled(False)
			md = gtk.MessageDialog(self, 
				gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
				gtk.BUTTONS_CLOSE, _("Failed to write game configuration") + "\n" + str(e))
			md.run()
			md.destroy()
		self.but_save.set_sensitive(False)
	
	def on_resolution_changed(self, cb):
		""" Called when value in resolution combobox gets changed """
		if self.is_custom_res():
			self.set_custom_res_enabled(True)
			if self.resolution_h.get_text().strip() == "" or self.resolution_w.get_text().strip() == "":
				self.resolution_h.set_text(cb.get_model()[0][0].split("x")[0])
				self.resolution_w.set_text(cb.get_model()[0][0].split("x")[1])
		else:
			self.set_custom_res_enabled(False)
		self.but_save.set_sensitive(True)
		self.lb_custom_w.set_visible( self.is_custom_res() and self.fullscreen.get_active() )
	
	def on_fullscreen_changed(self, *a):
		""" Called fullscreen combobox is toggled """
		self.but_save.set_sensitive(True)
		self.lb_custom_w.set_visible( self.is_custom_res() and self.fullscreen.get_active() )
	
	def on_custom_res_changed(self, ibox):
		""" Called when value in either custom resolution inputbox gets changed """
		ibox.set_text( "".join([ c for c in list(ibox.get_text()) if c in "1234567890" ]) )
		self.but_save.set_sensitive(True)
	
	def on_save(self, *a):
		""" Called when user clicks on Save button """
		if self.config_data:
			self.save_config(*self.config_data)
	
	def on_game_selected(self, lv):
		""" Called when user clicks in game list """
		model, it = lv.get_selection().get_selected()
		try:
			config, game, company = model[it]
		except Exception:
			return
		self.load_config(config)
		self.set_game_info(config, game, company)
	
	def set_game_info(self, config, game, company):
		""" Sets values in game info screen """
		self.game_info.set_text("%s by %s\n%s" % (game, company, _("Configuration is stored in:")))
		config_dir = os.path.split(config)[0]
		self.link.set_uri("file://%s" % config_dir)
		if config_dir.startswith(os.path.expanduser("~")):
			config_dir = "~" + config_dir[len(os.path.expanduser("~")):]
		self.link.set_label(config_dir)
	
class BoldLabel(gtk.Label):
	""" Left-aligned label with bold text """
	def __init__(self, text):
		gtk.Label.__init__(self)
		self.set_markup("<b>%s</b>" % text)
		self.set_alignment(0, 0)

def populate_resolution_combo(app):
	""" Uses xrandr utility to loads list of resolutions available for primary display """
	if not os.path.exists(XRANDR):
		print >>sys.stderr, "Warning: xrandr utility not found. Only current desktop resolution will be available"
		app.set_resolutions([])
		return
	xr_data = Popen([XRANDR], stdout=PIPE).communicate()[0].split("\n")
	try:
		out = [ x for x in xr_data if "primary" in x ]
		if len(out) == 0: out = [ x for x in xr_data if "connected" in x ]
		primary = out[0].split(" ")[0]
		print "Found primary display:", primary
	except Exception, e:
		print >>sys.stderr, "Warning: Failed to determine primary display. Only current desktop resolution will be available"
		app.set_resolutions([])
		return
	appends = False
	r_list = []
	for x in xr_data:
		if appends:
			if not x.startswith("  "):
				break
			try:
				res = x.strip().split(" ")[0]
			except Exception:
				continue
			print "Found resolution:", res
			r_list.append(res)
		if x.startswith(primary):
			appends = True
	app.set_resolutions(r_list)

def search_for_configs(app):
	""" Searchs for config files in known locations """
	configs = Popen(["find", os.path.expanduser("~/.config/unity3d"), "-iname", "prefs"], stdout=PIPE).communicate()[0].split("\n")
	configs.sort(key=lambda c : c.split(os.path.sep)[-2] if len(c.split(os.path.sep)) > 2 else "" )
	for x in configs:
		try:
			company = x.split(os.path.sep)[-3]
			game = x.split(os.path.sep)[-2]
		except Exception:
			continue
		app.add_game(x, game, company)

if __name__ == "__main__":
	# Parse arguments
	# -f, -h and --help are recognized; Anything else is considered to be config location
	if len(sys.argv) <= 1:
		gtk.threads_init()
		a = App()
		a.show()
		thread.start_new_thread(populate_resolution_combo, (a,))
		thread.start_new_thread(search_for_configs, (a,))
		gtk.main()
	elif sys.argv[1] in ("-h", "--help"):
		# Display help and exit
		print HELP % {'exe' : sys.argv[0]}
	else:
		# Check for -f parameter
		create = False
		if sys.argv[1] == "-f":
			sys.argv.remove("-f")
			create = True
		# Determine if config_location points to configuration directory or configuration file
		config_dir = sys.argv[1]
		if config_dir.endswith(os.path.sep + "prefs"):
			config = config_dir
			config_dir = os.path.split(config_dir)[0]
		else:
			config = os.path.join(config_dir, "prefs")
		# Check if configuration file already exists
		if not os.path.exists(config):
			if create:
				# Create new configuration if requested...
				print "Creating default configuration in", config_dir
				try:
					os.makedirs(config_dir)
				except Exception:
					pass
				try:
					file(config, "w").write(DEFAULT_CONFIG)
				except Exception, e:
					print >>sys.stderr, e
					sys.exit(1)
			else:
				# Fail miserably otherwise
				print >>sys.stderr, "Specified path is not unity configuration file nor configuration directory"
				sys.exit(-1)

		# Prepare UI and GTK
		gtk.threads_init()
		a = App()
		# Get list of available resolutions
		t = Thread(target=populate_resolution_combo, args=(a,))
		t.start()
		t.join()
		# Load configuration
		print "Loading configuration file", config
		company = config.split(os.path.sep)[-3]
		game = config.split(os.path.sep)[-2]
		a.load_config(config)
		a.set_game_info(config, game, company)
		# Setup and show window
		a.set_game_list_enabled(False)
		a.set_title("%s: %s" % (_(APP_NAME_SHORT), game))
		a.show()
		# GTK mainloop
		gtk.main()

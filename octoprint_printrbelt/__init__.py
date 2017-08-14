# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

class PrintrbeltPlugin(octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.TemplatePlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			# put your plugin's default settings here
		)

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/printrbelt.js"],
			css=["css/printrbelt.css"],
			less=["less/printrbelt.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			printrbelt=dict(
				displayName="Printrbelt Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="markwal",
				repo="OctoPrint-PrintrBelt",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/markwal/OctoPrint-PrintrBelt/archive/{target_version}.zip"
			)
		)

class GcodeShifter(octoprint.filemanager.util.LineProcessorStream):
	def __init__(self):
		super
		self.process_line = process_first_line

	def process_first_line(self, line):
		if "tilted-bed" in line:
			self.process_line = pass_through_line
			return line
		self.process_line = shift_line
		return "# gcode modified by tilted-bed preprocessor\r\n" + line

	def shift_line(self, line):
		pass

	def pass_through_line(self, line):
		return line

def shift_and_skew(path, file_object, links=None, printer_profile=None, allow_overwrite=True, *args, *kwargs):
	if not octoprint.filemanager.valid_file_type(path, type="gcode"):
		return file_object

	return octoprint.filemanager.util.StreamWrapper(file_object.filename, GcodeShifter(file_object.stream()))

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Printrbelt Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PrintrbeltPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.filemanager.preprocessor": shift_and_skew
	}


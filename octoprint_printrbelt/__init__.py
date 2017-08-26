# coding=utf-8
from __future__ import absolute_import

import os
import os.path

import octoprint.plugin

class PrintrbeltPlugin(octoprint.plugin.SlicerPlugin,
		octoprint.plugin.StartupPlugin,
		octoprint.plugin.SettingsPlugin,
		octoprint.plugin.AssetPlugin,
		octoprint.plugin.TemplatePlugin):

	def __init__(self, *args, **kwargs):
		self._slicer = None

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
		)

	##~~ AssetPlugin mixin

	def get_assets(self):
		return dict(
			js=["js/printrbelt.js"],
			css=["css/printrbelt.css"],
			less=["less/printrbelt.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
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

	##~~ SlicerPlugin mixin

	def is_slicer_configured(self):
		return self._slicer and self._slicer.is_slicer_configured()

	def get_slicer_properties(self):
		return dict(
			type="printrbelt-cura",
			name="PrintrBelt-CuraEngine",
			same_device=True,
			progress_report=True,
			source_file_types=["stl"],
			destination_extensions=["gco", "gcode", "g"]
		)

	def get_slicer_default_profile(self):
		if not self._slicer:
			return None
		return self._slicer.get_slicer_default_profile()

	def get_slicer_profile(self, path):
		if not self._slicer:
			return None
		return self._slicer.get_slicer_profile(path)

	def save_slicer_profile(self, *args, **kwargs):
		if not self._slicer:
			return None
		return self._slicer.save_slicer_profile(*args, **kwargs)

	def do_slice(self, model_path, printer_profile, machinecode_path=None, profile_path=None, position=None,
	             on_progress=None, on_progress_args=None, on_progress_kwargs=None):
		if not self._slicer:
			return None
		return self._slicer.do_slice(model_path, printer_profile, machinecode_path=machinecode_path, profile_path=profile_path, position=position,
				on_progress=on_progress, on_progress_args=on_progress_args, on_progress_kwargs=on_progress_kwargs)

	def cancel_slicing(self, machinecode_path):
		if not self._slicer:
			return None
		return self._slicer.cancel_slicing(machinecode_path)

	##~~ StartupPlugin

	def on_after_startup(self, *args, **kwargs):
		if self._settings.get(['verbose']):
			self._logger.setLevel(logging.DEBUG)
		self._logger.debug("on_after_startup")
		self._slicer = self._slicing_manager.get_slicer('cura', require_configured=False)


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


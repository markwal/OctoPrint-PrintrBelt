# coding=utf-8
from __future__ import absolute_import

__author__ = "Mark Walker (markwal@hotmail.com)"
__license__ = "GNU General Public License v2 http://www.gnu.org/licenses/gpl-2.0.html"
__copyright__ = "Copyright (C) 2017 Mark Walker"

"""
    This file is part of OctoPrint-PrintrBelt.

	OctoPrint-PrintrBelt is free software; you can redistribute it and/or
	modify it under the terms of the GNU General Public License
	as published by the Free Software Foundation; either version 2
	of the License, or (at your option) any later version.

	OctoPrint-PrintrBelt is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with OctoPrint-PrintrBelt.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import os.path
import math

import octoprint.plugin
from octoprint.slicing import TemporaryProfile


#-----------------------------------------------------------------------------
# --islink--
# os.path.islink always returns False on Windows in python 2
# should be able to remove this and call os.path.islink directly if OctoPrint
# ever upgrades to python 3
def islink(path):
	if os.name == 'nt':
		import ctypes
		FILE_ATTRIBUTE_REPARSE_POINT = 0x400
		return os.path.isdir(path) and (ctypes.windll.kernel32.GetFileAttributesW(unicode(path)))

	return os.path.islink(path)


#-----------------------------------------------------------------------------
# --main plugin class--
#
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
			belt_angle = 35.0
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
		return self._slicer.get_slicer_default_profile()

	def get_slicer_profile(self, path):
		return self._slicer.get_slicer_profile(path)

	def save_slicer_profile(self, *args, **kwargs):
		return self._slicer.save_slicer_profile(*args, **kwargs)

	def do_slice(self, model_path, printer_profile, machinecode_path=None, profile_path=None, position=None,
	             on_progress=None, on_progress_args=None, on_progress_kwargs=None):
		try:
			angle = self._settings.get_float(['belt_angle'])
			if angle != 0.0:
				overrides = {
					'stl_transformation_matrix': [[0,0,-math.cos(math.radians(angle))],[0,1,0],[1+math.tan(math.radians(angle)),0,1]],
					'object_sink': 0.3 * math.cos(angle),
					'skirt_line_count': 0,
					'brim_line_count': 0,
					'support': "none",
					'platform_adhesion': "none"
				}
			else:
				overrides = None
			self._logger.info("with _temporary")
			with self._temporary_profile(profile_path, overrides=overrides) as temp_profile_path:
				self._logger.info("do_slice")
				return self._slicer.do_slice(model_path, printer_profile,
						machinecode_path=machinecode_path,
						profile_path=temp_profile_path, position=position,
						on_progress=on_progress, on_progress_args=on_progress_args,
						on_progress_kwargs=on_progress_kwargs)
		except:
			self._logger.exception("do_slice")

	def _temporary_profile(self, path, overrides):
		self._logger.info("load_profile_from_path")
		profile = self._slicing_manager._load_profile_from_path('cura', path)
		self._logger.info("TemporaryProfile")
		return TemporaryProfile(self._slicer.save_slicer_profile, profile, overrides=overrides)

	def cancel_slicing(self, machinecode_path):
		return self._slicer.cancel_slicing(machinecode_path)

	##~~ StartupPlugin

	def on_after_startup(self, *args, **kwargs):
		if self._settings.get(['verbose']):
			self._logger.setLevel(logging.DEBUG)
		self._logger.debug("on_after_startup")
		self._slicer = self._slicing_manager.get_slicer('cura', require_configured=False)
		profile_folder = self._slicing_manager.get_slicer_profile_path('printrbelt-cura')
		if os.path.exists(profile_folder):
			if islink(profile_folder):
				return
			if len(os.listdir(profile_folder)) > 0:
				os.rename(profile_folder, profile_folder + "_old")
			else:
				os.rmdir(profile_folder)
		if hasattr(os, 'symlink'):
			os.symlink(self._slicing_manager.get_slicer_profile_path('cura'), profile_folder)
		elif os.name == 'nt':
			os.system('mklink /D "{0}" "{1}"'.format(profile_folder,self._slicing_manager.get_slicer_profile_path('cura')))
		else:
			self._logger.error("Unable to create symlink for slicing profile folder")

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

def shift_and_skew(path, file_object, links=None, printer_profile=None, allow_overwrite=True, *args, **kwargs):
	if not octoprint.filemanager.valid_file_type(path, type="gcode"):
		return file_object

	return octoprint.filemanager.util.StreamWrapper(file_object.filename, GcodeShifter(file_object.stream()))

__plugin_name__ = "PrintrBelt"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PrintrbeltPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}


/*
 * View model for OctoPrint-PrintrBelt
 * Copyright (c) 2017 by Mark Walker
 *
 * Author: Mark Walker (markwal@hotmail.com)
 * License: GPLv2
 */
$(function() {
    function PrintrbeltViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        self.onBeforeBinding = function() {
            self.settings = self.settingsViewModel.settings.plugins.printrbelt;
            console.log(JSON.stringify(self.settings.plugins));
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        PrintrbeltViewModel,
        [ "settingsViewModel" ],
        [ "#settings_plugin_printrbelt" ]
    ]);
});

"""
An RV engine for Tank.
"""

import os
import tank
import inspect
import logging

from tank.platform import Engine
from tank import TankError

class RVEngine(Engine):

    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)
        self.toolkit_rv_mode_name = os.environ["TK_RV_MODE_NAME"]

        if self.context.project is None:
            # must have at least a project in the context to even start!
            raise tank.TankError("The engine needs at least a project in the context "
                                 "in order to start! Your context: %s" % self.context)

        # default menu name is Shotgun but this can be overriden
        # in the configuration to be Sgtk in case of conflicts
        self._menu_name = "Shotgun"
        if self.get_setting("use_sgtk_as_menu_name", False):
            self._menu_name = "SGTK"

        self._ui_enabled = True

    def pre_app_init(self):
        # This probably shouldn't be here but it helps the Toolkit tools to look
        # right but has the side effect of changing RV's look and feel.
        self._initialize_dark_look_and_feel()

    def post_app_init(self):
        """
        Called when all apps have initialized
        """

        # sets up sgtk menu
        if self.has_ui:
            tk_rv = self.import_module("tk_rv")
            self._menu_generator = tk_rv.MenuGenerator(self, self._menu_name)
            self._menu_generator.create_menu()

    def destroy_engine(self):
        self.log_debug("%s: Destroying..." % self)
        if self._ui_enabled:
            self._menu_generator.destroy_menu()

    @property
    def has_ui(self):
        """
        Should always be true.
        No terminal mode for RV and no interactive mode that doesn't have ui running.
        """
        return self._ui_enabled

    ##########################################################################################
    # logging interfaces

    def log_debug(self, msg):
        if self.get_setting("debug_logging", False):
            msg = "DEBUG: Shotgun - %s" % msg
            print msg

    def log_info(self, msg):
        msg = "INFO: Shotgun - %s" % msg
        print msg

    def log_warning(self, msg):
        msg = "WARNING: Shotgun - %s" % msg
        print msg

    def log_error(self, msg):
        msg = "ERROR: Shotgun - %s" % msg
        print msg

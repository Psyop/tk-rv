"""
Menu handling for RV

"""

import tank
import sys
import os
import unicodedata

from rv import commands

from tank.platform.qt import QtGui, QtCore

class MenuGenerator(object):
    """
    Menu generation functionality for RV
    """

    def __init__(self, engine, menu_name):
        self._engine = engine
        self._toolkit_rv_mode_name = engine.toolkit_rv_mode_name
        self._menu_name = menu_name

    ##########################################################################################
    # public methods

    def create_menu(self, *args):
        """
        Render the entire SGTK menu.
        """

        # handle used to hold list of menu items
        self._menu_handle = []

        # clear sgtk menu
        sgtk_menu = [(self._menu_name, [("_", None)])]
        commands.defineModeMenu(self._toolkit_rv_mode_name, sgtk_menu)

        # add context submenu
        self._context_menu = self._add_context_menu()
        self._menu_handle.append(self._context_menu)

        # add separator
        separator_item = ("_", None)
        self._menu_handle.append(separator_item)

        # create menu item for each command
        menu_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
            menu_items.append(AppCommand(cmd_name, cmd_details))

        # sort list of commands in name order
        menu_items.sort(key=lambda x: x.name)

        # add favourites to the menu
        for fav in self._engine.get_setting("menu_favourites", []):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            for cmd in menu_items:
                if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                    menu_item = cmd.define_menu_item()
                    self._menu_handle.append(menu_item)
                    cmd.favourite = True

        # add separator
        self._menu_handle.append(separator_item)

        # separate menu items out into various sections
        commands_by_app = {}
        for cmd in menu_items:
            if cmd.get_type() == "context_menu":
                menu_item = cmd.define_menu_item()
                self._context_menu[1].append(menu_item)
            else:
                app_name = cmd.get_app_name()
                if app_name is None:
                    app_name = "Other Items"
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                menu_item = cmd.define_menu_item()
                commands_by_app[app_name].append(menu_item)

        # add app-specific menus to the menu handle
        for menu_name, menu_items in commands_by_app.iteritems():
            self._menu_handle.append((menu_name, menu_items))

        # update sgtk menu
        sgtk_menu = [(self._menu_name, self._menu_handle)]
        commands.defineModeMenu(self._toolkit_rv_mode_name, sgtk_menu)

    def destroy_menu(self):
        """"
        Clears sgtk menu.
        """

        sgtk_menu = [("", [("_", None)])]
        commands.defineModeMenu(self._toolkit_rv_mode_name, sgtk_menu)

    ##########################################################################################
    # context menu and UI

    def _add_context_menu(self):
        """
        Returns a context menu which displays the current context
        """

        ctx = self._engine.context
        ctx_name = str(ctx)

        jump_shotgun_item = ("Jump To Shotgun", self._jump_to_sg, None, None)
        jump_file_sys_item = ("Jump To File System", self._jump_to_fs, None, None)
        separator_item = ("_", None, None, None)

        # create the menu
        ctx_menu = (ctx_name, [jump_shotgun_item, jump_file_sys_item, separator_item])

        return ctx_menu

    def _jump_to_sg(self, event):
        """
        Jump to shotgun, launch web browser
        """

        from tank.platform.qt import QtCore, QtGui
        url = self._engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _jump_to_fs(self, event):
        """
        Jump from context to FS
        """

        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations
        for disk_location in paths:

            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)

class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """

    def __init__(self, name, command_dict):
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False

    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None

    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine
        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                return app_instance_name

        return None

    def get_documentation_url_str(self):
        """
        Returns the documentation as a str
        """
        if "app" in self.properties:
            app = self.properties["app"]
            doc_url = app.documentation_url
            # deal with nuke's inability to handle unicode. #fail
            if doc_url.__class__ == unicode:
                doc_url = unicodedata.normalize('NFKD', doc_url).encode('ascii', 'ignore')
            return doc_url

        return None

    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")

    def define_menu_item(self):
        """
        Adds an app command to the menu item
        """

        hotkey = self.properties.get("hotkey")
        if hotkey:
            menu_item = (self.name, self.menu_item_callback, hotkey, None)
        else:
            menu_item = (self.name, self.menu_item_callback, None, None)

        return menu_item

    def menu_item_callback(self, event):
        self.callback()

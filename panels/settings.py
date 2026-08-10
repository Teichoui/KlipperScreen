import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ks_includes.functions import get_current_timezone, list_timezones, set_timezone
from ks_includes.screen_panel import ScreenPanel


class Panel(ScreenPanel):
    def __init__(self, screen, title):
        title = title or _("Settings")
        super().__init__(screen, title)
        self.printers = self.settings = self.langs = {}
        self.menu = ["settings_menu"]
        options = self._config.get_configurable_options().copy()
        options.append(
            {"printers": {"name": _("Printer Connections"), "type": "menu", "menu": "printers"}}
        )
        options.append({"lang": {"name": _("Language"), "type": "menu", "menu": "lang"}})
        tz_name = get_current_timezone() or _("Unknown")
        options.append(
            {
                "timezone": {
                    "name": _("Timezone") + f": {tz_name}",
                    "type": "button",
                    "callback": self.open_timezone_dialog,
                }
            }
        )
        self.labels["settings_menu"] = self._gtk.ScrolledWindow()
        self.labels["settings"] = Gtk.Grid()
        self.labels["settings_menu"].add(self.labels["settings"])
        for option in options:
            name = list(option)[0]
            self.add_option("settings", self.settings, name, option[name])

        self.labels["lang_menu"] = self._gtk.ScrolledWindow()
        self.labels["lang"] = Gtk.Grid()
        self.labels["lang_menu"].add(self.labels["lang"])
        for lang in ["system_lang", *self._config.lang_list]:
            self.langs[lang] = {
                "name": lang,
                "type": "button",
                "callback": self._screen.change_language,
            }
            self.add_option("lang", self.langs, lang, self.langs[lang])

        self.labels["printers_menu"] = self._gtk.ScrolledWindow()
        self.labels["printers"] = Gtk.Grid()
        self.labels["printers_menu"].add(self.labels["printers"])
        for printer in self._config.get_printers():
            pname = list(printer)[0]
            self.printers[pname] = {
                "name": pname,
                "section": f"printer {pname}",
                "type": "printer",
                "moonraker_host": printer[pname]["moonraker_host"],
                "moonraker_port": printer[pname]["moonraker_port"],
            }
            self.add_option("printers", self.printers, pname, self.printers[pname])

        self.content.add(self.labels["settings_menu"])

    def open_timezone_dialog(self, widget, name=None):
        timezones = list_timezones()
        if not timezones:
            self._screen.show_popup_message(_("Unable to retrieve timezone list"))
            return

        current = get_current_timezone()

        combo = Gtk.ComboBoxText()
        combo.set_hexpand(True)
        active_index = 0
        for i, tz in enumerate(timezones):
            combo.append_text(tz)
            if tz == current:
                active_index = i
        combo.set_active(active_index)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        label = Gtk.Label(label=_("Select your timezone"), wrap=True, hexpand=True)
        box.pack_start(label, False, False, 0)
        box.pack_start(combo, False, False, 0)

        buttons = [
            {"name": _("Set"), "response": Gtk.ResponseType.OK, "style": "dialog-info"},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL, "style": "dialog-error"},
        ]
        self._gtk.Dialog(_("Timezone"), buttons, box, self.timezone_dialog_response, combo)

    def timezone_dialog_response(self, dialog, response_id, combo):
        self._gtk.remove_dialog(dialog)
        if response_id != Gtk.ResponseType.OK:
            return
        tz = combo.get_active_text()
        if not tz:
            return
        ret, err = set_timezone(tz)
        if ret != 0:
            self._screen.show_popup_message(
                _("Failed to set timezone") + f": {err if err else f'exit code {ret}'}"
            )
            return
        self._screen.show_popup_message(_("Timezone set to") + f" {tz}", level=1)
        self._screen.panels_reinit.append("settings")

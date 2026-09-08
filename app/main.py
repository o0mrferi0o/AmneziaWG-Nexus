from __future__ import annotations
import threading
from pathlib import Path
from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from .core import ConnectionManager, StateManager
from .models import ConnectionDetails, ConnectionState, Profile
from .services import AWGService, discover_profiles

APP_ID = "io.github.mrf3ri.AmneziaWGNexus"

class NexusWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="AmneziaWG-Nexus", default_width=1080, default_height=720)
        self.state, self.service = StateManager(), AWGService()
        self.manager, self.profiles, self.refreshing = ConnectionManager(self.state, self.service), [], False
        self.set_content(self._build())
        self.reload_profiles(); self.refresh(); GLib.timeout_add_seconds(4, self._tick)
    def _build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, margin_top=24, margin_bottom=24, margin_start=28, margin_end=28)
        header = Gtk.Box(); title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        title.append(Gtk.Label(label="AMNEZIAWG-NEXUS", xalign=0, css_classes=["app-title"]))
        title.append(Gtk.Label(label="Secure VPN Manager", xalign=0, css_classes=["muted"]))
        header.append(title)
        refresh = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Refresh connection state")
        refresh.connect("clicked", lambda *_: self.refresh()); header.append(refresh)
        folder = Gtk.Button(icon_name="folder-open-symbolic", tooltip_text="Open Profiles Folder")
        folder.connect("clicked", self.open_folder); header.append(folder); root.append(header)
        self.status = Gtk.Label(xalign=0, css_classes=["status", "disconnected"]); root.append(self.status)
        self.profile_name = Gtk.Label(label="No profile selected", xalign=0, css_classes=["hero"]); root.append(self.profile_name)
        self.status_copy = Gtk.Label(xalign=0, css_classes=["muted"]); root.append(self.status_copy)
        self.action = Gtk.Button(label="Connect", css_classes=["suggested-action", "action"]); self.action.connect("clicked", self.toggle); root.append(self.action)
        grid = Gtk.Grid(column_spacing=20, hexpand=True, vexpand=True); root.append(grid)
        profiles_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, css_classes=["card"], hexpand=True, vexpand=True)
        profiles_card.append(Gtk.Label(label="PROFILES", xalign=0, css_classes=["section-title"]))
        self.search = Gtk.SearchEntry(placeholder_text="Search profiles…"); self.search.connect("search-changed", lambda *_: self.render_profiles()); profiles_card.append(self.search)
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, css_classes=["boxed-list"]); self.listbox.connect("row-selected", self.select_profile)
        scroll=Gtk.ScrolledWindow(vexpand=True, child=self.listbox); profiles_card.append(scroll); grid.attach(profiles_card,0,0,1,1)
        detail_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, css_classes=["card"], hexpand=True, vexpand=True)
        detail_card.append(Gtk.Label(label="CONNECTION DETAILS", xalign=0, css_classes=["section-title"]))
        self.details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); detail_card.append(self.details); grid.attach(detail_card,1,0,1,1)
        self.render_details(ConnectionDetails()); self.update_view(); return root
    def reload_profiles(self):
        self.profiles = discover_profiles(); self.render_profiles()
        if self.profiles and not self.state.active_profile: self.state.active_profile = self.profiles[0]
        self.update_view()
    def render_profiles(self):
        while (row := self.listbox.get_first_child()): self.listbox.remove(row)
        query = self.search.get_text().casefold()
        for profile in self.profiles:
            if query and query not in profile.name.casefold() and query not in profile.endpoint.casefold(): continue
            subtitle = "Invalid configuration" if not profile.valid else (profile.endpoint or "Available")
            icon = "dialog-warning-symbolic" if not profile.valid else "network-vpn-symbolic"
            row = Adw.ActionRow(title=profile.name, subtitle=subtitle); row.add_prefix(Gtk.Image(icon_name=icon)); row.profile=profile; self.listbox.append(row)
    def select_profile(self, _, row):
        if row: self.state.active_profile = row.profile; self.update_view()
    def toggle(self, *_):
        profile=self.state.active_profile
        if not profile: return
        worker = self.manager.disconnect if self.state.state == ConnectionState.CONNECTED else lambda: self.manager.connect(profile)
        threading.Thread(target=lambda: self._operate(worker), daemon=True).start()
    def _operate(self, operation):
        try: operation()
        except Exception as exc: self.state.state, self.state.error = ConnectionState.ERROR, "VPN operation failed" 
        GLib.idle_add(self.refresh)
    def refresh(self):
        if self.refreshing: return
        self.refreshing=True; threading.Thread(target=self._refresh_worker, daemon=True).start()
    def _refresh_worker(self):
        try:
            active=self.service.active_interfaces()
            profile=self.state.active_profile
            if self.state.state == ConnectionState.CONNECTED and (not profile or profile.interface not in active): self.state.state=ConnectionState.DISCONNECTED
            details=self.service.details(profile.interface) if profile and profile.interface in active else ConnectionDetails()
            if profile and profile.interface in active: details.public_ip=self.service.public_ip()
            GLib.idle_add(self._refreshed, details)
        finally: self.refreshing=False
    def _refreshed(self, details): self.render_details(details); self.update_view()
    def _tick(self): self.refresh(); return True
    def update_view(self):
        state=self.state.state; labels={ConnectionState.DISCONNECTED:"DISCONNECTED",ConnectionState.CONNECTING:"CONNECTING…",ConnectionState.CONNECTED:"CONNECTED",ConnectionState.DISCONNECTING:"DISCONNECTING…",ConnectionState.ERROR:"CONNECTION FAILED"}
        profile=self.state.active_profile; self.status.set_label("●  "+labels[state]); self.status.set_css_classes(["status", state.value])
        self.profile_name.set_label(profile.name if profile else "No profile selected")
        self.status_copy.set_label(self.state.error if state == ConnectionState.ERROR else ("Secure tunnel active" if state == ConnectionState.CONNECTED else "Select a validated profile to establish a secure tunnel"))
        self.action.set_label("Disconnect" if state==ConnectionState.CONNECTED else "Connect"); self.action.set_sensitive(bool(profile and profile.valid and state not in {ConnectionState.CONNECTING,ConnectionState.DISCONNECTING}))
    def render_details(self, d):
        while (child:=self.details.get_first_child()): self.details.remove(child)
        for label, value in [("Tunnel",d.tunnel_ip),("Endpoint",d.endpoint),("Handshake",d.handshake),("Download",format_bytes(d.rx)),("Upload",format_bytes(d.tx)),("Public IPv4",d.public_ip),("Allowed IPs",d.allowed_ips)]:
            row=Gtk.Box(); row.append(Gtk.Label(label=label, xalign=0, hexpand=True, css_classes=["muted"])); row.append(Gtk.Label(label=value, xalign=1, selectable=True)); self.details.append(row)
    def open_folder(self, *_): Gio.AppInfo.launch_default_for_uri("file:///etc/amnezia", None)

def format_bytes(value):
    for unit in ("B","KiB","MiB","GiB"):
        if value < 1024 or unit=="GiB": return f"{value:.1f} {unit}" if unit != "B" else f"{value} B"
        value/=1024

class NexusApplication(Adw.Application):
    def __init__(self): super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
    def do_startup(self):
        Adw.Application.do_startup(self)
        load_css()
    def do_activate(self):
        win=self.props.active_window or NexusWindow(self); win.present()

def load_css():
    provider=Gtk.CssProvider(); provider.load_from_path(str(Path(__file__).parent.parent/"assets/styles/main.css")); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
def main():
    app=NexusApplication(); return app.run(None)

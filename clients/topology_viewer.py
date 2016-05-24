#!/usr/bin/env python3

import os
import sys
sys.path.append("/usr/share/xdot") # Debian bug in xdot packaging. cf http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=679532
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

try:
    import xdot
except ImportError:
    print("You need xdot to run the topology viewer.\n"
          "On Debian/Ubuntu, apt-get install xdot.")
    sys.exit(1)

import logging; logger = logging.getLogger("underworlds.topology_viewer")
logging.basicConfig(level=logging.INFO)

import time
import dateutil.relativedelta

import underworlds
from underworlds.types import *

#colors
COL_WORLDS = "FF9700"
COL_WORLDS_BORDER = "A66200"
COL_CLIENTS = "00AB6F"
COL_EDGES = "0E0874"

COL_NODE_MESH = "8805A8"
COL_NODE_CAMERA = "569700"
COL_NODE_ENTITY = "FFDE00"
COL_NODE_UNDEFINED = "DEDEDE"

def heat_to_rgb(v, maxvalue = 1.0, minvalue = 0.0):
    min_visible_wavelength = 450.0
    max_visible_wavelength = 700.0

    wavelength = (v - minvalue) / (maxvalue-minvalue) * \
                 (max_visible_wavelength - min_visible_wavelength) + \
                 min_visible_wavelength

    rgb = wavelength_to_rgb(wavelength)

    return "%02x%02x%02x" % rgb

def wavelength_to_rgb(wl):
    """ Converts a visible wavelength (in nanometer) to the corresponding
    R,B,G triple.

    Based on: http://stackoverflow.com/questions/2374959/algorithm-to-convert-any-positive-integer-to-an-rgb-value
    """
    gamma = 0.80
    intensity_max = 255

    def adjust(color, factor):
        if color == 0.0:
            return 0 # Don't want 0^x = 1 for x <> 0
        else:
            return int(intensity_max * pow(color * factor, gamma))
    
    if wl >= 380 and wl < 440:
        red = -(wl - 440) / (440 - 380)
        green = 0.0
        blue = 1.0
    elif wl >= 440 and wl < 490:
        red = 0.0
        green = (wl - 440) / (490 - 440)
        blue = 1.0
    elif wl >= 490 and wl < 510:
        red = 0.0
        green = 1.0
        blue = -(wl - 510) / (510 - 490)
    elif wl >= 510 and wl < 580:
        red = (wl - 510) / (580 - 510)
        green = 1.0
        blue = 0.0
    elif wl >= 580 and wl < 645:
        red = 1.0
        green = -(wl - 645) / (645 - 580)
        blue = 0.0
    elif wl >= 645 and wl <= 780:
        red = 1.0
        green = 0.0
        blue = 0.0
    else:
        red = 0.0
        green = 0.0
        blue = 0.0

    # Let the intensity fall off near the vision limits
    if wl >= 380 and wl < 420:
        factor = 0.3 + 0.7 * (wl - 380) / (420 - 380)
    elif wl >= 420 and wl < 700:
        factor = 1.0
    elif wl >= 700 and wl < 780:
        factor = 0.3 + 0.7 * (780 - wl) / (780 - 700)
    else:
        factor = 0.0

    r = adjust(red,   factor)
    g = adjust(green, factor)
    b = adjust(blue,  factor)

    return (r,g,b)

class UnderworldsWindow(xdot.DotWindow):

    base_name = "Underworlds Viewer"

    def __init__(self):
        xdot.DotWindow.__init__(self)


        self.autorefresh = False

        # Create actions
        actiongroup = Gtk.ActionGroup('ReloadAction')
        actiongroup.add_actions((
            ('Reload', Gtk.STOCK_REFRESH, None, None, "Reload the topology", self.on_reload),
        ))
        actiongroup.add_toggle_actions((
            ('Autorefresh', Gtk.STOCK_MEDIA_PLAY, None, None, "Autorefresh", self.toggle_autorefresh, False),
        ))

        # Add the actiongroup to the uimanager
        self.uimanager.insert_action_group(actiongroup)

        self.dotwidget.connect('clicked', self.on_node_clicked)

        self._ctx = underworlds.Context("topology observer")

    def toggle_autorefresh(self, action):
        if self.autorefresh:
            self.autorefresh = False
        else:
            self.autorefresh = True
            gobject.timeout_add(200, self.autoupdate)

    def get_dot_content(self):
        pass

    def autoupdate(self):
        self.on_reload(None)
        return self.autorefresh

    def on_reload(self, action):
        self.set_dotcode(self.get_dot_content())

        uptime = dateutil.relativedelta.relativedelta(seconds = self._ctx.uptime())
        self.set_title(self.base_name + " - uptime: %dh%02d'%02d''" % (uptime.hours + (uptime.days * 24), uptime.minutes, uptime.seconds))

    def on_node_clicked(self, widget, url, event):
        pass

class UnderworldsTopologyWindow(UnderworldsWindow):
    
    base_name = "Underworlds Topology Viewer"

    def get_dot_content(self):
        topo = self._ctx.topology()

        dotcode = "digraph G {\n"

        for w in topo["worlds"]:
            dotcode += '"%s" [color="#%s", shape=box, style=filled, URL="%s"];\n' % (w, COL_WORLDS, w)

        for c in topo["clients"].keys():
            name = topo["clientnames"][c]
            dotcode += '"%s" [label="%s", color="#%s", style=filled];\n' % (c, name, COL_CLIENTS)

        for c, links in topo["clients"].items():
            for w, details in links.items():
                type, timestamp = details

                last_activity = time.time() - timestamp
                
                heat = max(0.0, 1.0 - (last_activity / 30))
                
                label = "%s\\n(last activity: " % type.lower()
                if last_activity < 2:
                    label += "%d ms" % (last_activity * 1000)
                elif last_activity > 60:
                    label += "%d min" % (last_activity / 60)
                else:
                    label += "%.2f sec" % last_activity
                
                label += " ago)"

                # orient the arrow in the right direction
                if type == READER:
                    edge = '"%s" -> "%s"' % (w, c)
                elif type == MONITOR:
                    edge = '"%s" <-> "%s"' % (w, c)
                else:
                    edge = '"%s" -> "%s"' % (c, w)
                dotcode += edge + ' [label="%s", color="#%s", fontsize=8];\n' % (label, heat_to_rgb(heat))

        dotcode += "}\n"

        return dotcode

    def on_node_clicked(self, widget, world, event):

        ### Workaround for xdot mangling the URL (-> the world look like that: "b'test'")
        import ast
        world = ast.literal_eval(world).decode()
        ###

        window = UnderworldsWorldWindow(world)
        window.on_reload(None)


class UnderworldsWorldWindow(UnderworldsWindow):


    def __init__(self, world):
        UnderworldsWindow.__init__(self)

        self.base_name = "Underworlds World Explorer: <%s>" % world
        self.world = self._ctx.worlds[world]
        self.nodes = self.world.scene.nodes

    def get_dot_content(self):

        dotcode = "digraph G {\n"

        for n in self.nodes:
            shape = "shape=box, style=filled"
            color = COL_NODE_UNDEFINED
            if n.type == MESH:
                shape = "shape=box3d"
                color = COL_NODE_MESH
            elif n.type == CAMERA:
                color = COL_NODE_CAMERA
            elif n.type == ENTITY:
                color = COL_NODE_ENTITY

            last_activity = time.time() - n.last_update
            
            heat = max(0.0, 1.0 - (last_activity / 30))
            
            label = "%s\\n(last update: " % n
            if last_activity < 2:
                label += "%d ms" % (last_activity * 1000)
            elif last_activity > 60:
                label += "%d min" % (last_activity / 60)
            else:
                label += "%.2f sec" % last_activity
            
            label += " ago)"

            dotcode += '"%s" [label="%s", color="#%s", %s];\n' % (n.id, label, color, shape)

        for n in self.nodes:
            for c in n.children:

                dotcode += '"%s" -> "%s" [color="#%s"];\n' % (n.id, self.nodes[c].id, COL_EDGES)

        dotcode += "}\n"

        return dotcode

    def on_node_clicked(self, widget, url, event):
        window = UnderworldsWorldWindow()
        window.set_destroy_with_parent(True)
        window.on_reload(None)


def main():
    window = UnderworldsTopologyWindow()
    window.on_reload(None)
    window.connect('destroy', Gtk.main_quit)
    Gtk.main()

if __name__ == '__main__':
    main()

# Copyright (C) 2016 Chris Teague
# This file is part of "Delete After Watching" (DAW) Kodi Addon.
#
#    DAW is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    DAW is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with DAW.  If not, see <http://www.gnu.org/licenses/>.

# todo: comment classes/methods
# python imports
import sys
import os
import json

# kodi imports
import xbmc
import xbmcgui
import xbmcaddon
import pyxbmct.addonwindow as pyxbmct

# addon imports
import util

_path = util.__ADDON.getAddonInfo('path')
_check_icon = os.path.join(_path, 'resources', 'media', 'check.png')

_rows = 12
_cols = 4


class MultiChoiceDialog(pyxbmct.AddonDialogWindow):
    """
    Dialog which allow for selecting multiple items simultaneously.
    Based on the pyxbmct gui library by Roman_V_M and the suggested
    implementation from the forum:
    http://forum.kodi.tv/showthread.php?tid=207531
    """
    def __init__(self, title="", items=[], selected=[]):
        super(MultiChoiceDialog, self).__init__(title)
        self.setGeometry(width_=540, height_=648, rows_=_rows, columns_=_cols)
        self.selected = []
        self.set_controls()
        self.connect_controls()
        self.listing.addItems(items)
        self.set_navigation()
        self.ok_pressed = False

        for index in range(self.listing.size()):
            if self.listing.getListItem(index).getLabel() in selected:
                self.check_uncheck(index)

    def set_controls(self):
        self.listing = pyxbmct.List(_imageWidth=15)
        self.placeControl(self.listing, row=0, column=0,
                          rowspan=_rows-1, columnspan=_cols)
        self.ok_button = pyxbmct.Button("OK")
        self.placeControl(self.ok_button, row=_rows-1, column=(_cols//2)-1)
        self.cancel_button = pyxbmct.Button("Cancel")
        self.placeControl(self.cancel_button, row=_rows-1, column=(_cols//2))

    def connect_controls(self):
        self.connect(self.listing, self.check_uncheck)
        self.connect(self.ok_button, self.ok)
        self.connect(self.cancel_button, self.close)

    def set_navigation(self):
        self.listing.controlUp(self.ok_button)
        self.listing.controlDown(self.ok_button)
        self.listing.controlRight(self.ok_button)
        self.ok_button.setNavigation(self.listing, self.listing,
                                     self.cancel_button, self.cancel_button)
        self.cancel_button.setNavigation(self.listing, self.listing,
                                         self.ok_button, self.ok_button)
        self.setFocus(self.listing)

    def check_uncheck(self, index=None):
        if index:
            list_item = self.listing.getListItem(index)
        else:
            list_item = self.listing.getSelectedItem()
        if list_item.getLabel2() == "checked":
            list_item.setArt({'icon': ''})
            list_item.setLabel2("unchecked")
        else:
            list_item.setArt({'icon': _check_icon})
            list_item.setLabel2("checked")

    def ok(self):
        for index in range(self.listing.size()):
            if self.listing.getListItem(index).getLabel2() == "checked":
                self.selected.append(index)
        self.ok_pressed = True
        super(MultiChoiceDialog, self).close()

    def close(self):
        self.selected = []
        super(MultiChoiceDialog, self).close()


def select_items(media_type):
    items = []
    selected_items = []
    filename = None  # .json file to store the selected items in
    select_dialog_title = None

    if media_type == 'type=movie':
        util.log("Selecting Movies")
        resp = util.rpc('VideoLibrary.GetMovies',
                        {"properties": ['title', 'sorttitle', 'originaltitle'],
                         "sort": {"order": "ascending", "method": "title"}})

        result = resp.get('result')
        library_movies = result.get('movies')
        for movie in library_movies:
            items.append(movie.get('title'))
        filename = util.movies_selected_path
        select_dialog_title = util.string(32016)

    elif media_type == 'type=series':
        util.log("Selecting tv series")
        resp = util.rpc('VideoLibrary.GetTVShows',
                        {"properties": ['title', 'sorttitle', 'originaltitle'],
                         "sort": {"order": "ascending", "method": "title"}})

        result = resp.get('result')
        tvshows = result.get('tvshows')
        for show in tvshows:
            items.append(show.get('title'))
        filename = util.series_selected_path
        select_dialog_title = util.string(32009)
    else:
        util.log("daw argument error, argv: %s" % (sys.argv))
        xbmcgui.Dialog().notification("Error", "Video type error")
        sys.exit(1)

    if os.path.isfile(filename):
        fp = open(filename, 'r')
        selected_items = json.load(fp)
        fp.close()

    dialog = MultiChoiceDialog(select_dialog_title, items, selected_items)
    dialog.doModal()
    if dialog.ok_pressed and dialog.selected:
        new_selected = [items[i] for i in dialog.selected]
        if not os.path.exists(util.profile):
            os.makedirs(util.profile, 0o755)
        fp = open(filename, 'w+')
        json.dump(new_selected, fp)
        fp.close()

    del dialog  # delete when done, as xbmcgui classes aren't grabage-collected


if __name__ == "__main__":
    select_items(sys.argv[1])

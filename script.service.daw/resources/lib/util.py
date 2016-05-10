# -*- coding: utf-8 -*-
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

from __future__ import unicode_literals
import xbmc
import xbmcaddon
import json
import os

try:
    __ADDON = xbmcaddon.Addon()
except RuntimeError:
    __ADDON = xbmcaddon.Addon(id='script.service.daw')
__ADDON_ID = __ADDON.getAddonInfo('id').decode('utf-8')
ADDON_NAME = __ADDON.getAddonInfo('name')
_profile = xbmc.translatePath(__ADDON.getAddonInfo('profile') )
_series_selected_file = 'series_selected.json'
series_selected_path = os.path.join(_profile, _series_selected_file)
_movies_selected_file = 'movies_selected.json'
movies_selected_path = os.path.join(_profile, _movies_selected_file)


def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log(("[" + __ADDON_ID + "] " + msg).encode('utf-8', 'replace'), level)

def rpc(method, params={}):
    id=42 #todo: make this a random integer
    params = json.dumps(params, encoding='utf-8')
    query = b'{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": %d}' % (method, params, id)
    log("daw rpc: %s" % (query))
    return json.loads(xbmc.executeJSONRPC(query), encoding='utf-8')

def string(id):
	return  __ADDON.getLocalizedString(id)

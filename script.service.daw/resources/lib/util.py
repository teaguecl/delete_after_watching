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
# todo: comment classes/methods
from __future__ import unicode_literals
import xbmc
import xbmcaddon
import json
import os
import random
import xbmcvfs

__ADDON = xbmcaddon.Addon(id='script.service.daw')
__ADDON_ID = __ADDON.getAddonInfo('id')
ADDON_NAME = __ADDON.getAddonInfo('name')
profile = xbmc.translatePath(__ADDON.getAddonInfo('profile'))
_series_selected_file = 'series_selected.json'
series_selected_path = os.path.join(profile, _series_selected_file)
_movies_selected_file = 'movies_selected.json'
movies_selected_path = os.path.join(profile, _movies_selected_file)


def log(msg, level=xbmc.LOGINFO):
    if "true" == xbmcaddon.Addon(id='script.service.daw').getSetting('logging_enabled'):
        xbmc.log("[" + __ADDON_ID + "] " + msg, level)


def rpc(method, params={}):
    id = random.randint(1, 99)
    params = json.dumps(params)
    query = '{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": %d}' % (method, params, id)
    log("rpc: {}".format(query))
    return json.loads(xbmc.executeJSONRPC(query), encoding='utf-8')


def string(id):
    return __ADDON.getLocalizedString(id)


def delete_file(filename):
    validated_file = xbmcvfs.validatePath(filename)
    if xbmcvfs.exists(validated_file):
        log("deleting file: {}".format(validated_file))
        xbmcvfs.delete(validated_file)
    else:
        log("delete file failed: {}".format(validated_file))

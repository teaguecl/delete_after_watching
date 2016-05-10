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

#todo sensible logging
import os
import xbmcgui
#from resources.lib import dialog, utilfile
#from resources.lib.utils import setting
#from resources.lib.progress import Progress
from resources.lib import util
#import resources.lib.util as util
import json
import xbmcaddon

_PROMPT_NEVER = "0"
_PROMPT_SELECTED = "1"
_PROMPT_UNSELECTED = "2"

class Video(object):
    def __init__(self):
        util.log("daw video created object")
        self.type = None
        self.title = None
        self.full_title = None
        self.prompt = None
        self.playcount = None
        self.first_watch_only = None
    def delete(self):
        util.log("daw video delete")
    def ended(self):
        if self.prompt == _PROMPT_NEVER:
            return
        selected_videos = []
        if os.path.isfile(self.selected_path):
            fp = open(self.selected_path, 'r')
            selected_videos = json.load(fp)
            fp.close()

        # start by checking if the just finished video is 'selected'
        do_prompt = False
        if self.prompt == _PROMPT_SELECTED:
            do_prompt = self.title in selected_videos
        elif self.prompt == _PROMPT_UNSELECTED:
            do_prompt = self.title not in selected_videos

        # if selected, but this isn't the first watch - then don't prompt for delete
        if do_prompt and self.first_watch_only == 'true' and self.playcount != 0:
            do_prompt = False

        if do_prompt:
            do_delete = xbmcgui.Dialog().yesno(self.full_title,
                                               self.file, '',
                                               util.string(32018), autoclose=120*1000)
            if do_delete:
                self.delete()

class Movie(Video):
    def __init__(self, id):
        super(Movie, self).__init__()
        self.type = 'movie'
        self.id = id
        self.selected_path = util.movies_selected_path
    def ended(self):
        util.log("daw movie ended")
        params = {'movieid': self.id, 'properties' : ['title', 'playcount', 'file']}
        response = util.rpc('VideoLibrary.GetMovieDetails', params)
        result = response.get('result')
        util.log("daw: moviedetails %s" % (response))
        moviedetails = result.get('moviedetails')
        movie_title = moviedetails.get('title')
        filename = moviedetails.get('file')
        self.title = movie_title
        self.full_title = self.title
        self.file = filename
        self.playcount = int(moviedetails.get('playcount'))
        self.prompt = xbmcaddon.Addon().getSetting('movies_prompt_rule')
        self.first_watch_only = xbmcaddon.Addon().getSetting('movie_first_watch_del')
        super(Movie, self).ended()
    def delete(self):
        params = {'movieid': self.id}
        response = util.rpc('VideoLibrary.RemoveMovie', params)
        if response.get('result') != 'OK':
            util.log("daw: Error removing from library")
        os.remove(self.file)

class SeriesEpisode(Video):
    def __init__(self, id):
        super(SeriesEpisode, self).__init__()
        self.type = 'episode'
        self.id = id
        self.selected_path = util.series_selected_path

    def ended(self):
        util.log("daw tvshow ended")
        params = {'episodeid': self.id, 'properties' : ['title', 'playcount', 'file', 'tvshowid']}
        response = util.rpc('VideoLibrary.GetEpisodeDetails', params)
        result = response.get('result')
        episodedetails = result.get('episodedetails')
        episode_title = episodedetails.get('title')
        filename = episodedetails.get('file')
        tvshowid = episodedetails.get('tvshowid')
        self.playcount = int(episodedetails.get('playcount'))

        params = {'tvshowid': tvshowid, 'properties' : ['title', 'sorttitle', 'originaltitle', 'playcount', 'file']}
        response = util.rpc('VideoLibrary.GetTVShowDetails', params)
        result = response.get('result')
        tvshowdetails = result.get('tvshowdetails')
        series_title = tvshowdetails.get('title')
        self.title = series_title
        self.full_title = series_title + ': ' + episode_title
        self.file = filename
        self.prompt = xbmcaddon.Addon().getSetting('series_prompt_rule')
        self.first_watch_only = xbmcaddon.Addon().getSetting('series_first_watch_del')
        super(SeriesEpisode, self).ended()

    def delete(self):
        params = {'episodeid': self.id}
        response = util.rpc('VideoLibrary.RemoveEpisode', params)
        if response.get('result') != 'OK':
            util.log("daw: Error removing from library") # todo: a notification here?
        os.remove(self.file)


        #todo: handle this class of video
class NonLibraryVideo(Video):
    def __init__(self, filename):
        super(NonLibraryVideo, self).__init__()
        self.type = 'nonlibrary' # todo: use isinstanceof???
        self.filename = filename

    def ended(self):
        util.log("daw nonlibrary video ended")

class DAWPlayer(xbmc.Player):
    def onPlayBackStarted(self):
        util.log("daw: Playback started")
        util.log("daw: %s " % (self.getPlayingFile()))
        self.playing = None

        response = util.rpc('Player.GetActivePlayers')
        util.log("daw active players: %s" % (response))

        playerList = response.get('result', [])
        for player in playerList:
            util.log("daw: player:: %s" % (player))
            if player.get('type') == 'video':
                playerId = player.get('playerid')
                util.log("daw: playerid is %s" % (playerId))

                response = util.rpc('Player.GetItem', {'playerid': playerId,
                                                 'properties': ['file', 'title', 'playcount']})
                util.log("daw getitem resp: %s" % (response))
                result = response.get('result')
                item = result.get('item')
                type = item.get('type')
                id = item.get('id')
                file = item.get('file')
                title = item.get('title')
                playcount = item.get('playcount')

                util.log("daw playcount: %s" % (playcount))
                if type == 'movie':
                    self.playing = Movie(id)
                elif type == 'episode':
                    self.playing = SeriesEpisode(id)
                elif type == 'unknown':
                    self.playing = NonLibraryVideo(filename=file)

class DAWMonitor(xbmc.Monitor):
    def __init__(self, player):
        super(DAWMonitor, self ).__init__()
        self.player = player

    def onNotification(self, sender, method, data):
        util.log("daw: onNotification: %s" % (method))
        if method == 'Player.OnStop':
            data = json.loads(data)
            util.log("daw: data: %s" % (data))

            watched_to_end = data['end']
            if self.player.playing:
                if watched_to_end == True:
                    util.log("daw Watched")
                    self.player.playing.ended()
                else:
                    util.log("daw Not Watched")
                self.player.playing = None

player = DAWPlayer()
monitor = DAWMonitor(player)
monitor.waitForAbort()

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
import os
import xbmcgui
from resources.lib import util
import xbmcaddon
import json

_PROMPT_NEVER = "0"
_PROMPT_SELECTED = "1"
_PROMPT_UNSELECTED = "2"
_PROMPT_ALWAYS = "3"


class Video(object):
    def __init__(self):
        util.log("video created object")
        self.title = None
        self.full_title = None
        self.prompt = None
        self.playcount = None
        self.first_watch_only = None
        self.selected_path = None
        self.file = None

    def __str__(self):
        obj_string = ("title={}, full_title={}, prompt={}, playcount={}, "
                      "first_watch={}, selected_path{}, file={}").format(
                          self.title, self.full_title,
                          self.prompt, str(self.playcount),
                          self.first_watch_only, self.selected_path, self.file)
        return obj_string

    def delete(self):
        util.log("video delete")

    def ended(self):
        util.log("Video ended: {}".format(self))
        if self.prompt == _PROMPT_NEVER:
            return

        do_prompt = False
        if self.prompt == _PROMPT_ALWAYS:
            do_prompt = True
        else:
            selected_videos = []
            if os.path.isfile(self.selected_path):
                fp = open(self.selected_path, 'r')
                selected_videos = json.load(fp)
                fp.close()

            # check if the just finished video is 'selected'
            if self.prompt == _PROMPT_SELECTED:
                do_prompt = self.title in selected_videos
            elif self.prompt == _PROMPT_UNSELECTED:
                do_prompt = self.title not in selected_videos

        # if configured to prompt on first watch,
        # and this isn't the first watch - don't prompt for delete
        if do_prompt and self.first_watch_only == 'true' and self.playcount != 0:
            do_prompt = False

        if do_prompt:
            do_delete = xbmcgui.Dialog().yesno(self.full_title,
                                               self.file, '',
                                               util.string(32018),
                                               autoclose=120*1000)
            if do_delete:
                self.delete()


class Movie(Video):

    def __init__(self, media_id):
        super(Movie, self).__init__()
        self.id = media_id
        self.selected_path = util.movies_selected_path

    def ended(self):
        util.log("Movie ended")
        params = {'movieid': self.id, 'properties': ['title', 'playcount', 'file']}
        response = util.rpc('VideoLibrary.GetMovieDetails', params)
        result = response.get('result')
        util.log("moviedetails %s" % (response))
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
        util.log("Deleting Movie: {}".format(self.title))
        params = {'movieid': self.id}
        response = util.rpc('VideoLibrary.RemoveMovie', params)
        if response.get('result') != 'OK':
            util.log("Error removing from library")
        else:
            util.delete_file(self.file)


class SeriesEpisode(Video):

    def __init__(self, media_id):
        super(SeriesEpisode, self).__init__()
        self.id = media_id
        self.selected_path = util.series_selected_path

    def ended(self):
        util.log("tvshow ended: {}".format(self))
        params = {'episodeid': self.id, 'properties': ['title', 'playcount', 'file', 'tvshowid']}
        response = util.rpc('VideoLibrary.GetEpisodeDetails', params)
        result = response.get('result')
        episodedetails = result.get('episodedetails')
        episode_title = episodedetails.get('title')
        filename = episodedetails.get('file')
        tvshowid = episodedetails.get('tvshowid')
        self.playcount = int(episodedetails.get('playcount'))

        params = {'tvshowid': tvshowid, 'properties': ['title', 'sorttitle', 'originaltitle', 'playcount', 'file']}
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
        util.log("Deleting TV Show: {}".format(self.full_title))
        util.log("file: {}".format(self.file))
        params = {'episodeid': self.id}
        response = util.rpc('VideoLibrary.RemoveEpisode', params)
        if response.get('result') != 'OK':
            util.log("Error removing from library")
            xbmcgui.Dialog().notification("Error", "Unable to remove from library")
        else:
            util.delete_file(self.file)


class NonLibraryVideo(Video):
    def __init__(self, filename, playcount):
        util.log("nonlibrary started: {} playcount: {}".format(filename, playcount))
        super(NonLibraryVideo, self).__init__()
        self.file = filename
        self.playcount = playcount

    def ended(self):
        util.log("nonlibrary video ended: {}".format(self))
        self.prompt = xbmcaddon.Addon().getSetting('non-library_prompt_rule')
        if self.prompt == "1":  # Value 1 from this setting means 'always'
            self.prompt = _PROMPT_ALWAYS
        self.first_watch_only = xbmcaddon.Addon().getSetting('non-library_first_watch_del')
        self.full_title = xbmcaddon.Addon().getAddonInfo('name')
        super(NonLibraryVideo, self).ended()

    def delete(self):
        util.log("nonlibrary delete: {}".format(self.file))
        util.delete_file(self.file)

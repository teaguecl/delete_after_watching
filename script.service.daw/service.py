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

# todo: exit kodi while in setting menu
"""Delete After Watching service module

This module implements the DAW service.  This service runs at startup,
and continues until shutdown.

The DAW service uses xmbc.Player to detect when a video has started, and
it uses xbmc.Monitor to determine when it stops.  When a video stops, DAW
will prompt the user to see if they would like to delete the just finished
video.  This prompt is conditional, based on the settings the user has chosen
(e.g. Movies, TV Shows etc).

todo: put github url here
"""

from resources.lib import util
from resources.lib import video_types
import json
import xbmc


class DAWPlayer(xbmc.Player, object):
    """
    Extension of the xbmc.Player used to detect when video playback begins.

    The __init__ method may be documented in either the class level
    docstring, or as a docstring on the __init__ method itself.

    Either form is acceptable, but the two should not be mixed. Choose one
    convention to document the __init__ method and be consistent with it.

    Attributes:
        playing (Video): Object representing the currently playing video.
    """

    def __init__(self):
        self.playing = None
        super(DAWPlayer, self).__init__()

    def onPlayBackEnded(self):
        util.log("Playback ended")
        if self.isPlayingVideo():
            util.log("Playing a video")
            util.log("time: {}".format(self.getTime()))
        pass

    def onPlayBackStopped(self):
        util.log("Playback stopped")
        if self.isPlayingVideo():
            util.log("Playing a video")
            util.log("time: {}".format(self.getTime()))
        pass

    def onAVStarted(self):
        """Callback which is executed when media playback begins.

        This is an overload of the xbmc.Player class method of the same name.
        It will detect what type of media is being played, and if it is one of
        interest, it will store this information in the self.playing attribute.
        """
        util.log("Playback started")
        util.log("{} ".format(xbmc.Player.getPlayingFile(self)))
        self.playing = None

        response = util.rpc('Player.GetActivePlayers')
        player_list = response.get('result', [])
        for player in player_list:
            util.log("player: {}".format(player))
            if player.get('type') == 'video':
                player_id = player.get('playerid')
                response = util.rpc('Player.GetItem',
                                    {'playerid': player_id,
                                     'properties': ['file',
                                                    'playcount']})
                util.log("getitem resp: {}".format(response))
                result = response.get('result')
                item = result.get('item')
                media_type = item.get('type')
                media_id = item.get('id')
                filename = item.get('file')
                playcount = item.get('playcount')

                util.log("playcount: {}".format(playcount))
                util.log("type: {}".format(media_type))
                if media_type == 'movie':
                    self.playing = video_types.Movie(media_id)
                elif media_type == 'episode':
                    self.playing = video_types.SeriesEpisode(media_id)
                elif media_type == 'unknown':
                    self.playing = video_types.NonLibraryVideo(filename,
                                                               playcount)


class DAWMonitor(xbmc.Monitor, object):
    """Monitors the status of Kodi.

    Looks for media playback ending, and notifies the register DAWPlayer.

    Args:
        player (DAWPlayer): Player to be notified when media playback ends.

    Attributes:
        self.player (DAWPlayer): Player object

    """
    def __init__(self, player):
        super(DAWMonitor, self).__init__()
        self.player = player

    def onNotification(self, sender, method, data):
        """Callback for Kodi notifications.

        Checks if the notification is indicating that the media playback has
        ended.  If so, it also checks if the media was watched all the way
        to the end.  If both conditions are met, it notifies the registered
        DAWPlayer object of this event.

        """
        util.log("onNotification: %s" % (method))
        if method == 'Player.OnStop':
            data = json.loads(data)
            util.log("onStop data: %s" % (data))
            
            watched_to_end = data['end']
            if self.player.playing:
                if watched_to_end is True:
                    self.player.playing.ended()
                self.player.playing = None

        if method == 'VideoLibrary.OnUpdate':
            data = json.loads(data)
            util.log("onUpdate data: %s" % (data))
            sid = 6
            params = {'episodeid': sid, 'properties': ['title', 'playcount', 'file', 'tvshowid', 'resume', 'runtime']}
            response = util.rpc('VideoLibrary.GetEpisodeDetails', params)
            result = response.get('result')
            episodedetails = result.get('episodedetails')
            episode_title = episodedetails.get('title')
            filename = episodedetails.get('file')
            tvshowid = episodedetails.get('tvshowid')
            resume = episodedetails.get('resume')
            runtime = episodedetails.get('runtime')
            util.log("tv resume: {}   runtime: {}".format(resume, runtime))

monitor = DAWMonitor(DAWPlayer())
monitor.waitForAbort()

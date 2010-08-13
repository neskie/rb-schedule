import rb, rhythmdb
import gtk, pygtk, gobject
from time import localtime
import random
import os
from configdata import *

class Schedule (rb.Plugin):
    def __init__(self):
        rb.Plugin.__init__(self)
        self.timeout_id = None
        self.timeout = 1000*5
        self.shows = ScheduleLoader() 
        self.db = None
        self.shell = None

    def activate(self, shell):
        '''We initalize some values and start prepping shows'''
        self.shell = shell
        self.db = shell.props.db
        self.playlistayer = self.shell.get_player()
        gobject.timeout_add(self.timeout,self.clear_queue)
        self.timeout_id = gobject.timeout_add(self.timeout,self.prep_show)

    def deactivate(self, shell):
        del self.shell
        del self.playlistayer
        del self.db
        del self.shows
        del self.timeout
        del self.timeout_id

    def prep_show(self):
        '''Get the time until the top of the hour and then add songs to the
        queue.'''

        t = localtime()
        min_to_hour = 60 - int(t.tm_min)
        print min_to_hour

        # if min_to_hour is less than 5 minutes? then we should?
        # play some a station id filled with PSA's???

        self.timeout = 1000*(60*min_to_hour - int(t.tm_sec))

        self.add_to_queue(min_to_hour)
        
        if not self.playlistayer.props.playing:
            self.playlistayer.playpause()

        # on start we call a this function and so we'll remove the old version
        # and then start a new one on the timeout.
        gobject.source_remove(self.timeout_id)
        self.timeout_id = gobject.timeout_add(self.timeout,self.prep_show)
        return True

    def add_to_queue(self,time_duration):
        '''Gets current show and creates a list of the locations and adds them
        to the play queue.'''
        try:
            genre = str(self.shows.get_current_show()['title'])
        except:
            genre = "Rock"

        qm = self.get_qm([[rhythmdb.QUERY_PROP_LIKE, rhythmdb.PROP_GENRE,
            genre]])

        if qm.get_duration() < time_duration*60:
            '''If we have less music then an hour lets just play Rock.'''
            print "You should go with rock"
            qm = self.get_qm([[rhythmdb.QUERY_PROP_LIKE,rhythmdb.PROP_GENRE,"Rock"]])

        uri_loc = self.get_locations(qm)
     
        total_duration = 0
        uri_loc = random.sample(uri_loc,len(uri_loc))
	
        try:
            id = self.get_station_id()
            self.shell.add_to_queue(id[0])
        except:
            print "No Station IDS"

        for song in uri_loc:
            if total_duration + song[1] < time_duration*60 + 30:
                total_duration += song[1]
                self.shell.add_to_queue(song[0])

        print "Duration: " + str(1.0*total_duration/60)
        print "Timeout:  " + str(1.0*self.timeout/1000/60)

    # pass a list of lists of key:value pairs to search on
    def get_qm(self,query_list):
        db = self.db
        query = db.query_new()
        for q in query_list:
            db.query_append(query,q)
        qm = db.query_model_new(query)
        db.do_full_query_parsed(qm, query)
        return qm

    def get_locations(self, qm):
        locations = []
        for row in qm:
            entry = row[0]
            duration = self.db.entry_get(entry, rhythmdb.PROP_DURATION)
            location = self.db.entry_get(entry, rhythmdb.PROP_LOCATION)
            locations.append((location,duration))
        return locations

    def get_station_id(self):
        '''Gets a Station ID'''
        qm = self.get_qm([[rhythmdb.QUERY_PROP_LIKE,rhythmdb.PROP_GENRE,"Station ID"]])
        ids = self.get_locations(qm)
        index = random.randint(0, len(ids)-1)
        return ids[index]

    #Why isn't their a python Binding for this?
    def clear_queue(self):
        queue = self.shell.props.queue_source
        view = queue.get_entry_view()
        view.select_all()
        if not view.have_selection():
            queue.delete()
        return False

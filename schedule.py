#schedule.py
# vim: ts=4: sw=4:et:sts:ai
#
# Goal: Pick an hour, or the remaining portion of an hour in a certain genre,
# spoken word show, or do nothing and add it to the play_queue
#
# We can use the iteravely call the gobject time out.  Once when we first
# start rhythmbox, then timeout the rest of the hour, then on the hour we
# timeout.
#
# Here are some descriptors of a show:
#  * syndicated, automatic, or live
#  * they have a genre
#  * they have an hour and dow to start
#
# We need to make a list with these requriements:
#    * play one station id at beginning and in middlee of show
#    * play 2 PSA's around 15:min and around 45:minutes

import rb, rhythmdb
import gtk, pygtk, gobject
from time import strftime, localtime
import random
import os

class Schedule (rb.Plugin):
    def __init__(self):
        rb.Plugin.__init__(self)
        self.day = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        self.timeout_id = None
        self.timeout = 1000*3
        self.shows = {}
        self.pl = "Rock"
        self.db = None
        self.shell = None

        #load all of the shows into the variable.
        self.load_shows()

    def activate(self, shell):
        self.shell = shell
        self.db = shell.props.db
        self.player = self.shell.get_player()

        #Initial timeout waits for 3 seconds then runs.
        self.timeout_id = gobject.timeout_add(self.timeout,self.check_schedule)

    def deactivate(self, shell):
        del self.shell
        del self.player
        del self.db

    def check_schedule(self):
        t = localtime()

        self.pl = self.shows[self.day[int(t.tm_wday)]][str(t.tm_hour)]

        min_to_hour = 60 - int(t.tm_min)
        self.timeout = 1000*(60*min_to_hour + int(t.tm_sec))
        print self.timeout_id

        self.get_genre(min_to_hour)
        
        if not self.player.props.playing:
            self.player.playpause()

        gobject.source_remove(self.timeout_id)
        self.timeout_id = gobject.timeout_add(self.timeout,self.check_schedule)
        print self.timeout
        print self.timeout_id
        return True

    # boring load shows of the schedule stored in a local dictionary file.
    def load_shows(self):
        for day in self.day:
            self.shows[day] = {}

        PROJ_ROOT = os.path.dirname(os.path.realpath(__file__))
        path = PROJ_ROOT+"/radiosched.csv"
        fd = open(path)

        show = fd.readline()
        while show:
            show = show.strip().split('|')
            self.shows[show[4]][show[3]] = show[2]
            show = fd.readline()

    #send a 
    def get_genre(self,time_duration):
        genre = self.pl
        db = self.shell.props.db
        query = db.query_new()
        db.query_append(query,[rhythmdb.QUERY_PROP_LIKE,
            rhythmdb.PROP_GENRE, genre])
        qm = db.query_model_new(query)
        db.do_full_query_parsed(qm, query)

        uri_loc= []
        for row in qm:
            entry = row[0]
            duration = db.entry_get(entry, rhythmdb.PROP_DURATION)
            location = db.entry_get(entry, rhythmdb.PROP_LOCATION)
            uri_loc.append((location,duration))
     
        total_duration = 0
        uri_loc = self.randomize(uri_loc)
        try:
            song = uri_loc.pop()
        except:
            pass

        while uri_loc :
            if total_duration + song[1] < time_duration*60:
                total_duration += song[1]
                self.shell.add_to_queue(song[0])
            song = uri_loc.pop()

    #this should be a sub routine of some other function it's only used to
    # a list random.
    def randomize(self,l):
        length = len(l)
        for i in range(length):
            j = random.randint(i, length-1)
            l[i], l[j] = l[j], l[i]
        return l

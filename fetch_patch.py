diff --git a/.gitignore b/.gitignore
new file mode 100644
index 0000000..0d20b64
--- /dev/null
+++ b/.gitignore
@@ -0,0 +1 @@
+*.pyc
diff --git a/README b/README
index f3b00f7..04d9a37 100644
--- a/README
+++ b/README
@@ -1,6 +1,7 @@
-This Rhytmbox Plugin will act as our Automatic Playlist Generator.  This is
-meant to be robust enough to work unattended for at leat a day, and not drift
-by too much.
+This is ugly, but it works to play music on a local community radio station
+running Ubuntu and Rhythmbox.
 
-The test suite is meant to work simulate about a week's worth of typical
-programming with some real world values for songs and playlists.
+== Future ==
+
+ * Work with an SQLite database
+ * Integrate with Django 1.2
diff --git a/Schedule.py b/Schedule.py
deleted file mode 100644
index 47e5e0a..0000000
--- a/Schedule.py
+++ /dev/null
@@ -1,121 +0,0 @@
-import rb, rhythmdb
-import gtk, pygtk, gobject
-from time import localtime
-import random
-import ScheduleSlot
-import os
-from configdata import *
-
-class Schedule (rb.Plugin):
-    def __init__(self):
-        rb.Plugin.__init__(self)
-        self.timeout_id = None
-        self.timeout = 1000*5
-        self.shows = ScheduleLoader() 
-        self.db = None
-        self.shell = None
-
-    def activate(self, shell):
-        self.shell = shell
-        self.db = shell.props.db
-        self.playlistayer = self.shell.get_player()
-
-        gobject.timeout_add(self.timeout,self.clear_queue)
-
-        self.timeout_id = gobject.timeout_add(self.timeout,self.prep_show)
-
-    def deactivate(self, shell):
-        del self.shell
-        del self.playlistayer
-        del self.db
-        del self.shows
-        del self.timeout
-        del self.timeout_id
-
-    def prep_show(self):
-
-
-        t = localtime()
-        min_to_hour = 60 - int(t.tm_min)
-        print min_to_hour
-
-        # if min_to_hour is less than 5 minutes? then we should?
-        # play some a station id filled with PSA's???
-
-        self.timeout = 1000*(60*min_to_hour - int(t.tm_sec))
-
-        self.add_to_queue(min_to_hour)
-        
-        if not self.playlistayer.props.playing:
-            self.playlistayer.playpause()
-
-        # on start we call a this function and so we'll remove the old version
-        # and then start a new one on the timeout.
-        gobject.source_remove(self.timeout_id)
-        self.timeout_id = gobject.timeout_add(self.timeout,self.prep_show)
-        return True
-
-    def add_to_queue(self,time_duration):
-        '''Gets current show and creates a list of the locations'''
-        genre = str(self.shows.get_current_show()['title'])
-
-        qm = self.get_qm([[rhythmdb.QUERY_PROP_LIKE, rhythmdb.PROP_GENRE,
-            genre]])
-
-        if qm.get_duration() < time_duration*60:
-             print "you should go with rock"
-             qm = self.get_qm([[rhythmdb.QUERY_PROP_LIKE,rhythmdb.PROP_GENRE,"Rock"]])
-
-        uri_loc = self.get_locations(qm)
-     
-        total_duration = 0
-        uri_loc = random.sample(uri_loc,len(uri_loc))
-	
-        try:
-            id = self.get_station_id()
-            self.shell.add_to_queue(id[0])
-        except:
-            print "No Station IDS"
-
-        for song in uri_loc:
-            if total_duration + song[1] < time_duration*60 + 30:
-                total_duration += song[1]
-                self.shell.add_to_queue(song[0])
-
-        print "Duration: " + str(1.0*total_duration/60)
-        print "Timeout:  " + str(1.0*self.timeout/1000/60)
-
-    # pass a list of lists of key:value pairs to search on
-    def get_qm(self,query_list):
-        db = self.db
-        query = db.query_new()
-        for q in query_list:
-            db.query_append(query,q)
-        qm = db.query_model_new(query)
-        db.do_full_query_parsed(qm, query)
-        return qm
-
-    def get_locations(self, qm):
-        locations = []
-        for row in qm:
-            entry = row[0]
-            duration = self.db.entry_get(entry, rhythmdb.PROP_DURATION)
-            location = self.db.entry_get(entry, rhythmdb.PROP_LOCATION)
-            locations.append((location,duration))
-        return locations
-
-    def get_station_id(self):
-        '''Gets a Station ID'''
-        qm = self.get_qm([[rhythmdb.QUERY_PROP_LIKE,rhythmdb.PROP_GENRE,"Station ID"]])
-        ids = self.get_locations(qm)
-        index = random.randint(0, len(ids)-1)
-        return ids[index]
-
-    #Why isn't their a python Binding for this?
-    def clear_queue(self):
-        queue = self.shell.props.queue_source
-        view = queue.get_entry_view()
-        view.select_all()
-        if not view.have_selection():
-            queue.delete()
-        return False
diff --git a/ScheduleSlot.py b/ScheduleSlot.py
deleted file mode 100644
index e111532..0000000
--- a/ScheduleSlot.py
+++ /dev/null
@@ -1,32 +0,0 @@
-#schedule.py
-import random
-from time import localtime
-import xml.dom
-import sqlite3
-
-class ScheduleDB():
-    def __init__(self):
-        self.day = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
-        self.shows = {}
-        self.pl = "Rock"
-        self.dbname = 'radiosched.db'
-        self.db = None
-        self.shell = None
-
-    def mixup(self,songlist):
-        return random.sample(songlist,len(songlist))
-    def open_db(self):
-        self.db = sqlite3.connect(self.dbname)
-
-    def get_genre(self,hour,dayofweek):
-        cur = self.db.cursor()
-        cur.execute("SELECT PlaylistName FROM RadioSchedule WHERE Hour=? and DayOfWeek=?",(hour,dayofweek))
-        return cur.fetchone()[0] 
-    def generate_playlist(self,songlist):
-        playlist = []
-        duration = 0
-        for song in self.mixup(songlist):
-            if duration + song[1] < 60*60 + random.randint(0,50):
-                duration = duration + song[1]
-                playlist.append(song)
-        return playlist
diff --git a/configdata.py b/configdata.py
deleted file mode 100644
index 86c6e54..0000000
--- a/configdata.py
+++ /dev/null
@@ -1,69 +0,0 @@
-from datetime import datetime, timedelta
-import json
-import os
-import unicodedata
-# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-# GNU General Public License for more details.
-#
-# You should have received a copy of the GNU General Public License
-# along with this program; if not, write to the Free Software
-# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
-
-def strip_accents(s):
-       return ''.join((c for c in unicodedata.normalize('NFD', s) if
-           unicodedata.category(c) != 'Mn'))
-
-class ScheduleLoader():
-    def __init__(self):
-        ROOT =  os.path.dirname(os.path.realpath(__file__))
-        show_json = os.path.join(ROOT, 'show.json')
-        f = open(show_json)
-        self.schedule  = json.load(f)
-        f.close()
-
-    def get_show(self, hour, dayofweek):
-        '''Returns the playlist of the given the hour and day of week.'''
-        dayofweek = dayofweek + 1
-
-        slots = [ x for x in self.schedule if x['model'] == 'show.slot']
-        shows = [ x for x in self.schedule if x['model'] == 'show.show']
-        current_slot = [ x['fields']['show'] for x in slots if x['fields']['hour'] == hour and
-                x['fields']['dayofweek'] == dayofweek ]
-        if current_slot:
-            current_show = [ x['fields'] for x in shows if x['pk'] == current_slot[0] ]
-            current_show[0]['title'] = strip_accents(current_show[0]['title'])
-            return current_show[0]
-        else:
-            return []
-
-    def get_current_show(self):
-        t = datetime.now()
-        hour = t.hour
-        dayofweek = t.weekday()
-        return self.get_show(hour, dayofweek)
-    def get_next(self):
-        d = timedelta(hours=1)
-        t = datetime.now() + d 
-        hour = t.hour
-        dayofweek = t.weekday()
-        return self.get_show(hour, dayofweek)
-    def get_last(self):
-        d = timedelta(hours=-1)
-        t = datetime.now() + d
-        hour = t.hour
-        dayofweek = t.weekday()
-        return self.get_show(hour, dayofweek)
-    def allowed_slots(self):
-        slots = [ x for x in self.schedule if x['model'] == 'show.slot']
-        return [ (slot['fields']['hour'], slot['fields']['dayofweek'] - 1) for slot in slots ]
-    def __iter__(self):
-        slots = self.allowed_slots()
-        d = timedelta(hours=-1)
-        t = datetime.now() + d
-        hour = t.hour 
-        dayofweek = t.weekday()
-        idx = slots.index((hour,dayofweek))
-        while True:
-            idx += (idx + 1) % len(slots)
-            hour, day = self.allowed_slots()[idx]
-            yield self.get_show(hour, day)
diff --git a/radiosched.csv b/radiosched.csv
index ef82a78..9ce7ee4 100644
--- a/radiosched.csv
+++ b/radiosched.csv
@@ -21,7 +21,7 @@
 |*|Secwepemcstin|9|Monday
 |*|World|10|Monday
 |*|Rock|11|Monday
-||Spoken Word|12|Monday
+||SpokenWord|12|Monday
 |*|Secwepemcstin|13|Monday
 |*|World|14|Monday
 ||Traditional|15|Monday
@@ -39,21 +39,21 @@
 |*|Secwepemcstin|9|Tuesday
 |*|World|10|Tuesday
 |*|Rock|11|Tuesday
-||Spoken Word|12|Tuesday
+||SpokenWord|12|Tuesday
 |*|Secwepemcstin|13|Tuesday
-|*|World|14|Tuesday
+|*|*|14|Tuesday
 |*|Traditional|15|Tuesday
 |*|Rock|16|Tuesday
 |*|Secwepemcstin|17|Tuesday
 ||Spoken Word|18|Tuesday
-|*|World|19|Tuesday
+|*|FolkWorld|19|Tuesday
 |*|R&B|20|Tuesday
 |*|World|21|Tuesday
-|*|World|22|Tuesday
-|*|World|23|Tuesday
+|*|*|22|Tuesday
+|*|*|23|Tuesday
 |*|Metal|0|Wednesday
 ||Spoken Word|7|Wednesday
-|*|World|8|Wednesday
+|*|FolkWorld|8|Wednesday
 |*|Secwepemcstin|9|Wednesday
 |*|World|10|Wednesday
 |*|DD|11|Wednesday
@@ -81,10 +81,10 @@
 |*|Traditional|15|Thursday
 |*|Rock|16|Thursday
 |*|Secwepemcstin|17|Thursday
-||Spoken Word|18|Thursday
+||SpokenWord|18|Thursday
 ||Rock|19|Thursday
 |*|Reggae|20|Thursday
-||Spoken Word|21|Thursday
+||SpokenWord|21|Thursday
 |*|Rock|22|Thursday
 ||Spoken Word|23|Thursday
 |*|Metal|0|Friday
@@ -92,7 +92,7 @@
 |*|Country|8|Friday
 |*|Secwepemcstin|9|Friday
 |*|World|10|Friday
-|*|Spoken Word|11|Friday
+|*|BikeShow|11|Friday
 |*|Jazz|12|Friday
 |*|Secwepemcstin|13|Friday
 |*|Jazz|14|Friday
@@ -111,13 +111,13 @@
 |*|Secwepemcstin|9|Saturday
 |*|World|10|Saturday
 |*|Country|11|Saturday
-||Deconstructing Dinner|12|Saturday
+||Punk|12|Saturday
 |*|Punk|13|Saturday
 |*|Traditional|14|Saturday
 |*|Rock|15|Saturday
 |*|Reggae|16|Saturday
 |*|Secwepemcstin|17|Saturday
-||Native Solidarity News|18|Saturday
+||Rock|18|Saturday
 ||Rock|19|Saturday
 ||Rock|20|Saturday
 |*|Hip Hop|21|Saturday
diff --git a/schedule.py b/schedule.py
new file mode 100644
index 0000000..ba492c1
--- /dev/null
+++ b/schedule.py
@@ -0,0 +1,125 @@
+#schedule.py
+# vim: ts=4: sw=4:et:sts:ai
+#
+# Goal: Pick an hour, or the remaining portion of an hour in a certain genre,
+# spoken word show, or do nothing and add it to the play_queue
+#
+# We can use the iteravely call the gobject time out.  Once when we first
+# start rhythmbox, then timeout the rest of the hour, then on the hour we
+# timeout.
+#
+# Here are some descriptors of a show:
+#  * syndicated, automatic, or live
+#  * they have a genre
+#  * they have an hour and dow to start
+#
+# We need to make a list with these requriements:
+#    * play one station id at beginning and in middlee of show
+#    * play 2 PSA's around 15:min and around 45:minutes
+
+import rb, rhythmdb
+import gtk, pygtk, gobject
+from time import strftime, localtime
+import random
+import os
+
+class Schedule (rb.Plugin):
+    def __init__(self):
+        rb.Plugin.__init__(self)
+        self.day = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
+        self.timeout_id = None
+        self.timeout = 1000*3
+        self.shows = {}
+        self.pl = "Rock"
+        self.db = None
+        self.shell = None
+
+        #load all of the shows into the variable.
+        self.load_shows()
+
+    def activate(self, shell):
+        self.shell = shell
+        self.db = shell.props.db
+        self.player = self.shell.get_player()
+
+        #Initial timeout waits for 3 seconds then runs.
+        self.timeout_id = gobject.timeout_add(self.timeout,self.check_schedule)
+
+    def deactivate(self, shell):
+        del self.shell
+        del self.player
+        del self.db
+
+    def check_schedule(self):
+        t = localtime()
+
+        self.pl = self.shows[self.day[int(t.tm_wday)]][str(t.tm_hour)]
+
+        min_to_hour = 60 - int(t.tm_min)
+        self.timeout = 1000*(60*min_to_hour + int(t.tm_sec))
+        print self.timeout_id
+
+        self.get_genre(min_to_hour)
+        
+        if not self.player.props.playing:
+            self.player.playpause()
+
+        gobject.source_remove(self.timeout_id)
+        self.timeout_id = gobject.timeout_add(self.timeout,self.check_schedule)
+        print self.timeout
+        print self.timeout_id
+        return True
+
+    # boring load shows of the schedule stored in a local dictionary file.
+    def load_shows(self):
+        for day in self.day:
+            self.shows[day] = {}
+
+        PROJ_ROOT = os.path.dirname(os.path.realpath(__file__))
+        path = PROJ_ROOT+"/radiosched.csv"
+        fd = open(path)
+
+        show = fd.readline()
+        while show:
+            show = show.strip().split('|')
+            self.shows[show[4]][show[3]] = show[2]
+            show = fd.readline()
+
+    #send a 
+    def get_genre(self,time_duration):
+        genre = self.pl
+        db = self.shell.props.db
+        query = db.query_new()
+        db.query_append(query,[rhythmdb.QUERY_PROP_LIKE,
+            rhythmdb.PROP_GENRE, genre])
+        qm = db.query_model_new(query)
+        db.do_full_query_parsed(qm, query)
+
+        uri_loc= []
+        for row in qm:
+            entry = row[0]
+            duration = db.entry_get(entry, rhythmdb.PROP_DURATION)
+            location = db.entry_get(entry, rhythmdb.PROP_LOCATION)
+            uri_loc.append((location,duration))
+     
+        total_duration = 0
+        uri_loc = self.randomize(uri_loc)
+        try:
+            song = uri_loc.pop()
+        except:
+            pass
+
+        while uri_loc :
+            if total_duration + song[1] < time_duration*60:
+                total_duration += song[1]
+                self.shell.add_to_queue(song[0])
+            song = uri_loc.pop()
+
+    #this should be a sub routine of some other function it's only used to
+    # a list random.
+    def randomize(self,l):
+        length = len(l)
+        for i in range(length):
+            j = random.randint(i, length-1)
+            l[i], l[j] = l[j], l[i]
+        return l
diff --git a/schedule.rb-plugin b/schedule.rb-plugin
index bb732cd..7d9eed5 100644
--- a/schedule.rb-plugin
+++ b/schedule.rb-plugin
@@ -1,6 +1,6 @@
 [RB Plugin]
 Loader=python
-Module=Schedule
+Module=schedule
 IAge=1
 Name=Radio Schedule Plugin
 Description=An implementation of a radio schedule.
diff --git a/show.json b/show.json
deleted file mode 100644
index 9f16141..0000000
--- a/show.json
+++ /dev/null
@@ -1 +0,0 @@
-[{"pk": 1, "model": "show.show", "fields": {"title": "Rock", "url": "", "featured": false, "host": 1, "syndicated": false, "enable_comments": true, "slug": "rock"}}, {"pk": 5, "model": "show.show", "fields": {"title": "Blues", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "blues"}}, {"pk": 6, "model": "show.show", "fields": {"title": "Classic Rock", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "classic-rock"}}, {"pk": 7, "model": "show.show", "fields": {"title": "Country", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "country"}}, {"pk": 9, "model": "show.show", "fields": {"title": "Hip-Hop", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "hip-hop"}}, {"pk": 10, "model": "show.show", "fields": {"title": "Jazz", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "jazz"}}, {"pk": 13, "model": "show.show", "fields": {"title": "Punk", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "punk"}}, {"pk": 17, "model": "show.show", "fields": {"title": "Traditional", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "traditional"}}, {"pk": 15, "model": "show.show", "fields": {"title": "Secwepemcts\u00edn", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "secwepemctsin"}}, {"pk": 18, "model": "show.show", "fields": {"title": "World", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "world"}}, {"pk": 19, "model": "show.show", "fields": {"title": "Reggae", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "reggae"}}, {"pk": 14, "model": "show.show", "fields": {"title": "R&B", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "r-and-b"}}, {"pk": 12, "model": "show.show", "fields": {"title": "Native Solidarity News", "url": "http://www.ckut.ca/nsn/", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "native-solidarity-news"}}, {"pk": 16, "model": "show.show", "fields": {"title": "Spoken Word", "url": "", "featured": false, "host": 2, "syndicated": false, "enable_comments": true, "slug": "spoken-word"}}, {"pk": 8, "model": "show.show", "fields": {"title": "Deconstructing Dinner", "url": "http://www.cjly.net/deconstructingdinner/", "featured": false, "host": 2, "syndicated": true, "enable_comments": true, "slug": "deconstructing-dinner"}}, {"pk": 20, "model": "show.show", "fields": {"title": "The Bike Show", "url": "http://thebikeshow.net/", "featured": false, "host": 2, "syndicated": true, "enable_comments": true, "slug": "bike-show"}}, {"pk": 150, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 7, "show": 16}}, {"pk": 157, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 8, "show": 1}}, {"pk": 164, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 9, "show": 15}}, {"pk": 171, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 10, "show": 18}}, {"pk": 178, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 11, "show": 1}}, {"pk": 185, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 12, "show": 8}}, {"pk": 192, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 13, "show": 15}}, {"pk": 199, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 14, "show": 19}}, {"pk": 206, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 15, "show": 17}}, {"pk": 213, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 16, "show": 10}}, {"pk": 220, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 17, "show": 15}}, {"pk": 227, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 18, "show": 16}}, {"pk": 234, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 19, "show": 5}}, {"pk": 241, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 20, "show": 14}}, {"pk": 248, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 21, "show": 9}}, {"pk": 255, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 22, "show": 1}}, {"pk": 262, "model": "show.slot", "fields": {"dayofweek": 1, "hour": 23, "show": 9}}, {"pk": 269, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 7, "show": 16}}, {"pk": 158, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 8, "show": 1}}, {"pk": 165, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 9, "show": 15}}, {"pk": 172, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 10, "show": 18}}, {"pk": 179, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 11, "show": 1}}, {"pk": 186, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 12, "show": 16}}, {"pk": 193, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 13, "show": 15}}, {"pk": 200, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 14, "show": 18}}, {"pk": 207, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 15, "show": 17}}, {"pk": 214, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 16, "show": 10}}, {"pk": 221, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 17, "show": 15}}, {"pk": 228, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 18, "show": 16}}, {"pk": 235, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 19, "show": 1}}, {"pk": 242, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 20, "show": 14}}, {"pk": 249, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 21, "show": 9}}, {"pk": 256, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 22, "show": 9}}, {"pk": 263, "model": "show.slot", "fields": {"dayofweek": 2, "hour": 23, "show": 9}}, {"pk": 270, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 7, "show": 16}}, {"pk": 159, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 8, "show": 7}}, {"pk": 166, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 9, "show": 15}}, {"pk": 173, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 10, "show": 18}}, {"pk": 180, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 11, "show": 1}}, {"pk": 187, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 12, "show": 16}}, {"pk": 194, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 13, "show": 15}}, {"pk": 201, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 14, "show": 18}}, {"pk": 208, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 15, "show": 17}}, {"pk": 215, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 16, "show": 1}}, {"pk": 222, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 17, "show": 15}}, {"pk": 229, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 18, "show": 16}}, {"pk": 236, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 19, "show": 18}}, {"pk": 243, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 20, "show": 14}}, {"pk": 250, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 21, "show": 18}}, {"pk": 257, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 22, "show": 18}}, {"pk": 264, "model": "show.slot", "fields": {"dayofweek": 3, "hour": 23, "show": 18}}, {"pk": 271, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 7, "show": 16}}, {"pk": 160, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 8, "show": 18}}, {"pk": 167, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 9, "show": 15}}, {"pk": 174, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 10, "show": 18}}, {"pk": 181, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 11, "show": 8}}, {"pk": 188, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 12, "show": 17}}, {"pk": 195, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 13, "show": 15}}, {"pk": 202, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 14, "show": 19}}, {"pk": 209, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 15, "show": 17}}, {"pk": 216, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 16, "show": 1}}, {"pk": 223, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 17, "show": 15}}, {"pk": 230, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 18, "show": 12}}, {"pk": 237, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 19, "show": 1}}, {"pk": 244, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 20, "show": 14}}, {"pk": 251, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 21, "show": 9}}, {"pk": 258, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 22, "show": 9}}, {"pk": 265, "model": "show.slot", "fields": {"dayofweek": 4, "hour": 23, "show": 9}}, {"pk": 272, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 7, "show": 16}}, {"pk": 161, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 8, "show": 7}}, {"pk": 168, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 9, "show": 15}}, {"pk": 175, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 10, "show": 6}}, {"pk": 182, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 11, "show": 1}}, {"pk": 189, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 12, "show": 8}}, {"pk": 196, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 13, "show": 15}}, {"pk": 203, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 14, "show": 1}}, {"pk": 210, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 15, "show": 17}}, {"pk": 217, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 16, "show": 1}}, {"pk": 224, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 17, "show": 15}}, {"pk": 231, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 18, "show": 16}}, {"pk": 238, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 19, "show": 1}}, {"pk": 245, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 20, "show": 19}}, {"pk": 252, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 21, "show": 16}}, {"pk": 259, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 22, "show": 1}}, {"pk": 266, "model": "show.slot", "fields": {"dayofweek": 5, "hour": 23, "show": 16}}, {"pk": 273, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 7, "show": 16}}, {"pk": 162, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 8, "show": 7}}, {"pk": 169, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 9, "show": 15}}, {"pk": 176, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 10, "show": 18}}, {"pk": 183, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 11, "show": 20}}, {"pk": 190, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 12, "show": 10}}, {"pk": 197, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 13, "show": 15}}, {"pk": 204, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 14, "show": 10}}, {"pk": 211, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 15, "show": 17}}, {"pk": 218, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 16, "show": 5}}, {"pk": 225, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 17, "show": 15}}, {"pk": 232, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 18, "show": 16}}, {"pk": 239, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 19, "show": 1}}, {"pk": 246, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 20, "show": 14}}, {"pk": 253, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 21, "show": 1}}, {"pk": 260, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 22, "show": 9}}, {"pk": 267, "model": "show.slot", "fields": {"dayofweek": 6, "hour": 23, "show": 9}}, {"pk": 156, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 7, "show": 16}}, {"pk": 163, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 8, "show": 1}}, {"pk": 170, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 9, "show": 15}}, {"pk": 177, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 10, "show": 18}}, {"pk": 184, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 11, "show": 7}}, {"pk": 191, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 12, "show": 8}}, {"pk": 198, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 13, "show": 13}}, {"pk": 205, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 14, "show": 17}}, {"pk": 212, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 15, "show": 1}}, {"pk": 219, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 16, "show": 19}}, {"pk": 226, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 17, "show": 15}}, {"pk": 233, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 18, "show": 12}}, {"pk": 240, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 19, "show": 1}}, {"pk": 247, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 20, "show": 1}}, {"pk": 254, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 21, "show": 9}}, {"pk": 261, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 22, "show": 19}}, {"pk": 268, "model": "show.slot", "fields": {"dayofweek": 7, "hour": 23, "show": 9}}]
diff --git a/test.py b/test.py
index dc89f87..7307eb1 100644
--- a/test.py
+++ b/test.py
@@ -1,90 +1,5 @@
-#!/usr/bin/env python
-import random
-import unittest
-from ScheduleSlot import *
-import xml.dom.minidom
+import os
+PROJ_ROOT = os.path.dirname(os.path.realpath(__file__))
+path = PROJ_ROOT+"/radiosched.csv"
+print path
 
-
-
-class TestSequenceFunctions(unittest.TestCase):
-
-    def setUp(self):
-        """Creates a ScheduleDB object, and creates a songlist of typical pop
-        songs."""
-        self.sched = ScheduleDB()
-        self.songlist = []
-        for i in range(1000):
-            self.songlist.append((str(i),random.randint(100,500)))
-        self.stationids = []
-        for i in range(50):
-            self.stationids.append((str(i),random.randint(10,20)))
-    def test_open_db(self):
-        """Opens up a sqlite3 database."""
-        self.sched.open_db()
-    def test_get_genre(self):
-        """Tests the get genre against some known values."""
-        self.sched.open_db()
-        known_values = (
-                ('10','Monday',u'World'),
-                ('11','Tuesday',u'Rock'),
-                ('22','Monday',u'HipHop'))
-        for hour, dow, genre in known_values:
-            value = self.sched.get_genre(hour,dow)
-            self.assertEqual(genre,value)
-    def test_playlist_aroundanhour(self):
-        """Making sure the playlist is not way over an hour."""
-        playlist = self.sched.generate_playlist(self.songlist)
-        sum = 0
-        for song in playlist:
-            sum = sum + song[1]
-        self.assertEqual(sum < 60*60 + 90, True)
-    def test_playlist_is_different(self):
-        """Make sure a songlist produces two different playlists."""
-        self.assertEqual(self.songlist == self.songlist, True)
-        playlist1 = self.sched.generate_playlist(self.songlist)
-        playlist2 = self.sched.generate_playlist(self.songlist)
-        self.assertEqual(playlist1 == playlist2, False)
-    def test_mixup(self):
-        """Mixup a playlist and make sure that each element is original
-        songlist."""
-        for element in self.sched.mixup(self.songlist):
-            self.assertEqual(element not in self.songlist, False)
-    def test_average_playlist_length(self):
-        """Tests the average playlist length over a week worth of programming
-        and make sure it is less then 5 seconds."""
-        runs = 24*7
-
-        total_duration = 0
-        for run in range(runs):
-            playlist = self.sched.generate_playlist(self.songlist)
-            playlist_duration = 0
-            for song in playlist:
-                playlist_duration = playlist_duration + song[1]
-            total_duration = total_duration + playlist_duration
-        diff  = abs(3600-total_duration/runs)
-        self.assertEqual(diff < 10, True)
-    def test_genre_exists_in_rhythmdb(self):
-        rhythmdb = '/home/neskie/.local/share/rhythmbox/rhythmdb.xml'
-        doc = xml.dom.minidom.parse(rhythmdb)
-
-        genres = []
-        for e in doc.childNodes:
-            for songentry in e.childNodes:
-                for f in songentry.childNodes:
-                    if f.localName == 'genre':
-                        for q in  f.childNodes:
-                            genre = q.data
-                            if genre not in genres:
-                                genres.append(genre)
-
-        print genres
-        hour = '10'
-        dow = 'Monday'
-        self.sched.open_db()
-        for hour in range(7,23):
-            value = self.sched.get_genre(str(hour),dow)
-            print value
-            self.assertEqual(value in genres, True)
-
-if __name__ == '__main__':
-    unittest.main()

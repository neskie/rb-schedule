from datetime import datetime, timedelta
import json
import os
import unicodedata
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

def strip_accents(s):
       return ''.join((c for c in unicodedata.normalize('NFD', s) if
           unicodedata.category(c) != 'Mn'))

class ScheduleLoader():
    def __init__(self):
        ROOT =  os.path.dirname(os.path.realpath(__file__))
        show_json = os.path.join(ROOT, 'show.json')
        f = open(show_json)
        self.schedule  = json.load(f)
        f.close()

    def get_show(self, hour, dayofweek):
        '''Returns the playlist of the given the hour and day of week.'''
        dayofweek = dayofweek + 1

        slots = [ x for x in self.schedule if x['model'] == 'show.slot']
        shows = [ x for x in self.schedule if x['model'] == 'show.show']
        current_slot = [ x['fields']['show'] for x in slots if x['fields']['hour'] == hour and
                x['fields']['dayofweek'] == dayofweek ]
        if current_slot:
            current_show = [ x['fields'] for x in shows if x['pk'] == current_slot[0] ]
            current_show[0]['title'] = strip_accents(current_show[0]['title'])
            return current_show[0]
        else:
            return []

    def get_current_show(self):
        t = datetime.now()
        hour = t.hour
        dayofweek = t.weekday()
        return self.get_show(hour, dayofweek)
    def get_next(self):
        d = timedelta(hours=1)
        t = datetime.now() + d 
        hour = t.hour
        dayofweek = t.weekday()
        return self.get_show(hour, dayofweek)
    def get_last(self):
        d = timedelta(hours=-1)
        t = datetime.now() + d
        hour = t.hour
        dayofweek = t.weekday()
        return self.get_show(hour, dayofweek)
    def allowed_slots(self):
        slots = [ x for x in self.schedule if x['model'] == 'show.slot']
        return [ (slot['fields']['hour'], slot['fields']['dayofweek'] - 1) for slot in slots ]
    def __iter__(self):
        slots = self.allowed_slots()
        d = timedelta(hours=-1)
        t = datetime.now() + d
        hour = t.hour 
        dayofweek = t.weekday()
        idx = slots.index((hour,dayofweek))
        while True:
            idx += (idx + 1) % len(slots)
            hour, day = self.allowed_slots()[idx]
            yield self.get_show(hour, day)

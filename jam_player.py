import urllib,re
import tempfile
import sys, os, time, thread
import glib, gobject
import shutil as sh
import pygst
pygst.require("0.10")
import gst


class JamendoFetcher():
	
	def __init__(self, AlbumId):
		self.albumId = AlbumId
		self.tracks = []
		self._getTracksIds()

	def _getTracksIds(self):
		url = 'http://www.jamendo.com/pl/get2/track_id/track/xml/track_album+album_artist/?order=numalbum_asc&n=50&album_id=%d' % (self.albumId)
		trackurl = 'http://www.jamendo.com/pl/get2/stream/track/redirect/?id=%d&streamencoding=mp31'
		self.tracks = [ trackurl % (int(num)) for num in re.findall('<track>(\d+)</track>', urllib.urlopen(url).read())]

	def _fetchTrack(self,trackUrl):
		tmpfile = tempfile.NamedTemporaryFile(mode='wb',prefix='jamendo',suffix='.mp3', delete=False)
		file(tmpfile.name,'w+b').write(urllib.urlopen(trackUrl).read())
		return tmpfile.name

	def downloadTracks(self,prefix):
		x = 1
		for track in self.tracks:
			fname = self._fetchTrack(track)
			newfile = '%s_%d.mp3' % (prefix,x)
			sh.move(fname, newfile)
			x += 1
			print 'Track %s done' % newfile



class CLI_Main:
	def __init__(self,playlist):
		self.playlist = playlist
		self.player = gst.element_factory_make("playbin2", "player")
		fakesink = gst.element_factory_make("fakesink", "fakesink")
		self.player.set_property("video-sink", fakesink)
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.on_message)

	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
			self.playmode = False
		elif t == gst.MESSAGE_ERROR:
			self.player.set_state(gst.STATE_NULL)
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.playmode = False

	def start(self):
		for track in self.playlist:
			print 'Playing %s' % track
			self.playmode = True
			self.player.set_property("uri", track)
			self.player.set_state(gst.STATE_PLAYING)
			while self.playmode:
				time.sleep(1)
		time.sleep(1)
		loop.quit()



if __name__ == '__main__':
	jf = JamendoFetcher(int(sys.argv[1]))
	mainclass = CLI_Main(jf.tracks)
	thread.start_new_thread(mainclass.start, ())
	gobject.threads_init()
	loop = glib.MainLoop()
	loop.run()

	#jf.downloadTracks('StrangeZero')

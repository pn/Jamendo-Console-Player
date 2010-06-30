#!/usr/bin/env python
import urllib,re,tempfile,sys, os, subprocess
from optparse import OptionParser
import shutil as sh
import simplejson as json

player = 'mpg123'

class JamendoAlbum():
	def __init__(self, AlbumId):
		self.albumId = AlbumId
		self.tracks = []
		self._getTracksIds(self.albumId)

	def _getTracksIds(self,albumId):
		url = 'http://www.jamendo.com/pl/get2/track_id+artist_name+album_name+name/track/xml/track_album+album_artist/?order=numalbum_asc&n=50&album_id=%d' % (albumId)
		keys = ['track_id','artist_name','album_name','name']
		
		for line in urllib.urlopen(url).read().split('<track>'):
			track = {}
			for key in keys:
				data = re.findall('<%s>(.*)</%s>' % (key,key), line)
				if len(data)>0:
					track[key] = data[0]
				else:
					continue
			if len( track.keys() ) == len( keys ): #all data parsed correctly
				self.tracks.append( 
					JamendoTrack(	track['track_id'], track['artist_name'], track['album_name'], track['name']) 
				)

	def _fetchTrack(self,trackUrl):
		'''Download the file and return the name of the file '''
		tmpfile = tempfile.NamedTemporaryFile(mode='wb',prefix='jamendo',suffix='.mp3', delete=False)
		file(tmpfile.name,'w+b').write(urllib.urlopen(trackUrl).read())
		return tmpfile.name

	def downloadTracks(self):
		'''Download all tracks and store them in files of names starting with 'prefix' '''
		x = 1
		for track in self.tracks:
			fname = self._fetchTrack( track.url )
			newfile = '%s-%s-%d-%s.mp3' % (track.artist_name, track.album_name, x , track.name )
			sh.move(fname, newfile)
			x += 1
			print 'Track %s done' % newfile

class JamendoTrack():
	def __init__(self,trackId,artist,album,name):
		self.trackId = trackId
		self.artist  = artist
		self.album = album
		self.name = name
		#self.url = 'http://www.jamendo.com/pl/get2/stream/track/redirect/?id=%s&streamencoding=mp31' % (self.trackId)
		self.url = 'http://www.jamendo.com/pl/get2/stream/track/redirect/?id=%s' % (self.trackId)

	def playTrack(self):
		''''''
		print 'Playing:\n\tArtist: %s\n\tAlbum: %s\n\tTitle: %s\n%s'  %  ( self.artist,self.album,self.name,self.url)
		global player
		try:
			p = subprocess.Popen([player, self.url],stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
			p.wait()
		except:
			p.terminate()
		print


class JamendoRadio():
	def __init__(self,station=""):
		self.station = station	
		self.RadioId = self._getRadioId() or 0
	
	def _getRadioId(self):
		url = 'http://api.jamendo.com/get2/id+name+idstr/radio/plain/?radio_idstr=%s' % self.station
		ret = urllib.urlopen(url).read().split()
		if len(ret)==2:
			try:
				return int(ret[0])
			except:
				return None
		else:
			return None
	
	def _getRadioTracks(self):
		url = 'http://www.jamendo.com/get2/track_id/track/plain/radio_track_inradioplaylist/?order=numradio_asc&radio_id=%d' % (self.RadioId)
		return urllib.urlopen(url).read().split()
	
	def playRadio(self):
		url = 'http://www.jamendo.com/get/track/id/track/data/rss2/%s?ali=full&ari=full+object&tri=full&item_o=track_no_asc&showhidden=1&shownotmod=1'
		self.play = True
		while self.play:
			trackIds = self._getRadioTracks()
			if len(trackIds)>0:
				for tId in trackIds:
					trackInfo = re.findall( '<title>(.*) : (.*) - (.*)</title>',  urllib.urlopen(url % tId).read()) 
					if len(trackInfo)>0:
						try:
							track = JamendoTrack(tId,trackInfo[0][0],trackInfo[0][1],trackInfo[0][2])
							track.playTrack()
						except:
							self.play = False


if __name__ == '__main__':
	parser = OptionParser(usage="usage: %prog [options] JamendoAlbumId")
	parser.add_option("-p", "--play",  action="store_true",    help="Play Jamendo album of specified ID" )
	parser.add_option("-d", "--download", action="store_true",  help="Download Jamendo album of specified ID")
	parser.add_option("-r", "--radio", action="store",  help="Play Jamendo radio",metavar="RADIO_NAME")
	(options, args) = parser.parse_args()
	
	if options.radio==None:
		if len(args) != 1:
			parser.error("Incorrect number of arguments")
		try:
			aId = int(args[0])
		except:
			parser.error("Wrong AlbumId")
			sys.exit()
		ja = JamendoAlbum(aId)
		if len(ja.tracks)>0:
			if options.download:
				ja.downloadTracks()
			if options.play:
				for track in ja.tracks:
					track.playTrack()
					track.playTrack()
		else:
			print "0 tracks to play/download"
	else:
		jr = JamendoRadio(options.radio)
		if jr.RadioId>0:
			jr.playRadio()
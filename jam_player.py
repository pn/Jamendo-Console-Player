#!/usr/bin/env python
import urllib,re,tempfile,sys, os, subprocess
from optparse import OptionParser
import shutil as sh

player = 'mpg123'

class JamendoFetcher():
	def __init__(self, AlbumId):
		self.albumId = AlbumId
		self.tracks = []
		self._getTracksIds(self.albumId)

	def _getTracksIds(self,albumId):
		url = 'http://www.jamendo.com/pl/get2/track_id+artist_name+album_name+name/track/xml/track_album+album_artist/?order=numalbum_asc&n=50&album_id=%d' % (albumId)
		trackurl = 'http://www.jamendo.com/pl/get2/stream/track/redirect/?id=%s&streamencoding=mp31'
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
				track['url'] = trackurl % (track['track_id'])
				self.tracks.append(track)

	def _fetchTrack(self,trackUrl):
		'''Download the file and return the name of the file '''
		tmpfile = tempfile.NamedTemporaryFile(mode='wb',prefix='jamendo',suffix='.mp3', delete=False)
		file(tmpfile.name,'w+b').write(urllib.urlopen(trackUrl).read())
		return tmpfile.name

	def downloadTracks(self,prefix='JamendoTrack'):
		'''Download all tracks and store them in files of names starting with 'prefix' '''
		x = 1
		for track in self.tracks:
			fname = self._fetchTrack(track['url'] )
			newfile = '%s_%d.mp3' % (prefix,x)
			sh.move(fname, newfile)
			x += 1
			print 'Track %s done' % newfile


if __name__ == '__main__':
	parser = OptionParser(usage="usage: %prog [options] JamendoAlbumId")
	parser.add_option("-p", "--play",  action="store_true",    help="Play Jamendo album of specified ID" )
	parser.add_option("-d", "--download", action="store_true",  help="Download Jamendo album of specified ID")
	parser.add_option("-x", "--prefix",   dest="prefix" , action="store", help="Use 'prefix' as base file name for downloaded files", metavar="PREFIX", default=False)
	(options, args) = parser.parse_args()
	
	if len(args) != 1:
		parser.error("Incorrect number of arguments")
	try:
		aId = int(args[0])
	except:
		parser.error("Wrong AlbumId")
		sys.exit()
	jf = JamendoFetcher(aId)
	if options.download:
		if options.prefix != False:
			jf.downloadTracks(options.prefix)
		else:
			jf.downloadTracks()
	if options.play:
		for track in jf.tracks:
			print 'Playing:\n\tArtist: %s\n\tAlbum: %s\n\tTitle: %s' %  ( track['artist_name'] ,track['album_name'] ,track['name'] )
			try:
				p = subprocess.Popen([player, track['url'] ],stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
				p.wait()
			except:
				p.terminate()
			print
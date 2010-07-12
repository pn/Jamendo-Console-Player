#!/usr/bin/env python
'''
Copyright (C) Satanowski
'''

import urllib,re,tempfile,sys, os, subprocess
from optparse import OptionParser
import shutil as sh

player = 'mpg123'

def wget(url):
	try:
		ret =  urllib.urlopen(url).read()
	except IOError: 
		print "\nError: There's something wrong with the network! Maybe your proxy settings are incorrect?\n"
		ret = None
	return ret


class JamendoAlbum():
	def __init__(self, AlbumId):
		self.albumId = AlbumId
		self.tracks = []
		self._getTracksIds()

	def _getTracksIds(self):
		url = 'http://api.jamendo.com/get2/track_id+artist_name+album_name+name/track/xml/track_album+album_artist/?order=numalbum_asc&n=50&album_id=%d' % (self.albumId)
		keys = ['track_id','artist_name','album_name','name']
		tracks_xml =  (wget(url) or '').split('<track>')
		for line in tracks_xml:
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

	def downloadTracks(self):
		x = 1
		for jtrack in self.tracks:
			print 'Downloading track %s' % (jtrack)
			jtrack.download("%s-%s-%d-%s.mp3'" % (self.artist, self.album, x, self.name) )
			x += 1
			print 'Track %s done' % newfile
	
	def __repr__(self):
		return  "<JamendoAlbum: id:%d tracks:%s>" % ( self.albumId, ','.join( [str(jt.trackId) for jt in self.tracks] ))
	
	def __str__(self):
		artists  = list(set(["'%s'" % jt.artist for jt in self.tracks]))
		albums = list(set(["'%s'" % jt.album for jt in self.tracks]))
		return  "[JamendoAlbum: id:%d Artist(s):%s Album(s):%s]" % ( self.albumId, ', '.join(artists) , ', '.join(albums) )



class JamendoTrack():
	def __init__(self,trackId,artist,album,name):
		self.trackId = trackId
		self.artist  = artist
		self.album = album
		self.name = name
		#self.url = 'http://www.jamendo.com/pl/get2/stream/track/redirect/?id=%s&streamencoding=mp31' % (self.trackId)
		self.url = 'http://api.jamendo.com/get2/stream/track/redirect/?id=%s' % (self.trackId)
		self.trackFileName = "%s-%s-%s.mp3" % (self.artist, self.album, self.name) 

	def _fetchTrack(self,trackUrl):
		track  = wget(trackUrl)
		if track != None:
			try:
				tmpfile = tempfile.NamedTemporaryFile(mode='wb',prefix='jamendo',suffix='.mp3', delete=False)
				file(tmpfile.name,'w+b').write(track)
			except IOError:
				print "\nError: Cannot write down the track. \n"
				return ''
		return tmpfile.name
	
	def download(self,fname=None):
		filename = (fname or self.trackFileName)
		tmpname = self._fetchTrack( self.url )
		if tmpname != '':
			sh.move(tmpname, fname)

	def playTrack(self):
		''''''
		print 'Playing track: %s\n%s\n'  %  ( self.url, self.__str__())
		global player
		#maybe it is already downloaded
		if os.access(self.trackFileName, os.F_OK):
			track_file = self.trackFileName
			print 'playing from local file: %s' % (track_file)
		else:
			track_file = None
		p = None
		try:
			p = subprocess.Popen([player, track_file or self.url],stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
			p.wait()
		except:
			if p: p.terminate()
		print
	
	def __repr__(self):
		return "<JamendoTrack id:%s, artist:%s, album:%s, title:%s>" % (self.trackId, self.artist, self.album, self.name)
	
	def __str__(self):
		return "[artist:%s, album:%s, title:%s]" % (self.artist, self.album, self.name)


class JamendoRadio():
	def __init__(self,station=""):
		self.station = station	
		self.radioId = self._getRadioId() or 0
	
	def _getRadioId(self):
		url = 'http://api.jamendo.com/get2/id+name+idstr/radio/plain/?radio_idstr=%s' % self.station
		ret = (wget(url) or '').split()
		if len(ret)==2:
			try:
				return int(ret[0])
			except:
				return None
		else:
			return None
	
	def _getRadioTracks(self):
		print 'Getting the list of new tracks for radio "%s"...\n' %  (self.station)
		url = 'http://api.jamendo.com/get2/track_id/track/plain/radio_track_inradioplaylist/?order=numradio_asc&radio_id=%d' % (self.radioId)
		return (wget(url) or '').split()
	
	def playRadio(self):
		url = 'http://api.jamendo.com/get/track/id/track/data/rss2/%s?ali=full&ari=full+object&tri=full&item_o=track_no_asc&showhidden=1&shownotmod=1'
		self.play = True
		while self.play:
			trackIds = self._getRadioTracks()
			if len(trackIds)>0:
				for tId in trackIds:
					trackInfo = re.findall( '<title>(.*) : (.*) - (.*)</title>',  wget(url % tId)  or '' ) 
					if len(trackInfo)>0:
						if trackInfo[0][0] == 'jamradio jingles': 
							print '\nSkipping the Jamendo jingle\n'
							continue
						try:
							track = JamendoTrack(tId,trackInfo[0][0],trackInfo[0][1],trackInfo[0][2])
							track.playTrack()
						except:
							self.play = False
			else:
				print "No tracks to play!"
				sys.exit()
	
	def __repr__(self):
		return  "<JamendoRadio: id:%d station:%s>" % ( self.radioId, self.station)

	def __str__(self):
		return  "[JamendoRadio: id:%d station:%s]" % ( self.radioId, self.station)


if __name__ == '__main__':
	found_player = False
	for path in os.environ["PATH"].split(os.pathsep):
		fpath = "%s/%s" % (path, player)
		if os.path.exists(fpath) and os.access(fpath, os.X_OK):
			found_player = True
	
	if not found_player:
	    print "Can't find payer: " + player
	    sys.exit()

	parser = OptionParser(usage="usage: %prog [options] JamendoAlbumId")
	parser.add_option("-p", "--play",  action="store_true",    help="Play Jamendo album of specified ID" )
	parser.add_option("-d", "--download", action="store_true",  help="Download Jamendo album of specified ID")
	parser.add_option("-r", "--radio", action="store",  help="Play Jamendo radio",metavar="RADIO_NAME")
	(options, args) = parser.parse_args()


	if options.play == None and options.download == None and options.radio == None:
		options.play = True  #default mode
	
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
		else:
			print "0 tracks to play/download"
	else:
		jr = JamendoRadio(options.radio)
		if jr.radioId>0:
			jr.playRadio()
		else:
			print "\nThere's no such radio station or its playlist is empty!\n"

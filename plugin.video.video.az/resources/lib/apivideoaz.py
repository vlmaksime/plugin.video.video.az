﻿# -*- coding: utf-8 -*-
# Module: apivideoaz
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import requests
import re

class VideoAzApiError(Exception):
    def __init__(self, value, code):
         self.value = value
         self.code = code

class videoaz:

    def __init__( self, params = {} ):

        self.__movie = []
        self.__video = []
        self.__tvseries = []
        self.__episodes = []

        #Settings
        self.__settings = {'cfduid':        params.get('cfduid'),
                           'episode_title': params.get('episode_title', 'Episode'),
                           'season_title':  params.get('season_title','Season'),
                           'video_stream':  params.get('video_stream', 'mp4'),
                           'video_quality': params.get('video_quality', 'HD'),
                           'rating_source': params.get('rating_source', 'imdb')}

        #Инициализация
        base_url = 'http://api.baku.video'

        #Links example
        #http://api.baku.video:80/movie/browse?page=1&category=0&lang=0&genre=0&keyword=
        #http://api.baku.video:80/movie/by_id?id=12077
        #http://api.baku.video:80/tvseries/browse?page=1&keyword=
        #http://api.baku.video:80/tvseries/browse_episodes?tvserie_id=344&season=2
        #http://api.baku.video:80/category/movie
        #http://api.baku.video:80/category/genre
        #http://api.baku.video:80/main
        #http://api.baku.video:80/video/browse?page=1&category=0&keyword=
        #http://api.baku.video:80/category/video
        #http://api.baku.video:80/video/by_id?id=159153

        self.__actions = {'main':            {'type': 'get', 'url': base_url + '/main'},
                          'playlist_xml':    {'type': 'get'},
                          #movie
                          'category_movie':  {'type': 'get', 'url': base_url + '/category/movie'},
                          'category_genre':  {'type': 'get', 'url': base_url + '/category/genre'},
                          'browse_movie':    {'type': 'get', 'url': base_url + '/movie/browse'},
                          'get_info_movie':  {'type': 'get', 'url': base_url + '/movie/by_id'},
                          #tvseries
                          'browse_tvseries': {'type': 'get', 'url': base_url + '/tvseries/browse'},
                          'browse_episodes': {'type': 'get', 'url': base_url + '/tvseries/browse_episodes'},
                          #video
                          'category_video':  {'type': 'get', 'url': base_url + '/category/video'},
                          'browse_video':    {'type': 'get', 'url': base_url + '/video/browse'},
                          'get_info_video':  {'type': 'get', 'url': base_url + '/video/by_id'}}

    def __get_setting( self, id, default='' ):
        return self.__settings.get(id, default)

    def __set_setting( self, id, value ):
        self.__settings[id] = value

    def __http_request( self, action, params = {}, data={}, url='' ):
        action_settings = self.__actions.get(action)

        user_agent = 'Mozilla/5.0 (Linux; Android 5.1; KODI) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/40.0.2214.124 Mobile Safari/537.36'

        url = action_settings.get('url', url)
        cookies = {}
        cfduid = self.__get_setting('cfduid')
        if cfduid:
            cookies['__cfduid'] = cfduid

        headers = {'User-Agent': user_agent}

        request_type = action_settings.get('type', 'post')
        try:
            if request_type == 'post':
                r = requests.post(url, data=data, params=params, headers=headers, cookies=cookies)
            elif request_type == 'get':
                r = requests.get(url, data=data, params=params, headers=headers, cookies=cookies)
            else:
                raise VideoAzApiError('Wrong request_type %s' % (request_type), 1)

            r.raise_for_status()
        except requests.ConnectionError as err:
            raise VideoAzApiError('Connection error', 1)

        return r

    def get_cfduid( self ):

        r = self.__http_request('main')
        cfduid = r.cookies.get('__cfduid', '')
        self.__set_setting('cfduid', cfduid)
        return cfduid

    def browse_video( self, params ):

        u_params = {'page':     params.get('page', 1),
                    'category': params.get('category', 0),
                    'keyword':  params.get('keyword', '')}

        r = self.__http_request('browse_video', u_params)
        j = r.json()

        if type(j) == list:
            self.__video = []
        else:
            self.__video = j.get('video', [])

        result = {'count': len(self.__video),
                  'list':  self.__make_list('video')}
        return result

    def browse_movie( self, params ):

        u_params = {'page':     params.get('page', 1),
                    'category': params.get('category', 0),
                    'lang':     params.get('lang', 0),
                    'genre':    params.get('genre', 0),
                    'keyword':  params.get('keyword', '')}

        r = self.__http_request('browse_movie', u_params)
        j = r.json()

        if type(j) == list:
            self.__movie = []
        else:
            self.__movie = j.get('movie', [])

        result = {'count': len(self.__movie),
                  'list':  self.__make_list('movie')}
        return result

    def browse_movie_related( self, id):
        u_params = {'id': id}

        r = self.__http_request('get_info_movie', u_params)
        j = r.json()
        self.__movie = j.get('related',[])

        result = {'count': len(self.__movie),
                  'list':  self.__make_list('movie')}
        return result

    def get_movie_details( self, id):
        u_params = {'id': id}

        r = self.__http_request('get_info_movie', u_params)
        j = r.json()
        self.__movie = j['player']

        details = self.__get_details('movie')
        return details

    def browse_tvseries( self, params ):

        u_params = {'page':    params.get('page', 1),
                    'keyword': params.get('keyword', '')}

        r = self.__http_request('browse_tvseries', u_params)
        j = r.json()

        if type(j) == list:
            self.__tvseries = []
        else:
            self.__tvseries = j.get('tvseries', [])

        result = {'count': len(self.__tvseries),
                  'list':  self.__make_list('tvseries')}
        return result

    def browse_episodes( self, params ):

        u_params = {'tvserie_id': params.get('tvserie_id', 0),
                    'season':     params.get('season', 0)}

        r = self.__http_request('browse_episodes', u_params)
        j = r.json()

        self.__episodes = j.get('episodes', [])
        self.__tvseries = j.get('tvseries')

        result = {'count': len(self.__episodes),
                  'title': self.__tvseries['title'],
                  'list':  self.__make_list('episodes', params )}
        return result

    def browse_seasons( self, params ):

        u_params = {'tvserie_id': params.get('tvserie_id', 0),
                    'season':     params.get('season', 0)}

        r = self.__http_request('browse_episodes', u_params)
        j = r.json()

        self.__episodes = j.get('episodes', [])
        self.__tvseries = j.get('tvseries')

        result = {'count': len(self.__tvseries['season_list']),
                  'title': self.__tvseries['title'],
                  'list':  self.__make_list('seasons')}
        return result

    def category_video( self ):
        r = self.__http_request('category_video')
        j = r.json()

        list = []
        for item in j:
            list.append(j[item])

        return list

    def category_movie( self ):
        r = self.__http_request('category_movie')
        j = r.json()

        list = []
        for item in j:
            list.append(j[item])

        return list

    def category_genre( self ):
        r = self.__http_request('category_genre')
        j = r.json()

        list = []
        for item in j:
            list.append(j[item])

        return list

    def get_video_url( self, params ):
        video_stream  = self.__get_setting('video_stream')
        video_quality = self.__get_setting('video_quality')

        type = params['type']
        if type == 'movie':
            u_params = {'id': params['id']}

            r = self.__http_request('get_info_movie', u_params)
            j = r.json()
            self.__movie = j['player']

            mp4_path = self.__movie['video']

            item_info = {'label':  self.__movie['title'],
                         'art':    { 'poster': self.__movie['thumb'].replace('thumb','cover') },
                         'info':   { 'video': {'mediatype': 'movie'} },
                         'fanart': self.__movie['thumb'],
                         'thumb':  self.__movie['thumb']}

            details = self.__get_details('movie')
            del details['video_quality']
            del details['audio_quality']
            item_info['info']['video'].update(details)

        elif type == 'episodes':
            u_params = {'tvserie_id': params['tvserie_id'],
                        'season':     params['season']}

            r = self.__http_request('browse_episodes', u_params)
            j = r.json()
            self.__episodes = j.get('episodes', [])
            self.__tvseries = j.get('tvseries')
            for episode in self.__episodes:
                if episode['id'] == params['id']:
                    u_params['episode'] = episode['episode']
                    mp4_path = episode['video']

                    label = '%s. %s %s %s %s' % (self.__tvseries['title'], self.__get_setting('season_title'), params['season'], self.__get_setting('episode_title'), episode['episode'])
                    item_info = {'label':  label,
                                 'art':    { 'poster': self.__tvseries['thumb'].replace('thumb','cover') },
                                 'info':   { 'video': {'mediatype': 'movie'} },
                                 'fanart': self.__tvseries['thumb'],
                                 'thumb':  self.__tvseries['thumb']}
        elif type == 'video':
            u_params = {'id': params['id']}

            r = self.__http_request('get_info_video', u_params)
            j = r.json()
            self.__video = j['player']

            mp4_path = self.__video['video_sd']

            item_info = {'label':  self.__video['title'],
                         'info': { 'video': {'genre': self.__video['categories'],
                                                   'mediatype': 'video'} },
                         'fanart': self.__video['large'],
                         'thumb':  self.__video['medium']}

        if video_stream == 'm3u8':
            m3u8_path = self.__get_playlist_url(type, u_params)
            path = m3u8_path if m3u8_path != '' else mp4_path
        else:
            path = mp4_path

        if type == 'video' and video_quality == 'HD' and self.__video['is_hd'] == '1':
            path = path.replace('sd.mp4', 'hd.mp4')

        item_info['path'] = path
        return item_info

    def __make_list( self, source, params = {} ):

        if source == 'movie':
            for movie in self.__movie:
                video_info = {'type': source,
                              'id':   movie['id']}

                title = movie['title']
                title_orig = movie['title_original'] if movie['title_original'] != '' else movie['title']
                item_info = {'label':  title,
                             'info': { 'video': {'year':          int(movie['year']) if movie['year'] else 0,
                                                 'title':         title,
                                                 'originaltitle': title_orig,
                                                 'sorttitle':     title,
                                                 'genre':         movie['genres'],
                                                 'mediatype':    'movie'} },
                             'art': { 'poster': movie['cover'] },
                             'fanart': movie['cover'].replace('cover','thumb'),
                             'thumb':  movie['cover'].replace('cover','thumb')}

                video_info = {'item_info':  item_info,
                              'video_info': video_info}
                yield video_info

        elif source == 'tvseries':
            for tvseries in self.__tvseries:

                video_info = {'type':   source,
                              'id':     tvseries['id'],
                              'season': tvseries['season']}

                title = tvseries['title']
                title_orig = tvseries['title_original'] if tvseries['title_original'] != '' else tvseries['title']
                item_info = {'label':  title,
                             'info': { 'video': {'title':         title,
                                                 'originaltitle': title_orig,
                                                 'tvshowtitle':   title_orig,
                                                 'sorttitle':     title,
                                                 'mediatype':    'tvshow'} },
                             'art': { 'poster': tvseries['cover'] },
                             'fanart': tvseries['cover'].replace('cover','thumb'),
                             'thumb':  tvseries['cover'].replace('cover','thumb')}

                video_info = {'item_info':  item_info,
                              'video_info': video_info}
                yield video_info

        elif source == 'episodes':
            season_title = self.__get_setting('season_title')
            episode_title = self.__get_setting('episode_title')

            title = self.__tvseries['title']
            title_orig = self.__tvseries['title_original'] if self.__tvseries['title_original'] != '' else self.__tvseries['title']

            for episode in self.__episodes:
                video_info = {'type':       source,
                              'id':         episode['id'],
                              'tvserie_id': self.__tvseries['id'],
                              'season':     params['season']}

                title_part = '%s %s %s %s' % (season_title, params['season'], episode_title, episode['episode'])
                title_full = '%s. %s' % (title, title_part)
                title_orig_full = '%s. %s' % (title_orig, title_part)

                item_info = {'label': title_full,
                             'info':  { 'video': {'title':         title_full,
                                                  'originaltitle': title_orig_full,
                                                  'tvshowtitle':   title_orig,
                                                  'sorttitle':     title,
                                                  'season':        int(params['season']),
                                                  'episode':       int(episode['episode']),
                                                  'mediatype':    'episode'} },
                             'art': { 'poster': self.__tvseries['thumb'].replace('thumb','cover') },
                             'fanart': self.__tvseries['thumb'],
                             'thumb':  self.__tvseries['thumb']}

                video_info = {'item_info':  item_info,
                              'video_info': video_info}
                yield video_info

        elif source == 'seasons':
            season_title = self.__get_setting('season_title')

            title = self.__tvseries['title']
            title_orig = self.__tvseries['title_original'] if self.__tvseries['title_original'] != '' else self.__tvseries['title']

            for season in self.__tvseries['season_list']:
                video_info = {'type':       source,
                              'tvserie_id': self.__tvseries['id'],
                              'season':     season}

                title_part = '%s %s' % (season_title, season)
                title_full = '%s. %s' % (title_part, title)
                title_orig_full = '%s. %s' % (title_part, title_orig)
                item_info = {'label':  title_full,
                             'info':  { 'video': {'title':         title_full,
                                                  'originaltitle': title_orig_full,
                                                  'tvshowtitle':   title,
                                                  'sorttitle':     title,
                                                  'season':        int(season),
                                                  'mediatype':    'season'} },
                             'art': { 'poster': self.__tvseries['thumb'].replace('thumb','cover') },
                             'fanart': self.__tvseries['thumb'],
                             'thumb':  self.__tvseries['thumb']}

                video_info = {'item_info':  item_info,
                              'video_info': video_info}
                yield video_info

        elif source == 'video':
            for video in self.__video:
                video_info = {'type': source,
                              'id':   video['id']}

                item_info = {'label':  video['title'],
                             'fanart': video['large'],
                             'thumb':  video['medium'],
                             'info':   { 'video': {'genre':      video['categories'],
                                                   'sorttitle':  video['title'],
                                                   'mediatype': 'video'} },
                             'art':    { 'poster': video['medium'] } }

                video_info = {'item_info':  item_info,
                              'video_info': video_info}
                yield video_info

    def __get_playlist_url( self, type, params ):
        import xml.etree.cElementTree as etree
        try:
            etree.fromstring('<?xml version="1.0"?><foo><bar/></foo>')
        except TypeError:
            import xml.etree.ElementTree as etree

        if type == 'movie':
            xml_url = 'http://video.az/jw/movie/xml/%s' % (params['id'])
        elif type == 'episodes':
            xml_url = 'http://video.az/jw/tvseries/xml/%s/%s/%s' % (params['tvserie_id'], params['season'], params['episode'])
        elif type == 'video':
            xml_url = 'http://video.az/jw/video/xml/%s' % (params['id'])
        else:
            xml_url = ''

        file = ''

        if xml_url != '':
            try:
                r = self.__http_request('playlist_xml', url=xml_url)
            except VideoAzApiError:
                return file

            root = etree.fromstring(r.text.encode('utf-8'))
            for sources in root.iter('{http://rss.jwpcdn.com/}source'):
                curfile = sources.attrib.get('file')
                if curfile[-4:] == 'm3u8':
                    file = curfile
                    break

        return file
    
    def __get_details(self, type):
        rating_field = self.__get_setting('rating_source') + '_rating'

        if type == 'movie':
            movie = self.__movie
            
            duration_str = movie['duration']
            duration_sec = 0
            for part in duration_str.split(':'):
                duration_sec = duration_sec * 60 + int(part)
            
            details = {'rating':   float(movie[rating_field]),
                       'genre':    movie['genres'], #.split(', ') if movie['genres'] else [],
                       'cast':     movie['actors'].split(', ') if movie['actors'] else [],
                       'country':  movie['country'], #.split(', ') if movie['country'] else [],
                       'director': movie['director'],
                       'writer':   movie['script'],
                       'tagline':  movie['slogan'],
                       'video_quality': movie['video_quality'],
                       'audio_quality': movie['audio_quality'],
                       'duration': duration_sec,
                       'plot':     self.__remove_html(movie['description']),
                       'mpaa':     self.__get_mpaa(movie['age_restriction'])}
        else:
            details = {}
        return details

    def __get_mpaa( self, age_restriction ):
        if age_restriction == u'Без ограничений':
            return 'G'
        elif age_restriction.find('6+') >= 0:
            return 'PG'
        elif age_restriction.find('12+') >= 0:
            return 'PG-13'
        elif age_restriction.find('16+') >= 0:
            return 'R'
        elif age_restriction.find('18+') >= 0:
            return 'NC-17'
        else:
            return ''

    def __remove_html( self, text ):
        result = text
        result = result.replace(u'&nbsp;',      u' ')
        result = result.replace(u'&pound;',     u'£')
        result = result.replace(u'&euro;',      u'€')
        result = result.replace(u'&para;',      u'¶')
        result = result.replace(u'&sect;',      u'§')
        result = result.replace(u'&copy;',      u'©')
        result = result.replace(u'&reg;',       u'®')
        result = result.replace(u'&trade;',     u'™')
        result = result.replace(u'&deg;',       u'°')
        result = result.replace(u'&plusmn;',    u'±')
        result = result.replace(u'&frac14;',    u'¼')
        result = result.replace(u'&frac12;',    u'½')
        result = result.replace(u'&frac34;',    u'¾')
        result = result.replace(u'&times;',     u'×')
        result = result.replace(u'&divide;',    u'÷')
        result = result.replace(u'&fnof;',      u'ƒ')
        result = result.replace(u'&Alpha;',     u'Α')
        result = result.replace(u'&Beta;',      u'Β')
        result = result.replace(u'&Gamma;',     u'Γ')
        result = result.replace(u'&Delta;',     u'Δ')
        result = result.replace(u'&Epsilon;',   u'Ε')
        result = result.replace(u'&Zeta;',      u'Ζ')
        result = result.replace(u'&Eta;',       u'Η')
        result = result.replace(u'&Theta;',     u'Θ')
        result = result.replace(u'&Iota;',      u'Ι')
        result = result.replace(u'&Kappa;',     u'Κ')
        result = result.replace(u'&Lambda;',    u'Λ')
        result = result.replace(u'&Mu;',        u'Μ')
        result = result.replace(u'&Nu;',        u'Ν')
        result = result.replace(u'&Xi;',        u'Ξ')
        result = result.replace(u'&Omicron;',   u'Ο')
        result = result.replace(u'&Pi;',        u'Π')
        result = result.replace(u'&Rho;',       u'Ρ')
        result = result.replace(u'&Sigma;',     u'Σ')
        result = result.replace(u'&Tau;',       u'Τ')
        result = result.replace(u'&Upsilon;',   u'Υ')
        result = result.replace(u'&Phi;',       u'Φ')
        result = result.replace(u'&Chi;',       u'Χ')
        result = result.replace(u'&Psi;',       u'Ψ')
        result = result.replace(u'&Omega;',     u'Ω')
        result = result.replace(u'&alpha;',     u'α')
        result = result.replace(u'&beta;',      u'β')
        result = result.replace(u'&gamma;',     u'γ')
        result = result.replace(u'&delta;',     u'δ')
        result = result.replace(u'&epsilon;',   u'ε')
        result = result.replace(u'&zeta;',      u'ζ')
        result = result.replace(u'&eta;',       u'η')
        result = result.replace(u'&theta;',     u'θ')
        result = result.replace(u'&iota;',      u'ι')
        result = result.replace(u'&kappa;',     u'κ')
        result = result.replace(u'&lambda;',    u'λ')
        result = result.replace(u'&mu;',        u'μ')
        result = result.replace(u'&nu;',        u'ν')
        result = result.replace(u'&xi;',        u'ξ')
        result = result.replace(u'&omicron;',   u'ο')
        result = result.replace(u'&pi;',        u'π')
        result = result.replace(u'&rho;',       u'ρ')
        result = result.replace(u'&sigmaf;',    u'ς')
        result = result.replace(u'&sigma;',     u'σ')
        result = result.replace(u'&tau;',       u'τ')
        result = result.replace(u'&upsilon;',   u'υ')
        result = result.replace(u'&phi;',       u'φ')
        result = result.replace(u'&chi;',       u'χ')
        result = result.replace(u'&psi;',       u'ψ')
        result = result.replace(u'&omega;',     u'ω')
        result = result.replace(u'&larr;',      u'←')
        result = result.replace(u'&uarr;',      u'↑')
        result = result.replace(u'&rarr;',      u'→')
        result = result.replace(u'&darr;',      u'↓')
        result = result.replace(u'&harr;',      u'↔')
        result = result.replace(u'&spades;',    u'♠')
        result = result.replace(u'&clubs;',     u'♣')
        result = result.replace(u'&hearts;',    u'♥')
        result = result.replace(u'&diams;',     u'♦')
        result = result.replace(u'&quot;',      u'"')
        result = result.replace(u'&amp;',       u'&')
        result = result.replace(u'&lt;',        u'<')
        result = result.replace(u'&gt;',        u'>')
        result = result.replace(u'&hellip;',    u'…')
        result = result.replace(u'&prime;',     u'′')
        result = result.replace(u'&Prime;',     u'″')
        result = result.replace(u'&ndash;',     u'–')
        result = result.replace(u'&mdash;',     u'—')
        result = result.replace(u'&lsquo;',     u'‘')
        result = result.replace(u'&rsquo;',     u'’')
        result = result.replace(u'&sbquo;',     u'‚')
        result = result.replace(u'&ldquo;',     u'“')
        result = result.replace(u'&rdquo;',     u'”')
        result = result.replace(u'&bdquo;',     u'„')
        result = result.replace(u'&laquo;',     u'«')
        result = result.replace(u'&raquo;',     u'»')

        # result = result.replace(u'<br>',    u'\n')

        return re.sub('<[^<]+?>', '', result)

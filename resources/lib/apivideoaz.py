# -*- coding: utf-8 -*-
# Module: apivideoaz
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import requests
import xml.etree.ElementTree as ET

class videoaz:
 
    def __init__( self, params = {}, debug = False ):

        self.__debug = debug

        self.__movie = []
        self.__tvseries = []
        self.__episodes = []
        
        #Инициализация настроек
        self.__settings = {'cfduid':        params.get('cfduid'),
                           'episode_title': params.get('episode_title', 'Episode'),
                           'season_title':  params.get('season_title','Season'),
                           'video_source':  params.get('video_source', 'm3u8')}
    
        #Инициализация 
        base_url = 'http://api.baku.video'

        #http://api.baku.video:80/movie/browse?page=1&category=0&lang=0&genre=0&keyword=
        #http://api.baku.video:80/movie/by_id?id=12077
        #http://api.baku.video:80/tvseries/browse?page=1&keyword=
        #http://api.baku.video:80/tvseries/browse_episodes?tvserie_id=344&season=2
        #http://api.baku.video:80/category/movie
        #http://api.baku.video:80/category/genre
        #http://api.baku.video:80/main
        #http://api.baku.video:80/video/browse?page=1&category=0&keyword=
        #http://api.baku.video:80/category/video
        
        self.__actions = {'main':            {'type': 'get', 'url': base_url + '/main'},
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
                          'browse_video':    {'type': 'get', 'url': base_url + '/video/browse'}}


    def __debuglog( self, string ):
        if self.__debug: print(string)
        
    def __get_setting( self, id, default='' ):
        return self.__settings.get(id, default)

    def __set_setting( self, id, value ):
        self.__settings[id] = value

    def __http_request( self, action, params = {}, data={} ):
        action_settings = self.__actions.get(action)

        user_agent = 'Mozilla/5.0 (Linux; Android 5.1; KODI) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/40.0.2214.124 Mobile Safari/537.36'

        url = action_settings['url']
        cookies = {}
        cfduid = self.__get_setting('cfduid')
        if cfduid:
            cookies['__cfduid'] = cfduid

        headers = {'User-Agent': user_agent}

        request_type = action_settings.get('type', 'post')
        if request_type == 'post':
            return requests.post(url, data=data, params=params, headers=headers, cookies=cookies)
        elif request_type == 'get':
            return requests.get(url, data=data, params=params, headers=headers, cookies=cookies)
        else:
            return None

        r.raise_for_status()

        return r

    def __make_list( self, source, params = {} ):
        video_list = []
        
        if source == 'movie':
            for movie in self.__movie:
                video_info = {'type': source,
                              'id':   movie['id']}

                item_info = {'label':  movie['title'],
                             'label2': movie['title_original'],
                             'info': { 'video': {'year':  int(movie['year']),
                                                 'genre': movie['genres'] } },
                             'art': { 'poster': movie['cover'] } }
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})
        elif source == 'tvseries':
            for tvseries in self.__tvseries:
                video_info = {'type':   source,
                              'id':     tvseries['id'],
                              'season': tvseries['season']}
                            
                item_info = {'label':  tvseries['title'],
                             'label2': tvseries['title_original'],
                             'art': { 'poster': tvseries['cover'] } }
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})
        elif source == 'episodes':
            for episode in self.__episodes:
                video_info = {'type':       source,
                              'id':         episode['id'],
                              'tvserie_id': self.__tvseries['id'],
                              'season':     params['season']}
                              
                label = '%s. %s %s %s %s' % (self.__tvseries['title'], self.__get_setting('season_title'), params['season'], self.__get_setting('episode_title'), episode['episode'])              

                item_info = {'label': label,
                             'info':  { 'video': {'season':  int(params['season']),
                                                  'episode': int(episode['episode']) } },
                             'fanart': self.__tvseries['thumb'],
                             'thumb':  self.__tvseries['thumb']}
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})
        elif source == 'seasons':
            for season in self.__tvseries['season_list']:
                video_info = {'type':       source,
                              'tvserie_id': self.__tvseries['id'],
                              'season':     season}
                              
                label = '%s %s. %s' % (self.__get_setting('season_title'), season, self.__tvseries['title'])              
                item_info = {'label':  label,
                             'fanart': self.__tvseries['thumb'],
                             'thumb':  self.__tvseries['thumb']}
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})

        return video_list

    def get_cfduid( self ):

        r = self.__http_request('main')
        cfduid = r.cookies.get('__cfduid', '')
        self.__set_setting('cfduid', cfduid)
        return cfduid
        
    def browse_movie( self, params ):

        u_params = {'page':     params.get('page', 1),
                    'category': params.get('category', 0),
                    'lang':     params.get('lang', 0),
                    'genre':    params.get('genre', 0),
                    'keyword':  params.get('keyword', '')}

        r = self.__http_request('browse_movie', u_params)
        j = r.json()
        
        if type(j) == list:
            return []
        
        self.__movie = j.get('movie', [])
        return self.__make_list('movie')

    def browse_tvseries( self, params ):

        u_params = {'page':    params.get('page', 1),
                    'keyword': params.get('keyword', '')}

        r = self.__http_request('browse_tvseries', u_params)
        j = r.json()
        
        if type(j) == list:
            return []
        
        self.__tvseries = j.get('tvseries', [])
        return self.__make_list('tvseries')

    def browse_episodes( self, params ):

        u_params = {'tvserie_id': params.get('tvserie_id', 0),
                    'season':     params.get('season', 0)}

        r = self.__http_request('browse_episodes', u_params)
        j = r.json()
        
        self.__episodes = j.get('episodes', [])
        self.__tvseries = j.get('tvseries')
        return self.__make_list('episodes', params )

    def browse_seasons( self, params ):

        u_params = {'tvserie_id': params.get('tvserie_id', 0),
                    'season':     params.get('season', 0)}

        r = self.__http_request('browse_episodes', u_params)
        j = r.json()
        
        self.__episodes = j.get('episodes', [])
        self.__tvseries = j.get('tvseries')
        if len(self.__tvseries['season_list']) > 1:
            return self.__make_list('seasons')
        else:
            return self.__make_list('episodes', params )

    def get_video_url( self, params ):
        video_source = self.__get_setting('video_source')
        
        type = params['type']
        if type == 'movie':
            u_params = {'id': params['id']}
            
            r = self.__http_request('get_info_movie', u_params)
            j = r.json()
            self.__movie = j['player']

            m3u8_path = self.__get_playlist_url(type, u_params)
            mp4_path = self.__movie['video']
            
            item_info = {'label':  self.__movie['title'],
                         'fanart': self.__movie['thumb'],
                         'thumb':  self.__movie['thumb']}

 
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
                    m3u8_path = self.__get_playlist_url(type, u_params)
                    mp4_path = episode['video']

                    label = '%s. %s %s %s %s' % (self.__tvseries['title'], self.__get_setting('season_title'), params['season'], self.__get_setting('episode_title'), episode['episode'])              
                    item_info = {'label':  label,
                                 'fanart': self.__tvseries['thumb'],
                                 'thumb':  self.__tvseries['thumb']}
        if video_source == 'm3u8' and m3u8_path != '':
            item_info['path'] = m3u8_path
        else:
            item_info['path'] = mp4_path
            
        return item_info
        
    def __get_playlist_url( self, type, params ):
        
        if type == 'movie':
            xml_url = 'http://video.az/jw/movie/xml/%s' % (params['id'])
        elif type == 'episodes':
            xml_url = 'http://video.az/jw/tvseries/xml/%s/%s/%s' % (params['tvserie_id'], params['season'], params['episode'])
        
        r = requests.get(xml_url)
        r.raise_for_status()

        file = ''

        root = ET.fromstring(r.text.encode('utf-8'))
        for sources in root.iter('{http://rss.jwpcdn.com/}source'):
            file = sources.attrib.get('file')
            if file[-4:] == 'm3u8': break

        return file
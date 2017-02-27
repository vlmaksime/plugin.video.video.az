# -*- coding: utf-8 -*-
# Module: default
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.apivideoaz as apivideoaz
from simpleplugin import Plugin
from urllib import urlencode

# Create plugin instance
plugin = Plugin()
_ = plugin.initialize_gettext()

def init_api():
    settings_list = ['cfduid']

    settings = {}
    for id in settings_list:
        settings[id] = plugin.get_setting(id)

#    settings['addon'] = _addon
#    settings['addon_id'] = _addon.getAddonInfo('id')

    return apivideoaz.videoaz(settings)

def get_categories():
    categories = [{'action': 'list_videos', 'label': _('Movies'),  'params': {'cat': 'movies'}},
                  {'action': 'list_videos', 'label': _('TV Series'), 'params': {'cat': 'tvseries'}},
                  {'action': 'search',      'label': _('Search')}]

    return categories

def get_setting(id):
    value = plugin.get_setting(id)

    if id == 'lang':
        if   value == 1: return ru
        elif value == '1': return 'view'
        elif value == '2': return 'last'
        elif value == '3': return 'rate'
        elif value == '4': return 'name'
        elif value == '5': return 'rand'
        else: return '0'
    else:
        return value

def check_cookies():
    cfduid = plugin.get_setting('cfduid')
    if len(cfduid) == 0:
        cfduid = _api.get_cfduid()
        plugin.set_setting('cfduid', cfduid)
        
def get_request_params( params ):
    result = {}
    for param in params:
        if param[0] == '_':
            result[param[1:]] = params[param]
    return result

def make_items(video_list):
    listing = []

    for video in video_list:
        item_info = video['item_info']

        video_info = video['video_info']
        video_type = video_info['type']
        if video_type == 'movie':
            is_playable = True
            url = plugin.get_url(action='play_video', _type = 'movie', _id = video_info['id'])
        if video_type == 'tvseries':
            is_playable = False
            url = plugin.get_url(action='list_videos', cat = 'seasons', _tvserie_id = video_info['id'], _season = video_info['season'])
        if video_type == 'seasons':
            is_playable = False
            url = plugin.get_url(action='list_videos', cat = 'episodes', _tvserie_id = video_info['tvserie_id'], _season = video_info['season'])
        if video_type == 'episodes':
            is_playable = True
            url = plugin.get_url(action='play_video', _type = 'episodes', _tvserie_id = video_info['tvserie_id'], _season = video_info['season'], _id = video_info['id'])

        item_info['url'] = url
        item_info['is_playable'] = is_playable


        listing.append(item_info)

    return listing
    
@plugin.action()
def root( params ):

    listing = []

    categories = get_categories()
    for category in categories:
        url = plugin.get_url(action=category['action'])
 
        params = category.get('params')
        if params != None:
            url = url + '&' + urlencode(params)

        listing.append({
            'label': category['label'],
            'url': url
        })

    return plugin.create_listing(listing, content='files')

@plugin.action()
def list_videos( params ):
    content='files'
    
    u_params = get_request_params(params)

    if params['cat'] == 'movies':
        video_list = _api.browse_movie(u_params)
        content='movies'
    elif params['cat'] == 'tvseries':
        video_list = _api.browse_tvseries(u_params)
        content='tvshows'
    elif params['cat'] == 'seasons':
        video_list = _api.browse_seasons(u_params)
        content='tvshows'
    elif params['cat'] == 'episodes':
        video_list = _api.browse_episodes(u_params)
        content='episodes'

    listing = make_items(video_list)
    
    if len(video_list) >= 20:
        params['_page'] = int(params.get('_page', 1)) + 1
        url = plugin.get_url(action='list_videos')
        del params['action']
        url = url + '&' + urlencode(params)
        listing.append({
            'label': 'Далее',
            'url': url})
         
    return plugin.create_listing(listing, content=content)


@plugin.action()
def search( params ):

    keyword = ''

    kbd = xbmc.Keyboard()
    kbd.setDefault('')
    kbd.setHeading('Search')
    kbd.doModal()
    if kbd.isConfirmed():
        keyword = kbd.getText().decode('utf-8')

    listing = []
    if keyword != '':
        u_params = {'keyword': keyword}
        movie_list = _api.browse_movie(u_params)
        listing.extend(make_items(movie_list))
        tvseries_list = _api.browse_tvseries(u_params)
        listing.extend(make_items(tvseries_list))

    return plugin.create_listing(listing, content='movies')
    
@plugin.action()
def play_video( params ):

    u_params = get_request_params( params )
    item = _api.get_video_url( u_params )

    return plugin.resolve_url(play_item=item)

if __name__ == '__main__':
    debug = plugin.get_setting('debug')
    if debug: plugin.log_error('%s' % (sys.argv[2]))

    _api = init_api()
    check_cookies()
    plugin.run()
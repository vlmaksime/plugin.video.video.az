# -*- coding: utf-8 -*-
# Module: default
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.apivideoaz as apivideoaz
import xbmcgui
from simpleplugin import Plugin
from urllib import urlencode
import xbmc

# Create plugin instance
plugin = Plugin()
_ = plugin.initialize_gettext()

def init_api():
    settings_list = ['cfduid', 'video_stream', 'video_quality', 'rating_source']

    settings = {}
    for id in settings_list:
        if id == 'rating_source':
            rating_source = plugin.movie_rating
            if rating_source == 0: settings[id] = 'imdb'
            elif rating_source == 1: settings[id] = 'kinopoisk'
        else:
            settings[id] = plugin.get_setting(id)

    settings['episode_title'] = _('Episode').decode('utf-8')
    settings['season_title']  = _('Season').decode('utf-8')

    return apivideoaz.videoaz(settings)

def show_api_error(err):
    text = ''
    if err.code == 1:
        text = _('Connection error')
    else:
        text = str(err)
    xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text, xbmcgui.NOTIFICATION_ERROR)

def show_notification(text):
    xbmcgui.Dialog().notification(plugin.addon.getAddonInfo('name'), text)

def check_cookies():
    if not plugin.cfduid:
        try:
            cfduid = _api.get_cfduid()
            plugin.set_setting('cfduid', cfduid)
        except apivideoaz.VideoAzApiError as err:
            show_api_error(err)

def get_request_params( params ):
    result = {}
    for param in params:
        if param[0] == '_':
            result[param[1:]] = params[param]
    return result

@plugin.action()
def root( params ):
    listing = list_root()
    return plugin.create_listing(listing, content='files')

def list_root():
    items = [{'action': 'list_videos',    'label': _('Videos'),    'params': {'cat': 'videos'}},
             {'action': 'list_videos',    'label': _('Movies'),    'params': {'cat': 'movies'}},
             {'action': 'list_videos',    'label': _('TV Series'), 'params': {'cat': 'tvseries'}},
             {'action': 'search_history', 'label': _('Search')}]

    for item in items:
        params = item.get('params',{})
        url = plugin.get_url(action=item['action'], **params)

        list_item = {'label':  item['label'],
                     'url':    url,
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item

@plugin.action()
def list_videos( params ):
    cur_cat  = params['cat']
    cur_page = int(params.get('_page', '1'))
    content  = get_category_content(cur_cat)

    update_listing = (params.get('update_listing')=='True')
    if update_listing:
        del params['update_listing']
    else:
        update_listing = (int(params.get('_page','1')) > 1)

    dir_params = {}
    dir_params.update(params)
    del dir_params['action']
    if cur_page > 1:
        del dir_params['_page']

    check_cookies()

    u_params = get_request_params(params)

    try:
        video_list = get_video_list(cur_cat, u_params)
        succeeded = True
    except apivideoaz.VideoAzApiError as err:
        show_api_error(err)
        succeeded = False

    if cur_cat in ['videos', 'movies', 'tvseries']:
        category = '%s %d' % (_('Page'), cur_page)
    else:
        category = video_list.get('title')

    if succeeded and cur_cat == 'seasons' and video_list['count'] == 1:
        listing = []
        dir_params['cat'] = 'episodes'
        url = plugin.get_url(action='list_videos', **dir_params)
        xbmc.executebuiltin('Container.Update("%s")' % url)
        return

    if succeeded:
        listing = make_video_list(video_list, params, dir_params)
    else:
        listing = []

    return plugin.create_listing(listing, content=content, succeeded=succeeded, update_listing=update_listing, category=category, sort_methods=[0])

def get_category_content( cat ):
    if cat == 'tvseries':
        content = 'tvshows'
    elif cat == 'seasons':
        content = 'tvshows'
    elif cat == 'videos':
        content = 'episodes'
    elif cat in ['movies', 'movie_related']:
        content = 'movies'
    else:
        content = 'files'
        
    return content

def get_video_list(cat, u_params):
    if cat == 'movies':
        video_list = _api.browse_movie(u_params)
    elif cat == 'tvseries':
        video_list = _api.browse_tvseries(u_params)
    elif cat == 'seasons':
        video_list = _api.browse_seasons(u_params)
    elif cat == 'episodes':
        video_list = _api.browse_episodes(u_params)
    elif cat == 'videos':
        video_list = _api.browse_video(u_params)
    elif cat == 'movie_related':
        video_list = _api.browse_movie_related(u_params)

    return video_list

def make_video_list( video_list, params={}, dir_params = {}, search=False ):
    cur_cat  = params.get('cat', '')
    keyword  = params.get('_keyword', '')
    cur_page = int(params.get('_page', '1'))

    use_pages    = not search and not keyword and (cur_cat in ['movies', 'tvseries', 'videos'])
    use_search   = not search and (cur_cat in ['movies', 'tvseries', 'videos'])
    use_category = not search and (cur_cat in ['movies', 'videos'])
    use_genre    = not search and (cur_cat in ['movies'])
    use_lang     = not search and (cur_cat in ['movies'])

    if use_search:

        url = plugin.get_url(action='search_category', **dir_params)
        label = make_category_label('yellowgreen', _('Search'), keyword)
        list_item = {'label': label,
                     'is_folder':   False,
                     'is_playable': False,
                     'url':    url,
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item

    if use_category:

        list = get_category(cur_cat)

        cur_category = params.get('_category','0')

        url = plugin.get_url(action='select_category', **dir_params)
        label = make_category_label('blue', _('Categories'), get_category_name(list, cur_category))
        list_item = {'label': label,
                     'is_folder':   False,
                     'is_playable': False,
                     'url':    url,
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item

    if use_genre:

        list = get_genre(cur_cat)

        cur_genre = params.get('_genre','0')

        url = plugin.get_url(action='select_genre', **dir_params)
        label = make_category_label('blue', _('Genres'), get_category_name(list, cur_genre))
        list_item = {'label': label,
                     'is_folder':   False,
                     'is_playable': False,
                     'url':    url,
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item

    if use_lang:

        list = get_lang()

        cur_lang = params.get('_lang')

        url = plugin.get_url(action='select_lang', **dir_params)
        label = make_category_label('blue', _('Language'), get_lang_name(list, cur_lang))
        list_item = {'label': label,
                     'is_folder':   False,
                     'is_playable': False,
                     'url':    url,
                     'icon':   plugin.icon,
                     'fanart': plugin.fanart}
        yield list_item

    count = video_list['count']
    for video_item in video_list['list']:
        yield make_item(video_item, search)

    if use_pages:
        if cur_page > 1:
            if cur_page == 2:
                del params['_page']
            else:
                params['_page'] = cur_page - 1
            url = plugin.get_url(**params)
            item_info = {'label': _('Previous page...'),
                         'url':   url}
            yield item_info

        if count >= 20:
            params['_page'] = cur_page + 1
            url = plugin.get_url(**params)
            item_info = {'label': _('Next page...'),
                         'url':   url}
            yield item_info

def make_item( video_item, search ):
        item_info = video_item['item_info']

        video_info = video_item['video_info']
        video_type = video_info['type']

        use_atl_names = plugin.use_atl_names
        movie_details = plugin.movie_details

        if video_type == 'movie':
            is_playable = True
            url = plugin.get_url(action='play', _type = 'movie', _id = video_info['id'])

            label_list = []
            if search:
                label_list.append('[%s] ' % _('Movies').decode('utf-8'))
                
            if use_atl_names:
                label_list.append(item_info['info']['video']['originaltitle'])
            else:
                label_list.append(item_info['info']['video']['title'])

            # if item_info['info']['video']['year'] > 0:
                # label_list.append(' (%d)' % item_info['info']['video']['year'])

            if movie_details:
                details = get_movie_details(video_info['id'])

                quality_info = []
                if details.get('video_quality'):
                    quality_info.append('[B]%s:[/B] %s' % (_('Video quality').decode('utf-8'), details['video_quality']) )
                    del details['video_quality']

                if details.get('audio_quality'):
                    if len(quality_info): quality_info.append('\n')
                    quality_info.append('[B]%s:[/B] %s' % (_('Audio quality').decode('utf-8'), details['audio_quality']) )
                    del details['audio_quality']

                if details['plot'] and len(quality_info):
                    quality_info.append('\n\n')

                details['plot'] = ''.join(quality_info) + details['plot']
                
                item_info['info']['video'].update(details)
                
                
            item_info['label'] = ''.join(label_list)

            del item_info['info']['video']['title']

            related_url = plugin.get_url(action='list_videos', cat = 'movie_related', _id = video_info['id'])
            item_info['context_menu'] = [(_('Related'), 'Container.Update(%s)' % related_url)]

            
        elif video_type == 'tvseries':
            is_playable = False
            url = plugin.get_url(action='list_videos', cat = 'seasons', _tvserie_id = video_info['id'], _season = video_info['season'])

            if search:
                label_list = []
                label_list.append('[%s] ' % _('TV Series').decode('utf-8'))
                label_list.append(item_info['info']['video']['title'])
                item_info['label'] = ''.join(label_list)

                del item_info['info']['video']['title']

        elif video_type == 'seasons':
            is_playable = False
            url = plugin.get_url(action='list_videos', cat = 'episodes', _tvserie_id = video_info['tvserie_id'], _season = video_info['season'])

        elif video_type == 'episodes':
            is_playable = True
            url = plugin.get_url(action='play', _type = 'episodes', _tvserie_id = video_info['tvserie_id'], _season = video_info['season'], _id = video_info['id'])

            if use_atl_names:
                label_list = []
                label_list.append(item_info['info']['video']['tvshowtitle'])
                label_list.append('.s%02de%02d' % (item_info['info']['video']['season'], item_info['info']['video']['episode']))
                item_info['label'] = ''.join(label_list)

                del item_info['info']['video']['title']

        elif video_type == 'video':
            is_playable = True
            item_info['fanart'] = plugin.fanart
            url = plugin.get_url(action='play', _type = 'video', _id = video_info['id'])

            if search:
                label_list = []
                label_list.append('[%s] ' % _('Videos').decode('utf-8'))
                label_list.append(item_info['label'])
                item_info['label'] = ''.join(label_list)
            
        item_info['url'] = url
        item_info['is_playable'] = is_playable

        return item_info

def make_category_label( color, title, category ):
    label_parts = []
    label_parts.append('[COLOR=%s][B]' % color)
    label_parts.append(title)
    label_parts.append(':[/B] ')
    label_parts.append(category)
    label_parts.append('[/COLOR]')
    return ''.join(label_parts)

@plugin.cached(180)
def get_movie_details( id ):
    return _api.get_movie_details(id)

@plugin.cached(180)
def get_category( cat ):
    if cat == 'movies':
        list = _api.category_movie()
    elif cat == 'videos':
        list = _api.category_video()
    return list

@plugin.cached(180)
def get_genre( cat ):
    if cat == 'movies':
        list = _api.category_genre()
    return list

@plugin.cached(180)
def get_lang():
    list = []
    list.append({'id': 'az', 'title': _('Azərbaycanca')})
    list.append({'id': 'ru', 'title': _('Русский')})
    list.append({'id': 'en', 'title': _('English')})
    list.append({'id': 'tr', 'title': _('Türkçe')})

    return list

def get_category_name( list, id ):
    for item in list:
        if item['id'] == id:
            return item['title'].encode('utf-8')
    return _('All')

def get_lang_name( list, id ):
    for item in list:
        if item['id'] == id:
            return item['title']
    return _('All')

@plugin.action()
def search( params ):

    check_cookies()

    keyword  = params.get('keyword', '')
    usearch  = (params.get('usearch') == 'True')

    new_search = (keyword == '')
    succeeded = False

    if not keyword:
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(_('Search'))
        kbd.doModal()
        if kbd.isConfirmed():
            keyword = kbd.getText()

    if keyword and new_search and not usearch:
        with plugin.get_storage('__history__.pcl') as storage:
            history = storage.get('history', [])
            history.insert(0, {'keyword': keyword.decode('utf-8')})
            if len(history) > plugin.history_length:
                history.pop(-1)
            storage['history'] = history

        params['keyword'] = keyword
        url = plugin.get_url(**params)
        xbmc.executebuiltin('Container.Update("%s")' % url)
        return

    if keyword:
        succeeded = True
        category_list = []
        u_params = {'keyword': keyword}

        us_movies = usearch and plugin.us_movies
        search_movies = not usearch and plugin.search_movies
        if us_movies or search_movies:
            category_list.append('movies')

        us_tvseries = usearch and plugin.us_tvseries
        search_tvseries = not usearch and plugin.search_tvseries
        if us_tvseries or search_tvseries:
            category_list.append('tvseries')

        us_videos = usearch and plugin.us_videos
        search_videos = not usearch and plugin.search_videos
        if us_videos or search_videos:
            category_list.append('videos')

        video_items = []
        for cat in category_list:
            try:
                video_list = get_video_list(cat, u_params)
            except apivideoaz.VideoAzApiError as err:
                show_api_error(err)
                succeeded = False

            if succeeded and video_list['count']:
                for video_item in video_list['list']:
                    video_items.append(video_item)

        if succeeded and len(video_items) == 0:
            succeeded = False
            if not usearch:
                show_notification(_('Nothing found!'))

    if succeeded:
        search_list = {'count': len(video_items),
                       'list': video_items}
        listing = make_video_list(search_list, search=True)
    else:
        listing = []

    return plugin.create_listing(listing, succeeded = succeeded, content='movies', category=keyword, sort_methods=[27])

@plugin.action()
def search_category( params ):

    category = params.get('cat')
    keyword = params.get('_keyword', '')

    kbd = xbmc.Keyboard()
    kbd.setDefault(keyword)
    kbd.setHeading(_('Search'))
    kbd.doModal()
    if kbd.isConfirmed():
        keyword = kbd.getText()

    params['_keyword'] = keyword
    del params['action']
    url = plugin.get_url(action='list_videos', update_listing=True, **params)
    xbmc.executebuiltin('Container.Update("%s")' % url)

@plugin.action()
def search_history():

    with plugin.get_storage('__history__.pcl') as storage:
        history = storage.get('history', [])

        if len(history) > plugin.history_length:
            history[plugin.history_length - len(history):] = []
            storage['history'] = history

    listing = []
    listing.append({'label': _('New Search...'),
                    'url': plugin.get_url(action='search')})

    for item in history:
        listing.append({'label': item['keyword'],
                        'url': plugin.get_url(action='search', keyword=item['keyword'].encode('utf-8'))})

    return plugin.create_listing(listing, content='movies')

@plugin.action()
def play( params ):

    check_cookies()

    u_params = get_request_params( params )
    try:
        item = _api.get_video_url( u_params )
        succeeded = True
    except apivideoaz.VideoAzApiError as err:
        show_api_error(err)
        item = None
        succeeded = False

    return plugin.resolve_url(play_item=item, succeeded=succeeded)

@plugin.action()
def select_category( params ):
    list = get_category( params['cat'])
    list.insert(0, {'id': '0', 'title': _('All')})
    titles = []
    for list_item in list:
        titles.append(list_item['title'])
    ret = xbmcgui.Dialog().select(_('Categories'), titles)
    if ret >= 0:
        category = list[ret]['id']
        if category == '0' and params.get('_category'):
            del params['_category']
        else:
            params['_category'] = category
        del params['action']
        url = plugin.get_url(action='list_videos', update_listing=True, **params)
        xbmc.executebuiltin('Container.Update("%s")' % url)

@plugin.action()
def select_genre( params ):
    list = get_genre( params['cat'])
    list.insert(0, {'id': '0', 'title': _('All')})
    titles = []
    for list_item in list:
        titles.append(list_item['title'])
    ret = xbmcgui.Dialog().select(_('Genres'), titles)
    if ret >= 0:
        genre = list[ret]['id']
        if genre == '0' and params.get('_genre'):
            del params['_genre']
        else:
            params['_genre'] = genre
        del params['action']
        url = plugin.get_url(action='list_videos', update_listing=True, **params)
        xbmc.executebuiltin('Container.Update("%s")' % url)

@plugin.action()
def select_lang( params ):
    list = get_lang()
    list.insert(0, {'id': '0', 'title': _('All')})
    titles = []
    for list_item in list:
        titles.append(list_item['title'])
    ret = xbmcgui.Dialog().select(_('Language'), titles)
    if ret >= 0:
        lang = list[ret]['id']
        if lang == '0' and params.get('_lang'):
            del params['_lang']
        else:
            params['_lang'] = lang
        del params['action']
        url = plugin.get_url(action='list_videos', update_listing=True, **params)
        xbmc.executebuiltin('Container.Update("%s")' % url)

if __name__ == '__main__':
    _api = init_api()
    plugin.run()
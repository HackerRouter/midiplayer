PLUGIN_METADATA = {
    'id': 'midiplayer',
    'version': '1.0.0',
    'name': 'My Hello World Plugin'
}
import math
import random
import time
import re
import os
import json
from mcdreforged.api.all import *
from mcdreforged.api.types import *
from mcdreforged.api.command import *
from mcdreforged.api.rtext import *
from mcdreforged.api.command import SimpleCommandBuilder, Integer, Text, GreedyText
 
        
def on_load(server: PluginServerInterface, prev_module):
    global songs_json_file
    songs_json_file = create_midiplayer_folder()
    global player_pages, items_per_page, player_current_song, player_pages_playlist
    player_pages = {}  # 存储每个玩家的当前页 # 存储每个玩家的播放列表
    player_current_song = {} 
    player_pages_playlist = {}
    items_per_page=8


    builder = SimpleCommandBuilder()

    builder.command('!!mp list', list_all_songs)
    builder.command('!!mp list link', list_all_links)
    builder.command('!!mp add <song_name> <song_artists> <song_link>', add_song_to_json)
    builder.command('!!mp search <keyword>', search_songs)
    builder.command('!!mp page to <page>', page_to)
    builder.command('!!mp page prev', page_prev)
    builder.command('!!mp page next', page_next)
    builder.command('!!mp playlist to <page>', page_to_playlist)
    builder.command('!!mp playlist prev', page_prev_playlist)
    builder.command('!!mp playlist next', page_next_playlist)
    builder.command('!!mp edit <index> delete', edit_song_delete)
    builder.command('!!mp edit <index> copy', edit_song_copy)
    builder.command('!!mp delete <index>', edit_song_delete)
    builder.command('!!mp copy <index>', edit_song_copy)
    builder.command('!!mp edit <index> artist <song_artists>', edit_song_artist)
    builder.command('!!mp edit <index> name <song_name>', edit_song_name)
    builder.command('!!mp edit <index> link <song_link>', edit_song_link)
    builder.command('!!mp play <keyword>', play_song)
    builder.command('!!mp play add <keyword>', add_to_playlist)
    builder.command('!!mp stop', pause_song)
    builder.command('!!mp play stop', pause_song)
    builder.command('!!mp play cont', unpause_song)
    builder.command('!!mp play next', next_song)
    builder.command('!!mp play', next_song)
    builder.command('!!mp play prev', previous_song)
    builder.command('!!mp play random', random_playlist)
    '''builder.command('!!mp play list', show_playlist)
    builder.command('!!mp playlist', show_playlist)'''
    builder.command('!!mp play list', list_playlist)
    builder.command('!!mp playlist', list_playlist)
    builder.command('!!mp playlist search <keyword>', playlists_search_songs)
    builder.command('!!mp play del all', del_playlist_all)
    builder.command('!!mp del all', del_playlist_all)

    builder.arg('song_name', Text)
    builder.arg('song_artists', Text)
    builder.arg('song_link', Text)
    builder.arg('keyword', Text)
    builder.arg('page', Integer)
    builder.arg('index', Integer)

    builder.register(server)



def load_player_playlists(player):
    player_file = f"{player}.json"
    
    if os.path.exists(player_file):
        with open(player_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return []

def save_player_playlists(player, playlists):
    player_file = f"{player}.json"
    
    with open(player_file, 'w', encoding='utf-8') as f:
        json.dump(playlists, f, ensure_ascii=False, indent=4)

def update_player_playlists(player, song_link):
    playlists = load_player_playlists(player)
    if song_link not in playlists:
        playlists.append(song_link)
    
    save_player_playlists(player, playlists)



def del_playlist(source: 'PlayerCommandSource',args):
    player = source.get_info().player
    global player_pages, items_per_page, player_current_song
    _, _, _, _, songs_data = get_current_page(player)
    player_file = f"{player}.json"
    user_input = args['keyword']
    playlists = load_player_playlists(player)
    # 尝试将用户输入作为索引
    if user_input.isdigit():
        index = int(user_input) - 1
        if 0 <= index < len(songs_data):
            song = songs_data[index]
            if song['link'] not in playlists:
                playlists.pop(song['link'])
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》移出播放列表。","color":"dark_aqua"}]')
            else:
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"该歌曲已经在播放列表中。","color":"red"}]')
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        if ',' in user_input:

            indexes = [int(num.strip()) - 1 for num in user_input.split(',')]
            for index in indexes:
                if 0 <= index < len(songs_data):
                    song = songs_data[index]
                    if song['link'] not in playlists:
                        playlists.append(song['link'])
                        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》加入播放列表。","color":"dark_aqua"}]')
                else:
                    source.get_server().execute(f'tellraw {player}' + ' [{"text":"有一无效的歌曲索引！","color":"red"}]')
        elif '-' in user_input:

            parts = user_input.split(',')
            indexes = []
            for part in parts:
                if '-' in part:
                    start, end = user_input.split('-')
                    if start.isdigit() and end.isdigit():
                        indexes = list(range(int(start), int(end) + 1))
                    else:
                        source.get_server().execute(f'tellraw {player}' + ' [{"text":"输入的范围不正确！","color":"red"}]')
            for index in indexes:
                if 0 <= index - 1 < len(songs_data):
                    song = songs_data[index - 1]
                    if song['link'] not in playlists:
                        playlists.append(song['link'])
                        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》加入播放列表。","color":"dark_aqua"}]')
                else: 
                    source.get_server().execute(f'tellraw {player}' + ' [{"text":"有一无效的歌曲索引！","color":"red"}]')
        else:
            matching_songs = [
            (idx, song) for idx, song in enumerate(songs_data)
            if user_input.lower() in song['name'].lower() or any(user_input.lower() in artist.lower() for artist in song['artist'])
        ]

            if len(matching_songs) == 1:
                song = matching_songs[0][1]
                update_player_playlists(player, song['link'])
                source.get_server().execute(f'tellraw {player} "找到歌曲：{song['name']} - {", ".join(song['artist'])}"')
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》加入播放列表。","color":"dark_aqua"}]')
            elif matching_songs:
                source.get_server().execute(f'tellraw {player} "找到 {len(matching_songs)} 首匹配的歌曲:"')
                for idx, song in matching_songs:
                    artists = ", ".join(song['artist'])
                    source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')

            else:
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"没有找到匹配的歌曲。","color":"red"}]')

    save_player_playlists(player, playlists)
    






def del_playlist_all(source: 'PlayerCommandSource'):
    player = source.get_info().player
    global player_pages, items_per_page, player_current_song
    '''player_playlists[player] = []'''
    player_file = f"{player}.json"
    

    with open(player_file, 'w', encoding='utf-8') as f:
        pass 


    current_song = player_current_song.get(player)
    source.get_server().execute(f'execute as {player} run function {current_song}:stop')
    source.get_server().execute(f'tellraw {player}' + ' [{"text":"已清空当前播放列表。","color":"red"}]')

def show_playlist(source: 'PlayerCommandSource'):
    player = source.get_info().player
    global player_pages, items_per_page, player_current_song
    _, _, _, _, songs_data = get_current_page(player)
    '''if player not in player_playlists or not player_playlists[player]:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return

    playlist = player_playlists[player]'''
    playlist = load_player_playlists(player)
    player_file = f"{player}.json"
    if not os.path.exists(player_file):
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return
    current_song_link = player_current_song.get(player)

    source.get_server().execute(f'tellraw {player} "当前播放列表:"')
    for link in playlist:
        song = next((s for s in songs_data if s['link'] == link), None)
        if song:
            if link == current_song_link:
                source.get_server().execute(f'tellraw {player} "> {song["name"]} - {", ".join(song["artist"])} <"')
            else:
                source.get_server().execute(f'tellraw {player} "{song["name"]} - {", ".join(song["artist"])}"')


def pause_song(source: 'PlayerCommandSource'):
    player = source.get_info().player
    '''if player not in player_playlists or not player_playlists[player]:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return'''
    player_file = f"{player}.json"
    if not os.path.exists(player_file):
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return

    current_song = player_current_song.get(player)
    source.get_server().execute(f'execute as {player} run function {current_song}:pause')
    source.get_server().execute(f'tellraw {player}' + ' [{"text":"已暂停。","color":"dark_aqua"}]')#/tellraw @s [{"text":"已暂停。","color":"dark_aqua","bold":false,"italic":false,"underlined":false,"strikethrough":false,"obfuscated":false}]

def unpause_song(source: 'PlayerCommandSource'):
    player = source.get_info().player
    '''if player not in player_playlists or not player_playlists[player]:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return'''
    player_file = f"{player}.json"
    if not os.path.exists(player_file):
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return

    current_song = player_current_song.get(player)
    source.get_server().execute(f'execute as {player} run function {current_song}:play')
    source.get_server().execute(f'tellraw {player}' + ' [{"text":"已继续播放。","color":"dark_aqua"}]')



def previous_song(source: 'PlayerCommandSource'):
    global player_pages, items_per_page, player_current_song
    player = source.get_info().player
    _, _, _, _, songs_data = get_current_page(player)
    '''if player not in player_playlists or not player_playlists[player]:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return'''
    playlist = load_player_playlists(player)
    player_file = f"{player}.json"
    if not os.path.exists(player_file):
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return

    '''playlist = player_playlists[player]'''

    if len(playlist) == 1:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表只有一首歌，无法切换到上一首。","color":"red"}]') #/tellraw @s [{"text":"播放列表为空或无歌曲。","color":"red","bold":false,"italic":false,"underlined":false,"strikethrough":false,"obfuscated":false}]
        return

    current_song_link = player_current_song.get(player)
    if current_song_link:
        source.get_server().execute(f'execute as {player} run function {current_song_link}:stop')
        current_index = playlist.index(current_song_link)
        previous_index = (current_index - 1) % len(playlist)  
    else:
        previous_index = 0

    song_link = playlist[previous_index]
    player_current_song[player] = song_link
    source.get_server().execute(f'execute as {player} run function {song_link}:play')

    previous_song_link = playlist[(previous_index - 1) % len(playlist)]
    next_song_link = playlist[(previous_index + 1) % len(playlist)]
    
    previous_song = next((song for song in songs_data if song['link'] == previous_song_link), None)
    current_song = next((song for song in songs_data if song['link'] == song_link), None)
    next_song = next((song for song in songs_data if song['link'] == next_song_link), None)

    source.get_server().execute(f'tellraw {player}' + ' [{"text":"即将播放上一首歌曲……","color":"dark_aqua"}]')
    if previous_song:
        source.get_server().execute(f'tellraw {player} "上一首: {previous_song["name"]} - {", ".join(previous_song["artist"])}"')
    if current_song:
        source.get_server().execute(f'tellraw {player} "当前: > {current_song["name"]} - {", ".join(current_song["artist"])} <"')
    if next_song:
        source.get_server().execute(f'tellraw {player} "下一首: {next_song["name"]} - {", ".join(next_song["artist"])}"')

def next_song(source: 'PlayerCommandSource'):
    global player_pages, items_per_page, player_current_song
    player = source.get_info().player
    _, _, _, _, songs_data = get_current_page(player)
    '''if player not in player_playlists or not player_playlists[player]:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return'''

    playlist = load_player_playlists(player)
    player_file = f"{player}.json"
    if not os.path.exists(player_file):
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
        return


    if len(playlist) == 1:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表只有一首歌，无法切换到下一首。","color":"red"}]')
        return

    current_song_link = player_current_song.get(player)

    if current_song_link:
        source.get_server().execute(f'execute as {player} run function {current_song_link}:stop')
        current_index = playlist.index(current_song_link)
        next_index = (current_index + 1) % len(playlist)  # 循环播放
    else:
        next_index = 0

    # 更新并播放下一首歌a
    song_link = playlist[next_index]
    player_current_song[player] = song_link
    source.get_server().execute(f'execute as {player} run function {song_link}:play')


    previous_song_link = playlist[(next_index - 1) % len(playlist)]
    next_next_song_link = playlist[(next_index + 1) % len(playlist)]

    previous_song = next((song for song in songs_data if song['link'] == previous_song_link), None)
    current_song = next((song for song in songs_data if song['link'] == song_link), None)
    next_song = next((song for song in songs_data if song['link'] == next_next_song_link), None)

    source.get_server().execute(f'tellraw {player}' + ' [{"text":"即将播放下一首歌曲……","color":"dark_aqua"}]')
    if previous_song:
        source.get_server().execute(f'tellraw {player} "上一首: {previous_song["name"]} - {", ".join(previous_song["artist"])}"')
    if current_song:
        source.get_server().execute(f'tellraw {player} "当前: > {current_song["name"]} - {", ".join(current_song["artist"])} <"')
    if next_song:
        source.get_server().execute(f'tellraw {player} "下一首: {next_song["name"]} - {", ".join(next_song["artist"])}"')


def add_to_playlist(source: 'PlayerCommandSource',args):
    player = source.get_info().player
    _, _, _, _, songs_data = get_current_page(player)

    user_input = args['keyword']
    playlists = load_player_playlists(player)

    if user_input.isdigit():
        index = int(user_input) - 1
        if 0 <= index < len(songs_data):
            song = songs_data[index]
            if song['link'] not in playlists:
                playlists.append(song['link'])
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》加入播放列表。","color":"dark_aqua"}]')
            else:
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"该歌曲已经在播放列表中。","color":"red"}]')
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        if ',' in user_input:

            indexes = [int(num.strip()) - 1 for num in user_input.split(',')]
            for index in indexes:
                if 0 <= index < len(songs_data):
                    song = songs_data[index]
                    if song['link'] not in playlists:
                        playlists.append(song['link'])
                        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》加入播放列表。","color":"dark_aqua"}]')
                else:
                    source.get_server().execute(f'tellraw {player}' + ' [{"text":"有一无效的歌曲索引！","color":"red"}]')
        elif '-' in user_input:

            parts = user_input.split(',')
            indexes = []
            for part in parts:
                if '-' in part:
                    start, end = user_input.split('-')
                    if start.isdigit() and end.isdigit():
                        indexes = list(range(int(start), int(end) + 1))
                    else:
                        source.get_server().execute(f'tellraw {player}' + ' [{"text":"输入的范围不正确！","color":"red"}]')
            for index in indexes:
                if 0 <= index - 1 < len(songs_data):
                    song = songs_data[index - 1]
                    if song['link'] not in playlists:
                        playlists.append(song['link'])
                        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》加入播放列表。","color":"dark_aqua"}]')
                else: 
                    source.get_server().execute(f'tellraw {player}' + ' [{"text":"有一无效的歌曲索引！","color":"red"}]')
        else:
            matching_songs = [
            (idx, song) for idx, song in enumerate(songs_data)
            if user_input.lower() in song['name'].lower() or any(user_input.lower() in artist.lower() for artist in song['artist'])
        ]

            if len(matching_songs) == 1:
                song = matching_songs[0][1]
                update_player_playlists(player, song['link'])
                source.get_server().execute(f'tellraw {player} "找到歌曲：{song['name']} - {", ".join(song['artist'])}"')
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"已将《'+ song['name']+ '》加入播放列表。","color":"dark_aqua"}]')
            elif matching_songs:
                source.get_server().execute(f'tellraw {player} "找到 {len(matching_songs)} 首匹配的歌曲:"')
                for idx, song in matching_songs:
                    artists = ", ".join(song['artist'])
                    source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')

            else:
                source.get_server().execute(f'tellraw {player}' + ' [{"text":"没有找到匹配的歌曲。","color":"red"}]')

    save_player_playlists(player, playlists)


def random_playlist(source: 'PlayerCommandSource'):
    '''global player_playlists'''
    player = source.get_info().player
    '''if player not in player_playlists or not player_playlists[player]:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')'''
    player_file = f"{player}.json"
    

    if os.path.exists(player_file):
        player_playlists = load_player_playlists(player)
        random.shuffle(player_playlists)
        save_player_playlists(player, player_playlists)
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表已打乱。","color":"dark_aqua"}]')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表为空或无歌曲。","color":"red"}]')
    
    '''random.shuffle(player_playlists[player])
    source.get_server().execute(f'tellraw {player}' + ' [{"text":"播放列表已打乱。","color":"dark_aqua"}]')'''


def play_song(source: 'PlayerCommandSource',args):
    '''global player_playlists'''
    player = source.get_info().player
    playlists = load_player_playlists(player)
    _, _, _, _, songs_data = get_current_page(player)
    user_input = args['keyword']

    if user_input.isdigit():
        index = int(user_input) - 1
        if 0 <= index < len(songs_data):
            song = songs_data[index]

            '''if player not in player_playlists:
                player_playlists[player] = []
            if song['link'] not in player_playlists[player]:
                player_playlists[player].append(song['link'])'''
            if song['link'] not in playlists:
                        playlists.append(song['link'])

            if player in player_current_song:
                source.get_server().execute(f'execute as {player} run function {player_current_song[player]}:stop')  # 停止当前播放的歌曲 source.get_server().execute(f'execute as {player} run function {song['link']}:play')
            source.get_server().execute(f'tellraw {player} "找到歌曲：{song['name']} - {", ".join(song['artist'])}"')
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"即将播放……","color":"dark_aqua"}]')
            source.get_server().execute(f'execute as {player} run function {song['link']}:play')
            player_current_song[player] = song['link']  # 记录当前播放的歌曲
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        matching_songs = [
            (idx, song) for idx, song in enumerate(songs_data)
            if user_input.lower() in song['name'].lower() or any(user_input.lower() in artist.lower() for artist in song['artist'])
        ]

        if len(matching_songs) == 1:
            song = matching_songs[0][1]

            '''if player not in player_playlists:
                player_playlists[player] = []
            if song['link'] not in player_playlists[player]:
                player_playlists[player].append(song['link'])'''
            if song['link'] not in playlists:
                        playlists.append(song['link'])

            if player in player_current_song:
                source.get_server().execute(f'execute as {player} run function {player_current_song[player]}:stop')  # 停止当前播放的歌曲
            source.get_server().execute(f'tellraw {player} "找到歌曲：{song['name']} - {", ".join(song['artist'])}"')
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"即将播放……","color":"dark_aqua"}]')
            source.get_server().execute(f'execute as {player} run function {song['link']}:play')
            player_current_song[player] = song['link']  # 记录当前播放的歌曲
        elif matching_songs:
            source.get_server().execute(f'tellraw {player} "找到 {len(matching_songs)} 首匹配的歌曲:"')
            for idx, song in matching_songs:
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')

        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"没有找到匹配的歌曲。","color":"red"}]')

    save_player_playlists(player, playlists)


def edit_song_delete(source: 'PlayerCommandSource',args):
    player = source.get_info().player
    song_index = args['index'] - 1
    _, _, _, _, songs_data = get_current_page(player)
    if song_index < 1 or song_index > len(songs_data):
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        with open(songs_json_file, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)

        songs_data.pop(song_index)
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"歌曲已删除。","color":"dark_aqua"}]')

        with open(songs_json_file, 'w', encoding='utf-8') as f:
            json.dump(songs_data, f, indent=4)

def edit_song_copy(source: 'PlayerCommandSource',args):
    player = source.get_info().player
    song_index = args['index'] - 1
    _, _, _, _, songs_data = get_current_page(player)
    if song_index < 1 or song_index > len(songs_data):
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        with open(songs_json_file, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)

        song = songs_data[song_index]
        new_song = song.copy()
        songs_data.append(new_song)
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"歌曲已复制。","color":"dark_aqua"}]')

        with open(songs_json_file, 'w', encoding='utf-8') as f:
            json.dump(songs_data, f, indent=4)

def edit_song_artist(source: 'PlayerCommandSource',args):
    player = source.get_info().player
    song_artists = args['song_artists'].replace("_", " ")
    song_index = args['index'] - 1
    if song_index < 1 or song_index > items_per_page:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        with open(songs_json_file, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)

        song = songs_data[song_index]
        song['artist'] = [artist.strip() for artist in song_artists.split(',')]
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"歌曲作者已编辑。","color":"dark_aqua"}]')

        with open(songs_json_file, 'w', encoding='utf-8') as f:
            json.dump(songs_data, f, indent=4)


def edit_song_name(source: 'PlayerCommandSource',args):
    player = source.get_info().player
    song_name = args['song_name'].replace("_", " ")
    song_index = args['index'] - 1
    if song_index < 1 or song_index > items_per_page:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        with open(songs_json_file, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)

        song = songs_data[song_index]
        song['name'] = song_name
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"歌曲歌名已编辑。","color":"dark_aqua"}]')

        with open(songs_json_file, 'w', encoding='utf-8') as f:
            json.dump(songs_data, f, indent=4)

def edit_song_link(source: 'PlayerCommandSource',args):
    player = source.get_info().player
    song_link = args['song_link']
    song_index = args['index'] - 1
    if song_index < 1 or song_index > items_per_page:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的歌曲索引！","color":"red"}]')
    else:
        with open(songs_json_file, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)

        song = songs_data[song_index]
        song['link'] = song_link
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"歌曲链接已编辑。","color":"dark_aqua"}]')

        with open(songs_json_file, 'w', encoding='utf-8') as f:
            json.dump(songs_data, f, indent=4)

def page_prev(source: 'PlayerCommandSource'):
    player = source.get_info().player
    global player_pages
    if player not in player_pages:
        player_pages[player] = 1
    current_page, start_idx, end_idx, total_pages, songs_data = get_current_page(player)
    if player_pages.get(player, 1) > 1:
        player_pages[player] -= 1
        current_page, start_idx, end_idx, total_pages, songs_data = get_current_page(player)
        if songs_data:
            source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
            source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')
            for idx in range(start_idx, end_idx):
                song = songs_data[idx]
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')

    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已经是第一页。","color":"red"}]')


def page_next(source: 'PlayerCommandSource'):
    player = source.get_info().player
    global player_pages
    if player not in player_pages:
        player_pages[player] = 1
    current_page, start_idx, end_idx, total_pages, songs_data = get_current_page(player)
    if player_pages.get(player, 1) < total_pages:
        player_pages[player] += 1
        current_page, start_idx, end_idx, total_pages, songs_data = get_current_page(player)
        source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
        source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')
        if songs_data:
            for idx in range(start_idx, end_idx):
                song = songs_data[idx]
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已经是最后一页。","color":"red"}]')


def page_to(source: 'PlayerCommandSource', args):
    player = source.get_info().player
    target_page = int(args['page'])
    current_page, start_idx, end_idx, total_pages, songs_data = get_current_page(player)
    global player_pages
    if player not in player_pages:
        player_pages[player] = 1
    if 1 <= target_page <= total_pages:
        player_pages[player] = target_page
        current_page, start_idx, end_idx, total_pages, songs_data = get_current_page(player)
        source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
        source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')
        if songs_data:
            for idx in range(start_idx, end_idx):
                song = songs_data[idx]
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的页码，请重新输入。","color":"red"}]')

#################################
        ########################################
        #####################################
        ###################
def page_to_playlist(source: 'PlayerCommandSource', args):
    player = source.get_info().player
    target_page = int(args['page'])
    current_page, start_idx, end_idx, total_pages, total_songs, songs_data = get_current_page_playlist(player)
    global player_pages_playlist
    if player not in player_pages_playlist:
        player_pages_playlist[player] = 1
    if 1 <= target_page <= total_pages:
        player_pages_playlist[player] = target_page
        current_page, start_idx, end_idx, total_pages, total_songs, songs_data = get_current_page_playlist(player)
        source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
        source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')
        if songs_data:
            for idx in range(start_idx, end_idx):
                song = songs_data[idx]
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"无效的页码，请重新输入。","color":"red"}]')

def page_prev_playlist(source: 'PlayerCommandSource'):
    player = source.get_info().player
    global player_pages_playlist
    if player not in player_pages_playlist:
        player_pages_playlist[player] = 1
    current_page, start_idx, end_idx, total_pages, total_songs, songs_data = get_current_page_playlist(player)
    if player_pages_playlist.get(player, 1) > 1:
        player_pages_playlist[player] -= 1
        current_page, start_idx, end_idx, total_pages, total_songs, songs_data = get_current_page_playlist(player)
        if songs_data:
            source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
            source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')
            for idx in range(start_idx, end_idx):
                song = songs_data[idx]
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')

    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已经是第一页。","color":"red"}]')


def page_next_playlist(source: 'PlayerCommandSource'):
    player = source.get_info().player
    global player_pages_playlist
    if player not in player_pages_playlist:
        player_pages_playlist[player] = 1
    current_page, start_idx, end_idx, total_pages, total_songs, songs_data = get_current_page_playlist(player)
    if player_pages_playlist.get(player, 1) < total_pages:
        player_pages_playlist[player] += 1
        source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
        source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')
        playlists = load_player_playlists(player)
        if playlists:

            results = {}
            for idx in range(start_idx, end_idx):
                playlist = playlists[idx]
        # 查找json_data中link字段匹配的项
                song = next((item for item in songs_data if item['link'] == playlist), None)
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
                if song:
                    results[playlist] = {"name": song['name'], "artist": song['artist']}

        else:
            source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"已经是最后一页。","color":"red"}]')


def add_song_to_json(source: 'PlayerCommandSource', args):
    song_name = args['song_name'].replace("_", " ")
    song_artists = args['song_artists'].replace("_", " ")
    song_link = args['song_link']
    with open(songs_json_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)

    if isinstance(song_artists, str):
        artists = [artist.strip() for artist in song_artists.split(',')]
    else:
        artists = song_artists

    new_song = {
        "name": song_name,
        "link": song_link,
        "artist": artists
    }
    songs_data.append(new_song)

    with open(songs_json_file, 'w', encoding='utf-8') as f:
        json.dump(songs_data, f, indent=4)




def search_songs(source: 'PlayerCommandSource', args):
    keyword = args['keyword']
    player = source.get_info().player
    with open(songs_json_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)

    '''search_results = []
    for song in songs_data:
        if keyword.lower() in song['name'].lower() or any(keyword.lower() in artist.lower() for artist in song['artist']):
            search_results.append(song)'''
    matching_songs = [
            (idx, song) for idx, song in enumerate(songs_data)
            if keyword.lower() in song['name'].lower() or any(keyword.lower() in artist.lower() for artist in song['artist'])
        ]
    
    '''if search_results:
        source.get_server().execute(f'tellraw {player} "搜索结果："')
        for idx, song in enumerate(search_results, start=1):
            artists = ", ".join(song['artist'])  # 将作者列表转换为字符串
            source.get_server().execute(f'tellraw {player} "{idx}. {song['name']} - {artists}"')'''
    if matching_songs:
            source.get_server().execute(f'tellraw {player} "找到 {len(matching_songs)} 首匹配的歌曲:"')
            for idx, song in matching_songs:
                artists = ", ".join(song['artist'])
                source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"未找到匹配的歌曲。","color":"red"}]')

def playlists_search_songs(source: 'PlayerCommandSource', args):
    keyword = args['keyword']
    player = source.get_info().player
    player_playlists = load_player_playlists(player)
    with open(songs_json_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)
    matching_songs = []
    for idx, link in enumerate(player_playlists):
        # Find the song in songs_data with the matching link
        song = next((song for song in songs_data if song['link'] == link), None)
        if song and (keyword.lower() in song['name'].lower() or any(keyword.lower() in artist.lower() for artist in song['artist'])):
            matching_songs.append((idx, song))

    if matching_songs:
        source.get_server().execute(f'tellraw {player} "找到 {len(matching_songs)} 首匹配的歌曲:"')
        for playlist_idx, song in matching_songs:
            artists = ", ".join(song['artist'])
            source.get_server().execute(f'tellraw {player} "{playlist_idx + 1}. {song["name"]} - {artists}"')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"未找到匹配的歌曲。","color":"red"}]')

####################
        ############
        ############################
        ###################
def list_playlist(source: 'PlayerCommandSource'):
    player = source.get_info().player

    playlists = load_player_playlists(player)
        
    total_songs_playlist = len(playlists)
    global player_pages_playlist
    total_pages_playlist = (total_songs_playlist + items_per_page - 1) // items_per_page

    if player not in playlists:
        player_pages_playlist[player] = 1
    current_page = player_pages_playlist.get(player, 1)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(current_page * items_per_page, total_songs_playlist)
    source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages_playlist}"')
    source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')
    _, start_idx_all, end_idx_all, _, songs_data = get_current_page(player)
    
    if playlists:
        '''for idx in range(start_idx, end_idx):
            song = songs_data[songs_data.index({'link': playlists[idx]})]
            song = next((i for i, item in enumerate(songs_data) if item['link'] == playlists), None)
            artists = ", ".join(song['artist'])
            source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
        
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')'''
        results = {}
        for idx in range(start_idx, end_idx):
            playlist = playlists[idx]
            song = next((item for item in songs_data if item['link'] == playlist), None)
            # 提取name和artist
            artists = ", ".join(song['artist'])
            source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
            if song:
                results[playlist] = {"name": song['name'], "artist": song['artist']}

    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')




def list_all_songs(source: 'PlayerCommandSource'):
    player = source.get_info().player
    with open(songs_json_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)

    total_songs = len(songs_data)
    global total_pages
    global player_pages
    total_pages = (total_songs + items_per_page - 1) // items_per_page

    # 获取初始化当前页
    if player not in player_pages:
        player_pages[player] = 1
    current_page = player_pages.get(player, 1)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(current_page * items_per_page, total_songs)
    source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
    source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')

    if songs_data:
        for idx in range(start_idx, end_idx):
            song = songs_data[idx]
            artists = ", ".join(song['artist'])
            source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} - {artists}"')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')

def list_all_links(source: 'PlayerCommandSource'):
    player = source.get_info().player
    with open(songs_json_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)

    total_songs = len(songs_data)
    global total_pages
    total_pages = (total_songs + items_per_page - 1) // items_per_page

    current_page = player_pages.get(player, 1)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(current_page * items_per_page, total_songs)
    source.get_server().execute(f'tellraw {player} "当前页: {current_page}/{total_pages}"')
    source.get_server().execute(f'tellraw {player} "显示歌曲: {start_idx + 1} 到 {end_idx}"')

    if songs_data:
        for idx in range(start_idx, end_idx):
            song = songs_data[idx]
            link = song['link']
            source.get_server().execute(f'tellraw {player} "{idx + 1}. {song['name']} : {link}"')
    else:
        source.get_server().execute(f'tellraw {player}' + ' [{"text":"暂无歌曲记录。","color":"red"}]')


def get_current_page(player):
    with open(songs_json_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)

    total_songs = len(songs_data)
    global total_pages
    total_pages = (total_songs + items_per_page - 1) // items_per_page

    current_page = player_pages.get(player, 1)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(current_page * items_per_page, total_songs)

    return current_page, start_idx, end_idx, total_pages, songs_data

def get_current_page_playlist(player):
    player_file = f"{player}.json"
    with open(player_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)

    total_songs = len(songs_data)
    total_pages = (total_songs + items_per_page - 1) // items_per_page

    current_page = player_pages.get(player, 1)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(current_page * items_per_page, total_songs)

    return current_page, start_idx, end_idx, total_pages, total_songs, songs_data


def create_midiplayer_folder():
    current_dir = os.getcwd()

    config_dir = os.path.join(current_dir, 'config')

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    midiplayer_dir = os.path.join(config_dir, 'midiplayer')
    if not os.path.exists(midiplayer_dir):
        os.makedirs(midiplayer_dir)

    songs_json_file = os.path.join(midiplayer_dir, 'songs.json')
    if not os.path.exists(songs_json_file):
        with open(songs_json_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
    
    return songs_json_file
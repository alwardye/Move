# kivy imports
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivy.factory import Factory
from kivy.uix.screenmanager import ScreenManager
from android.permissions import request_permissions, Permission

# python imports
import pickle
import webbrowser
import sqlite3
import json
import os
from jnius import autoclass

# app imports
from asset import (
	refresh_build,
	movie_list_build,
	preview_build,
	download_picture,
	discover_new_movies,
	double_link_build,
	drop_down_build,
	search_build,
	about_view_build,
	export_database,
	youtube_build
)

Environment = autoclass('android.os.Environment')
external_disk = Environment.getExternalStorageDirectory().getAbsolutePath()
external_disk = f'{external_disk}/'

try:
	export_database(external_disk)
	conn = sqlite3.connect(f'{external_disk}/Movies/movies.db')
except:
	conn = sqlite3.connect('movies.db')


Builder.load_string(''' 
#:import NoTransition kivy.uix.screenmanager.NoTransition
#:import MovieItem asset.MovieItem
		

<Movies>:
	transition: NoTransition()
	canvas.before:
		Color:
			rgba: app.theme
		Rectangle:
			size: self.size
			pos: self.pos
	
	Screen:
		name: 'base'
		BoxLayout:
			orientation: 'vertical'
			Widget:
				size_hint_y: None
				height: dp(60)
				
			RecycleList:
				id: list_view
			
			
		MDToolbar:
			md_bg_color: app.ascent
			background_palette: "Primary"
			title: 'Movies'
			background_hue: "500"
			specific_text_color: app.theme_text
			elevation: 10
			text_color: 1, 1, 1, 1
			pos_hint: {'top': 1}
			right_action_items:
				[["magnify", lambda x: app.root.show_search()], 
				["refresh", lambda x: app.root.refresh()],
				["dots-vertical", lambda x: app.root.drop_down()]]
			
				
	Screen:
		name: 'preview'
		id: preview
		
													
<RecycleList@RecycleView>:
	bar_color: app.ascent
	bar_width: dp(10) if len(self.data) > 200 else dp(2)
	scroll_type: ['content', 'bars']
	viewclass: 'MovieItem'
	RecycleBoxLayout:
		spacing: dp(10)
		padding: dp(15)
		default_size: None, dp(70)
		default_size_hint: 1, None
		size_hint_y: None
		height: self.minimum_height
		orientation: 'vertical'

''')


class Movies(ScreenManager):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.refresh_loader = None
		self.preview_layout = None
		self.double_layout = None
		self.drop_down_layout = None
		self.search_layout = None
		self.about_app_layout = None
		self.youtube_layout = None

		self.modified = False
		self.showing_search = False
		request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])


		movie_list_build(self, conn, True)

	def preview(self, name: str) -> None:
		data = conn.execute('SELECT picture, runtime, desc, picture_link FROM Movies WHERE name=?', (name,))
		data = data.fetchone()

		if not self.preview_layout:
			preview_build(self)

		self.preview_layout.ids.title.title = name
		self.preview_layout.ids.runtime.text = data[1]
		self.preview_layout.ids.desc.text = data[2]

		if os.path.exists(data[0]):
			self.preview_layout.ids.image.source = data[0]
		else:
			self.preview_layout.ids.image.source = 'downloading.png'
			download_picture(
				[data[-1], data[0]], True
			)

		self.current = 'preview'

	def refresh(self):
		if not self.refresh_loader:
			refresh_build(self)

		Window.add_widget(self.refresh_loader)
		refresh_title = self.refresh_loader.ids.text.text

		if refresh_title == 'Download complete' or refresh_title == '[color=ff0000]Network Error':
			data = conn.execute('SELECT id, name FROM Movies ORDER BY id DESC')
			data = data.fetchone()

			discover_new_movies(
				data,
				self.refresh_loader,
				launch=True
			)

	def download_link(self, name):
		data = conn.execute('SELECT link FROM Movies WHERE name=?', (name,))
		data = data.fetchone()

		link = json.loads(data[0])

		if len(link) == 1:
			self.download(link[0])
		else:

			if not self.double_layout:
				double_link_build(self)

			self.double_layout.link1 = link[0]
			self.double_layout.link2 = link[1]
			Window.add_widget(self.double_layout)

	@staticmethod
	def download(link):
		webbrowser.open(link)

	@mainthread
	def update_movies_view(self, data: list):
		self.ids.list_view.data.insert(0, {
			'title': data[1], 'item_id': data[0]
		})
		self.ids.list_view.refresh_from_data()

		conn.execute('INSERT INTO Movies VALUES (?,?,?,?,?,?,?)', data)
		conn.commit()

	@mainthread
	def update_image(self, file):
		self.preview_layout.ids.image.source = file

	def show_youtube(self):
		youtube_build(self)
		Window.add_widget(self.youtube_layout)

	def trailer(self, root):
		Window.remove_widget(root)
		name = self.preview_layout.ids.title.title
		link_ = 'https://m.youtube.com/results?search_query='+name+' trailer'.replace(' ', '+')
		webbrowser.open(link_)

	def back(self):
		self.current = 'base'

	def drop_down(self):
		if not self.drop_down_layout:
			drop_down_build(self)

		Window.add_widget(self.drop_down_layout)

	def drop_action(self, nav: str):
		list_view = self.ids.list_view

		if self.modified:
			data = conn.execute('SELECT id, name FROM Movies ORDER BY id DESC')
			data = [{'title': item[1], 'item_id': item[0]} for item in data.fetchall()]
		else:
			data = list_view.data

		if nav == 'a/z':
			list_view.data = sorted(data, key=lambda i: i['title'])
		elif nav == 'latest':
			list_view.data = reversed(sorted(data, key=lambda i: i['item_id']))
		elif nav == 'oldest':
			list_view.data = sorted(data, key=lambda i: i['item_id'])
		else:
			if not self.about_app_layout:
				about_view_build(self)

			Window.add_widget(self.about_app_layout)

		list_view.refresh_from_data()
		list_view.scroll_y = 1
		self.modified = False
		Window.remove_widget(self.drop_down_layout)

	def show_search(self):
		if not self.search_layout:
			search_build(self)

		Window.add_widget(self.search_layout)
		self.showing_search = True
		self.search_layout.ids.input.focus = True

	def search(self, key):
		Window.remove_widget(self.search_layout)
		self.showing_search = False

		if key:
			if self.modified:
				data = conn.execute('SELECT id, name FROM Movies ORDER BY id DESC')
				data = [{'title': item[1], 'item_id': item[0]} for item in data.fetchall()]
			else:
				data = self.ids.list_view.data

			result = []

			for item in data:
				if key.lower() in item['title'].lower():
					result.append(item)

			self.ids.list_view.data = result
			self.ids.list_view.refresh_from_data()
			self.ids.list_view.scroll_y = 1

			self.modified = True


class MovieApp(MDApp):
	theme = .12, .12, .14, 1
	theme_text = 1, 1, 1, 1
	theme_bars = .14, .14, .16, 1
	ascent = 1, 36/255, 0, 1

	def __init__(self, **kwargs):
		self.title = 'Movies'
		self.theme_cls.primary_palette = "Orange"
		super(MovieApp, self).__init__(**kwargs)
	
	def build(self):
		Window.bind(on_keyboard=self.android_nav)
		self.root = Factory.Movies()
	
	def android_nav(self, __, key, *_):

		if key == 27:
			if self.root.current == 'base':
				sys.exist()
				

			self.root.current = 'base'
			return True
		elif key == 13:
			if self.root.showing_search:
				key = self.root.search_layout.ids.input.text
				self.root.search(key)

			return True


MovieApp().run()

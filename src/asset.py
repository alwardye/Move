import shutil
import requests
from json import dumps
from kivy.uix.image import Image
from bs4 import BeautifulSoup as bs
import random
import os
from kivy.logger import Logger

from kivy.animation import Animation
from kivy.app import App
from threading import Thread
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (
    NumericProperty,
    ListProperty,
    StringProperty,
    BooleanProperty
)
from kivymd.uix.behaviors import RectangularRippleBehavior, BackgroundColorBehavior
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.behaviors.backgroundcolorbehavior import (
    SpecificBackgroundColorBehavior,
)
from kivymd.uix.behaviors import (
    CircularRippleBehavior,
    RectangularRippleBehavior,
)
from kivy.graphics import (
    Color,
    Ellipse,
    StencilPush,
    StencilPop,
    StencilUse,
    StencilUnUse,
    Rectangle,
    RoundedRectangle,
)

Builder.load_string("""
#:import Window kivy.core.window.Window

<MovieItem>:
    title: ''
    item_id: 0
    radius: dp(2)
    ripple_scale: dp(40)
    
    MDCard:
        pos_hint: {'center_x': .5, 'center_y': .5}
        md_bg_color: app.theme_bars
        padding: [dp(5), dp(5)]
        MDLabel:
            text: root.title
            font_size: dp(15)
            theme_text_color: 'Custom'
            text_color: app.theme_text
            halign: 'center'
            
    Button:
        background_color: 0, 0, 0, 0
        pos_hint: {'center_x': .5, 'center_y': .5}
        on_release: app.root.preview(root.title)

""")


refresh = """
FloatLayout:
    Button:
        background_color: 0, 0, 0, .7
        on_release: Window.remove_widget(root)
        
    BoxLayout:
        orientation: 'vertical'
        padding: [dp(10), dp(20)]
        pos_hint: {'center_x': .5, 'center_y': .5}
        size_hint: .8, None
        height: dp(80)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: app.theme 
            RoundedRectangle:
                size: self.size
                pos: self.pos
                radius: [dp(5)]
                
        BoxLayout:
            MDLabel:
                id: text
                text: 'Download complete'
                font_size: dp(15)
                theme_text_color: 'Custom'
                text_color: app.theme_text
                markup: True
                
            MDLabel:
                id: num_info
                text: '--'
                font_size: dp(15)
                theme_text_color: 'Custom'
                text_color: .6, .6, .6, 1
                halign: 'right'
            
        ProgressLoader:
            id: progress
            size_hint_y: None
            height: dp(5)
            
        
<ProgressLoader@Widget>:
    max: 100
    value: 1
    canvas.before:
        Color:
            rgba: app.theme_bars
        Rectangle:
            size: self.size
            pos: self.pos
        
    canvas.after:
        Color:
            rgba: app.ascent
        Rectangle:
            size: self.size[0]*(root.value/root.max), self.size[1]
            pos: self.pos
        
"""

preview = """
BoxLayout:
    orientation: 'vertical'
        
    MDToolbar:
        id: title
        md_bg_color: app.ascent
        background_palette: "Primary"
        title: ' '
        specific_text_color: app.theme_text
        background_hue: "500"
        elevation: 10
        text_color: 1, 1, 1, 1
        pos_hint: {'top': 1}
        left_action_items: [['chevron-left', lambda x: app.root.back()]]
        right_action_items: [["download", lambda x: app.root.download_link(self.title)]]
        
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(20)
        padding: [dp(15), dp(15)]
        
        Widget:
            size_hint_y: None
            height: dp(5)
        
        ClickableImage:
            id: image
            size_hint_y: .6
            source: ''
            allow_stretch: True
            on_release: app.root.show_youtube()
            
        MDCard:
            md_bg_color: app.theme_bars
            size_hint: None, None
            pos_hint: {'center_x': .5}
            height: dp(30)
            Label:
                id: runtime
                font_size: dp(15)
                color: app.theme_text
                markup: True
        
        
        ScrollView:
            size_hint: 0.9,0.50
            pos_hint: {'center_x': .5}
            bar_width: dp(0)
            bar_color: app.theme_cls.primary_color
            MDCard:
                md_bg_color: app.theme_bars
                size_hint_y: None
                padding: [dp(10), dp(10)]
                orientation: 'vertical'
                height: self.minimum_height	
                Label:
                    id: desc
                    text: ''
                    font_size: dp(13)
                    markup: True
                    halign: 'center'
                    text_size: self.width, None
                    size_hint: 1, None
                    height: self.texture_size[1]
                    
                
<ClickableImage@ButtonBehavior+Image>:

"""

double_link = """
FloatLayout:
    link1: ''
    link2: ''
    Button:
        background_color: 0, 0, 0, .7
        on_release: Window.remove_widget(root)
        
    BoxLayout:
        orientation: 'vertical'
        padding: [dp(15), dp(15)]
        pos_hint: {'center_x': .5, 'center_y': .5}
        size_hint: .8, None
        height: dp(150)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: app.theme 
            RoundedRectangle:
                size: self.size
                pos: self.pos
                radius: [dp(5)]
                
        MDLabel:
            text: 'Looks like there are two parts'
            font_size: dp(15)
            theme_text_color: 'Custom'
            text_color: app.theme_text
            halign: 'center'
            
        MDRaisedButton:
            md_bg_color: app.ascent
            text: 'Part 1'
            size_hint: 1, 1
            theme_text_color: 'Custom'
            text_color: app.theme_text
            on_release: 
                app.root.download(root.link1)
            
        MDRaisedButton:
            md_bg_color: app.ascent
            text: 'Part 2'
            size_hint: 1, 1
            theme_text_color: 'Custom'
            text_color: app.theme_text
            on_release:
                Window.remove_widget(root)
                app.root.download(root.link2)
"""

drop_down = """
FloatLayout:
    positions: Window.size[0] - dp(155), Window.size[1] - dp(185)
    Button:
        background_color: 0, 0, 0, 0
        on_press: Window.remove_widget(root)
    MDCard:
        pos: root.positions
        size_hint: None, None
        size: dp(150), dp(180)
        md_bg_color: app.theme
        orientation: 'vertical'
        padding: [dp(2), dp(2)]
        DropBtn:
            text: 'Order A/Z'
            on_release: app.root.drop_action('a/z')
        DropBtn:
            text: 'Order Latest'
            on_release: app.root.drop_action('latest')
        DropBtn:
            text: 'Order Oldest'
            on_release: app.root.drop_action('oldest')
            
<DropBtn>:
    background_color: 0, 0, 0, 0
    font_size: dp(15)
    color: app.theme_text
"""

search = """
BoxLayout:
    size_hint_y: None
    height: dp(64)
    padding: dp(10)
    pos_hint: {'top': 1}
    canvas.before:
        Color:
            rgba: app.theme_bars
        Rectangle:
            size: self.size
            pos: self.pos
            
    TextInput:
        id: input
        hint_text: 'Search...'
        size_hint_y: .8
        font_size: dp(16)
        valign: 'bottom'
        multiline: False
        cursor_color: app.ascent
        background_color: 0, 0, 0, 0
        foreground_color: app.theme_text
    
    MDIconButton:
        icon: 'magnify'   
        theme_text_color: 'Custom'
        text_color: app.theme_text
        on_release: app.root.search(root.ids.input.text)
        
    MDIconButton:
        icon: 'close'   
        theme_text_color: 'Custom'
        text_color: 1, 0, 0, 1
        on_release: 
            app.root.showing_search = False
            Window.remove_widget(root)
"""

about = """
BoxLayout:
    orientation: 'vertical'
    padding: [dp(20), dp(20)]
    spacing: dp(20)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            size: self.size
            pos: self.pos
    
    Label:
        text: 'About'
        font_size: dp(16)
        color: app.ascent
        size_hint_y: None
        height: dp(30)
        
         
    BoxLayout:
        size_hint_x: .8
        pos_hint: {'center_x': .5}
        canvas.before:
            Color:
                rgba: app.ascent
            RoundedRectangle:
                size: self.size
                pos: self.pos
                radius: [dp(10)]
            
    MDRaisedButton:
        md_bg_color: app.ascent
        text: 'Done'
        theme_text_color: 'Custom'
        text_color: app.theme_text
        pos_hint: {'center_x': .5}
        on_release: Window.remove_widget(root)
    
"""

youtube = """
FloatLayout:
    Button:
        background_color: 0, 0, 0, .7
        on_release: Window.remove_widget(root)
        
    BoxLayout:
        orientation: 'vertical'
        padding: [dp(10), dp(10)]
        pos_hint: {'center_x': .5, 'center_y': .5}
        size_hint: .8, None
        height: dp(100)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: app.theme 
            RoundedRectangle:
                size: self.size
                pos: self.pos
                radius: [dp(5)]
                
        MDLabel:
            text: 'Watch the youtube trailer'
            font_size: dp(15)
            theme_text_color: 'Custom'
            halign: 'center'
            text_color: app.theme_text
            
        BoxLayout:
            spacing: dp(5)
        
            MDRaisedButton:
                md_bg_color: app.ascent
                text: 'Yeah'
                theme_text_color: 'Custom'
                size_hint: 1, 1
                text_color: app.theme_text
                pos_hint: {'center_x': .5}
                on_release: app.root.trailer(root)
        
            MDRaisedButton:
                md_bg_color: app.theme_bars
                text: 'Nah'
                theme_text_color: 'Custom'
                size_hint: 1, 1
                text_color: 1, 0, 0, 1
                pos_hint: {'center_x': .5}
                on_release: Window.remove_widget(root)
"""


class CommonRipple(object):
    ripple_rad = NumericProperty()
    ripple_rad_default = NumericProperty(1)
    ripple_post = ListProperty()
    ripple_color = ListProperty([.4, .4, .42, 1])
    ripple_alpha = NumericProperty(0.5)
    ripple_scale = NumericProperty(None)
    ripple_duration_in_fast = NumericProperty(0.3)
    # FIXME: These speeds should be calculated based on widget size in dp
    ripple_duration_in_slow = NumericProperty(2)
    ripple_duration_out = NumericProperty(0.3)
    ripple_func_in = StringProperty("out_quad")
    ripple_func_out = StringProperty("out_quad")

    doing_ripple = BooleanProperty(False)
    finishing_ripple = BooleanProperty(False)
    fading_out = BooleanProperty(False)
    _no_ripple_effect = BooleanProperty(False)

    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False

        if not self.disabled:
            if self.doing_ripple:
                Animation.cancel_all(
                    self, "ripple_rad", "ripple_color", "rect_color"
                )
                self.anim_complete()
            self.ripple_rad = self.ripple_rad_default
            self.ripple_pos = (touch.x, touch.y)

            if self.ripple_color:
                pass
            elif hasattr(self, "theme_cls"):
                self.ripple_color = self.theme_cls.ripple_color
            else:
                # If no theme, set Gray 300
                self.ripple_color = [
                    0.8784313725490196,
                    0.8784313725490196,
                    0.8784313725490196,
                    self.ripple_alpha,
                ]
            self.ripple_color[3] = self.ripple_alpha

            self.lay_canvas_instructions()
            self.finish_rad = max(self.width, self.height) * self.ripple_scale
            self.start_ripple()
        return super().on_touch_down(touch)

    def lay_canvas_instructions(self):
        raise NotImplementedError

    def on_touch_move(self, touch, *args):
        if not self.collide_point(touch.x, touch.y):
            if not self.finishing_ripple and self.doing_ripple:
                self.finish_ripple()
        return super().on_touch_move(touch, *args)

    def on_touch_up(self, touch):
        if self.collide_point(touch.x, touch.y) and self.doing_ripple:
            self.finish_ripple()
        return super().on_touch_up(touch)

    def start_ripple(self):
        if not self.doing_ripple:
            anim = Animation(
                ripple_rad=self.finish_rad,
                t="linear",
                duration=self.ripple_duration_in_slow,
            )
            anim.bind(on_complete=self.fade_out)
            self.doing_ripple = True
            anim.start(self)

    def _set_ellipse(self, instance, value):
        self.ellipse.size = (self.ripple_rad, self.ripple_rad)

    # Adjust ellipse pos here

    def _set_color(self, instance, value):
        self.col_instruction.a = value[3]

    def finish_ripple(self):
        if self.doing_ripple and not self.finishing_ripple:
            Animation.cancel_all(self, "ripple_rad")
            anim = Animation(
                ripple_rad=self.finish_rad,
                t=self.ripple_func_in,
                duration=self.ripple_duration_in_fast,
            )
            anim.bind(on_complete=self.fade_out)
            self.finishing_ripple = True
            anim.start(self)

    def fade_out(self, *args):
        rc = self.ripple_color
        if not self.fading_out:
            Animation.cancel_all(self, "ripple_color")
            anim = Animation(
                ripple_color=[rc[0], rc[1], rc[2], 0.0],
                t=self.ripple_func_out,
                duration=self.ripple_duration_out,
            )
            anim.bind(on_complete=self.anim_complete)
            self.fading_out = True
            anim.start(self)

    def anim_complete(self, *args):
        self.doing_ripple = False
        self.finishing_ripple = False
        self.fading_out = False
        self.canvas.after.clear()


class BorderRipple(CommonRipple):
    ripple_scale = NumericProperty(2.75)
    radius = NumericProperty(dp(10))

    def lay_canvas_instructions(self):
        if self._no_ripple_effect:
            return
        with self.canvas.after:
            StencilPush()
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            StencilUse()
            self.col_instruction = Color(rgba=self.ripple_color)
            self.ellipse = Ellipse(
                size=(self.ripple_rad, self.ripple_rad),
                pos=(
                    self.ripple_pos[0] - self.ripple_rad / 2.0,
                    self.ripple_pos[1] - self.ripple_rad / 2.0,
                ),
            )
            StencilUnUse()
            Rectangle(pos=self.pos, size=self.size)
            StencilPop()
        self.bind(ripple_color=self._set_color, ripple_rad=self._set_ellipse)

    def _set_ellipse(self, instance, value):
        super()._set_ellipse(instance, value)
        self.ellipse.pos = (
            self.ripple_pos[0] - self.ripple_rad / 2.0,
            self.ripple_pos[1] - self.ripple_rad / 2.0,
        )


class MovieItem(BorderRipple, FloatLayout):
    pass


class DropBtn(ButtonBehavior, RectangularRippleBehavior, BackgroundColorBehavior, Label):
    pass


def get_content(url: str, raw: bool = False):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel 	Mac OS X 10_11_5) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.'
                      '2661.102 Safari/537.36'
    }

    try:
        result = requests.get(url, headers=headers)

        if raw:
            return result.raw
        return bs(result.text, 'html.parser')
    except:
        ids = App.get_running_app().root.refresh_loader.ids
        ids.text.text = '[color=ff0000]Network Error'
        ids.num_info.text = '--'
        exit()


def get_index_details(url: str):
    movies = []
    content = get_content(url)
    content = content.find_all('div', class_='listing')

    for movie in content:
        movies.append([
            movie.a.text,
            movie.a['href']
        ])
    return movies


def generate_link(name: str, links_no: int):
    links = []

    rand_ = random.randint(1, 4)
    parent = f'http://hd{rand_}.dlmania.com/Hollywood/'
    ending = ' HD (HDMp4Mania).mp4'

    if links_no == 1:
        links.append(f'{parent}{name}/{name}{ending}')

    elif links_no == 2:
        links.append(f'{parent}{name}/{name} HD 1.mp4')
        links.append(f'{parent}{name}/{name} HD 2.mp4')

    links = [link.replace(' ', '%20') for link in links]

    return links


def get_movies_details(movies: list, ui_class: classmethod, movie_id):
    movie_id += 1

    for i, movie in enumerate(list(reversed(movies))):
        entry_url = movie[1]

        content = get_content('https://hdmp4mania1.net/' + entry_url)

        links_no = len(content.find_all('div', class_='download'))
        links = generate_link(movie[0], links_no)

        pic = content.find_all('div', class_='logo')
        pic = pic[-2].img['src']
        pic_link = f'https:{pic}'.replace(' ', '%20')
        pic = f"Pic/{pic.split('/')[-1]}"

        description_section = content.find_all('div', class_='description')
        description = (':'.join(description_section[3].text.split(':')[1:])).strip()

        runtime = (':'.join(description_section[4].text.split(':')[1:])).strip()

        data = [movie_id, movie[0], pic, description, runtime, dumps(links), pic_link]

        ui_class.ids.num_info.text = f'{i + 1}/{len(movies)}'
        ui_class.ids.progress.value = i + 1

        App.get_running_app().root.update_movies_view(data)

        movie_id += 1

    ui_class.ids.text.text = 'Download complete'


def discover_new_movies(known: list, callback: classmethod, launch: bool):
    if launch:
        thread = Thread(target=discover_new_movies, args=[
            known, callback, False
        ])
        thread.setDaemon(True)
        thread.start()
    else:
        ui_class = callback
        index = 1
        new_movies = []
        discover_loop = True

        ui_class.ids.text.text = 'Discovering...'
        ui_class.ids.progress.max = 100
        ui_class.ids.progress.value = 1

        while discover_loop:
            url = f'https://hdmp4mania1.net/showcat.php?catid=2&sort=1&letter=&page={index}'
            movie_list = get_index_details(url)
            index += 1

            for movie in movie_list:
                if movie[0] == known[1]:
                    discover_loop = False
                    break
                else:
                    new_movies.append(movie)
                    ui_class.ids.num_info.text = str(len(new_movies))

        # scrapping info
        if new_movies:
            ui_class.ids.progress.max = len(new_movies)
            ui_class.ids.progress.value = 0
            ui_class.ids.text.text = 'Downloading...'
            get_movies_details(new_movies, ui_class, known[0])
        else:
            ui_class.ids.progress.max = 100
            ui_class.ids.progress.value = 100
            ui_class.ids.num_info.text = ''
            ui_class.ids.text.text = 'You are up to date'


def refresh_build(root):
    root.refresh_loader = Builder.load_string(refresh)
    

def preview_build(root):
    root.preview_layout = Builder.load_string(preview)
    root.ids.preview.add_widget(root.preview_layout)


def movie_list_build(root, movies_list, launch: bool):
    if launch:
        data = movies_list.execute('SELECT id, name FROM Movies ORDER BY id')
        data = data.fetchall()
        thread = Thread(target=movie_list_build, args=[
            root, data, False
        ])
        thread.setDaemon(True)
        thread.start()
    else:
        data = []
        for movie in reversed(movies_list):
            data.append({
                'title': movie[1],
                'item_id': movie[0]
            })
        root.ids.list_view.data = data
        root.ids.list_view.refresh_from_data()


def download_picture(link: list, launch: bool):
    if launch:
        thread = Thread(target=download_picture, args=[
            link, False
        ])
        thread.setDaemon(True)
        thread.start()
    else:
        try:
            response = requests.get(link[0], stream=True)
            with open(link[1], 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            
            App.get_running_app().root.update_image(link[1])
        except Exception as e:
            Logger.error(str(e))
            Logger.info(link[1])
            App.get_running_app().root.update_image('failed.png')
        

def double_link_build(root):
    root.double_layout = Builder.load_string(double_link)


def drop_down_build(root):
    root.drop_down_layout = Builder.load_string(drop_down)


def search_build(root):
    root.search_layout = Builder.load_string(search)


def youtube_build(root):
    if not root.youtube_layout:
        root.youtube_layout = Builder.load_string(youtube)


def about_view_build(root):
    root.about_app_layout = Builder.load_string(about)


def export_database(external: str):
    if not os.path.exists(f'{external}Movies'):
        os.mkdir(f'{external}Movies')
        
    if not os.path.exists(f'{external}Movies/movies.db'):
        with open(f'{os.getcwd()}/movies.db', 'rb') as file:
            data = file.read()
            
        with open(f'{external}Movies/movies.db', 'wb') as file:
            file.write(data)



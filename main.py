import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from android.permissions import request_permissions, Permission
import glob
import os
from os.path import join
from jnius import autoclass
import html2txt

Window.clearcolor = (1, 1, 1, 1)

class CustomTextInput(TextInput):
    # https://github.com/kivy/kivy/issues/6473
    def _hide_cut_copy_paste(self, win = None):
        bubble = self._bubble
        if not bubble:
            return

Builder.load_string('''
<Urlpup>:
    size_hint: .7, .7
    auto_dismiss: False
    title: 'Enter URL'
    BoxLayout:
        orientation: 'vertical'
        CustomTextInput:
            id: url_input
            focus: True
            multiline: False
        Button:
            text: 'OK'    
            on_press: root.dismiss()
            on_release: app.create_new_article(url_input.text) 
''')

class Urlpup(Popup):
    pass


class MyScatter(ScatterLayout):
    pass

Builder.load_string('''
<MyScatter>:
    scale: 1
    do_scale: True 
    do_translation: True
    do_rotation: False
    auto_bring_to_front: False

    Image:
        id: img
        source: ''
        size_hint: (0.43, 0.6)
        pos_hint: {'center_x': 0.33, 'center_y': 0.5}
        keep_ratio: True
''')

Builder.load_string(''' 
<ScrollableLabel>: 
    text: ''
    scroll_y: 1
    Label: 
        text: root.text 
        text_size: self.width, None
        size_hint: (1, None)
        height: self.texture_size[1]
        color: (0, 0, 0, 1)
        halign: "center"
''') 
  
class ScrollableLabel(ScrollView): 
    text = StringProperty('') 

class Tedegraph(App):
    def build(self):
        
        mainbox = FloatLayout()
        
        self.ms = MyScatter()
        mainbox.add_widget(self.ms)
        mainbox.add_widget(Button(text="Fwd",
                                  font_size="17dp",
                                  size_hint=(.075, .15),
                                  pos_hint={"left":1,
                                            "center_y":0.5},
                                  on_press=self.forward))

        self.text_label = ScrollableLabel(pos_hint = {"right":0.90, "top":0.720}, size_hint = (0.43, 0.6))

        mainbox.add_widget(self.text_label)
        mainbox.add_widget(Button(text="Fwd",
                                  font_size="17dp",
                                  size_hint=(.075, .15),
                                  pos_hint={"right":1,
                                            "center_y":0.5},
                                  on_press=self.forward))
        mainbox.add_widget(Button(text="Back",
                                  font_size="17dp",
                                  size_hint=(.075, .15),
                                  pos_hint={"right":1,
                                            "top":1},
                                  on_press=self.backward))
        mainbox.add_widget(Button(text="Bookmark",
                                  font_size="17dp",
                                  size_hint=(.15, .075),
                                  pos_hint={"center_x":0.5,
                                            "bottom":1},
                                  on_press=self.add_bookmark))
        mainbox.add_widget(Button(text="New",
                                    font_size="17dp",
                                    size_hint=(.15, .075),
                                    pos_hint={"center_x":0.3,
                                              "bottom":1},
                                    on_press=self.create_new_article_popup))
        self.init()
        self.spinner_articles = Spinner(text ="Choose article", 
                values = sorted([d for d in os.listdir(self.working_directory) \
                            if os.path.isdir(os.path.join(self.working_directory, d))]),
                size_hint = (0.4, 0.075),
                pos_hint = {"right": 1, 'bottom':1} 
                ) 
        self.spinner_articles.bind(text = self.on_spinner_select)
        mainbox.add_widget(self.spinner_articles)
        return mainbox

    def download_nltk(self):
        if not os.path.isdir(os.path.join(self.data_dir, "nltk_data")):
            os.chdir(self.data_dir)
            
            # https://stackoverflow.com/questions/38916452/nltk-download-ssl-certificate-verify-failed
            import nltk
            import ssl
            try:
                try:
                    _create_unverified_https_context = ssl._create_unverified_context
                except AttributeError:
                    pass
                else:
                    ssl._create_default_https_context = _create_unverified_https_context
                nltk.download('punkt')
                return True
            except:
                popup = Popup(title='No Internet connection',
                              size_hint = (None, None), size = (400, 400),
                              auto_dismiss=True)
                popup.open()
                return False
        return True


    def init(self):
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                             Permission.READ_EXTERNAL_STORAGE])
        try:
            Environment = autoclass('android.os.Environment')
            self.working_directory = os.path.join(Environment.getExternalStorageDirectory().getAbsolutePath(), "tdg_articles")
        except:
            self.working_directory = os.path.join(App.get_running_app().user_data_dir, "tdg_articles")
        
        if not os.path.exists(self.working_directory):
            os.makedirs(self.working_directory)
        
        self.data_dir = os.path.join(os.path.abspath(getattr(self, 'user_data_dir')), "nltk")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        os.chdir(self.working_directory)
        self.lines = []
        self.line_number = 0
        self.article_part = 0
        self.article_parts = []
        self.current_article = None
    
    def forward(self, *args):
        if not self.current_article:
            return
        os.chdir(os.path.join(self.working_directory, self.current_article))
        if self.line_number < len(self.lines) - 1:
            self.line_number = self.line_number + 1
            self.text_label.text = self.lines[self.line_number]
            self.text_label.scroll_y = 1
        elif self.article_part < len(self.article_parts) - 1:
            self.article_part = self.article_part + 1
            f = open(self.article_parts[self.article_part], encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            self.line_number = 0
            f.close()
            img_file_name = self.article_parts[self.article_part].replace(".txt", "")
            images = [fn for fn in glob.glob(img_file_name + "*") if not fn.endswith("txt")]
            if images:
                img_file_name = images[0]
                self.ms.ids.img.source = img_file_name
            else:
                self.ms.ids.img.source = ""
            self.text_label.text = self.lines[self.line_number]
            self.text_label.scroll_y = 1

    def backward(self, *args):
        if not self.current_article:
            return
        os.chdir(os.path.join(self.working_directory, self.current_article))
        if self.line_number > 0:
            self.line_number = self.line_number - 1
            self.text_label.text = self.lines[self.line_number]
            self.text_label.scroll_y = 1
        elif self.article_part > 0:
            self.article_part = self.article_part - 1
            f = open(self.article_parts[self.article_part], encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            self.line_number = len(self.lines) - 1
            f.close()
            img_file_name = self.article_parts[self.article_part].replace(".txt", "")
            images = [fn for fn in glob.glob(img_file_name + "*") if not fn.endswith("txt")]
            if images:
                img_file_name = images[0]
                self.ms.ids.img.source = img_file_name
            else:
                self.ms.ids.img.source = ""
            self.text_label.text = self.lines[self.line_number]
            self.text_label.scroll_y = 1


    def add_bookmark(self, *args):

        if not self.current_article \
           or self.spinner_articles.text == "Choose article" \
           or not self.article_parts:
            return
        if self.lines[self.line_number] == "__BM__\n":
            return
        os.chdir(os.path.join(self.working_directory, self.current_article))

        # removing old bookmark
        for file in glob.glob("*.txt"):
            f = open(file, "r", encoding='utf-8', errors='ignore')
            lines = f.readlines()
            f.close()
            old_text = "".join(lines)
            if "__BM__\n" in old_text:
                with open(file, "w") as ff:
                    new_text = old_text.replace("__BM__\n", "")
                    ff.write(new_text)

        # making new bookmark
        f = open(self.article_parts[self.article_part], "r", encoding='utf-8', errors='ignore')
        self.lines = f.readlines()
        f.close()

        if self.line_number > 0:
            self.lines.insert(self.line_number - 1, "__BM__\n")
        else:
            self.lines.insert(0, "__BM__\n")

        f = open(self.article_parts[self.article_part], "w")
        new_text = "".join(self.lines)
        f.write(new_text)
        f.close()

        self.line_number = self.lines.index("__BM__\n")
        f = open(self.article_parts[self.article_part], "r", encoding='utf-8', errors='ignore')
        self.lines = f.readlines()
        f.close()

        os.chdir(self.working_directory)
        popup = Popup(title='Bookmark added successfully',
                      size_hint = (None, None), size = (400, 400),
                      auto_dismiss=True)
        popup.open()

    def on_spinner_select(self, spinner, text):
        self.current_article = text
        os.chdir(os.path.join(self.working_directory, self.current_article))
        self.article_parts = []
        for f in glob.glob("*.txt"):
            self.article_parts.append(f)
        self.article_parts.sort()
        self.article_part = 0
        self.lines = []
        self.line_number = 0
        breaker = False
        for idy, article_part in enumerate(self.article_parts):
          f = open(article_part, "r", encoding='utf-8', errors='ignore')
          lines = f.readlines()
          f.close()
          for idx, line in enumerate(lines):
              if line == "__BM__\n": # found bookmark
                  self.line_number = idx
                  self.article_part = idy
                  breaker = True
                  break
          if breaker:
              break

        if self.article_parts:
            f = open(self.article_parts[self.article_part], "r", encoding='utf-8', errors='ignore')
            self.lines = f.readlines()
            f.close()

            self.text_label.text = self.lines[self.line_number]
            img_file_name = self.article_parts[self.article_part].replace(".txt", "")
            images = [fn for fn in glob.glob(img_file_name + "*") if not fn.endswith("txt")]
            if images:
                img_file_name = images[0]
                self.ms.ids.img.source = img_file_name
            else:
                self.ms.ids.img.source = ""
        else:
            self.text_label.text = ""
            self.ms.ids.img.source = ""
            self.lines = []
            self.line_number = 0
        os.chdir(self.working_directory)

    def create_new_article_popup(self, *args):
        p = Urlpup()
        p.open()
        
    def create_new_article(self, url):

        if not "wikiped" in url:
            popup = Popup(title='Not a Wikipedia article',
                          size_hint = (None, None), size = (400, 400),
                          auto_dismiss=True)
            popup.open()
            return
        
        try:
            soup = html2txt.get_soup_from_url(url)
        except:
            popup = Popup(title='No Internet connection or bad URL',
                          size_hint = (None, None), size = (400, 400),
                          auto_dismiss=True)
            popup.open()
            return

        if (not url.startswith("http://")) and (not url.startswith("https://")):
            popup = Popup(title='URL does not start with http:// or https://',
                          size_hint = (None, None), size = (400, 400),
                          auto_dismiss=True)
            popup.open()
            return

        if not self.download_nltk():
            return
        os.chdir(self.data_dir)
        sentences = html2txt.node_to_sentences(soup.find(id = "content"))
        os.chdir(self.working_directory)

        title = url.split("/")[-1]
        language_code = url.split("/")[2][:2]
        title = title[0].upper() + title[1:] + "_" + language_code
        html2txt.save_article(url, title, sentences)
        os.chdir("..")
        
        self.spinner_articles.values = sorted([d for d in os.listdir(self.working_directory) \
                            if os.path.isdir(os.path.join(self.working_directory, d))])
        os.chdir(self.working_directory)
        popup = Popup(title='Article added successfully',
                      size_hint = (None, None), size = (400, 400),
                      auto_dismiss=True)
        popup.open()
        
if __name__ == "__main__":

    Tedegraph().run()

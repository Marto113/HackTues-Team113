from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserListView

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=10)
        file_chooser = FileChooserListView()
        file_chooser.path = "./"
        file_chooser.filters = ["*.png", "*.jpg", "*.jpeg"]
        file_chooser.bind(selection=self.select_image)
        layout.add_widget(file_chooser)
        self.image_preview = Image(allow_stretch=True, size_hint=(1, 1))
        layout.add_widget(self.image_preview)
        return layout

    def select_image(self, file_chooser, selection):
        if selection:
            image_file = selection[0]
            self.image_preview.source = image_file

if __name__ == "__main__":
    MyApp().run()
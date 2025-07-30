from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.lang import Builder
import requests

API_BASE_URL = "http://127.0.0.1:5000"

class LoginScreen(MDScreen):
    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text
        try:
            res = requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})
            if res.status_code == 200:
                user = res.json()
                self.manager.current = "main"
            else:
                self.ids.login_message.text = "Invalid credentials"
        except:
            self.ids.login_message.text = "Server error"

class MainScreen(MDScreen):
    def on_enter(self):
        self.load_inventory()

    def load_inventory(self):
        try:
            res = requests.get(f"{API_BASE_URL}/products")
            if res.status_code == 200:
                product_list = self.ids.inventory_list
                product_list.clear_widgets()
                for p in res.json():
                    item = OneLineAvatarIconListItem(
                        text=f"{p[1]} - Qty: {p[2]} - ₱{p[3]}"
                    )
                    product_list.add_widget(item)
        except:
            pass

class InventoryApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Pink"
        self.theme_cls.theme_style = "Light"
        return Builder.load_file("app.kv")

if __name__ == '__main__':
    InventoryApp().run()

# main.py (MDSnackbar usage fixed)
import sys
import traceback
import requests
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel

API_BASE_URL = "http://127.0.0.1:5000"

class LoginScreen(MDScreen):
    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text
        try:
            res = requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})
            if res.status_code == 200:
                user = res.json()
                app = MDApp.get_running_app()
                app.user_id = user["user_id"]
                app.role = user["role"]
                self.manager.current = "main"
            else:
                self.ids.login_message.text = "Invalid credentials"
        except Exception as e:
            self.ids.login_message.text = "Server error"
            print("Login error:", e)

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
        except Exception as e:
            print("Inventory load error:", e)

class InventoryApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Pink"
        self.theme_cls.theme_style = "Light"
        self.user_id = None
        self.role = None
        return Builder.load_file("app.kv")

    def show_snackbar(self, message):
        snackbar = MDSnackbar()
        snackbar.add_widget(
            MDLabel(
                text=message,
                halign="center",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            )
        )
        snackbar.open()

    def submit_product(self):
        screen = self.root.get_screen("main")
        name = screen.ids.name_field.text
        quantity = screen.ids.qty_field.text
        price = screen.ids.price_field.text
        expiration = screen.ids.exp_field.text

        if not all([name, quantity, price, expiration]):
            self.show_snackbar("All fields are required.")
            return

        try:
            res = requests.post(f"{API_BASE_URL}/add_product", json={
                "name": name,
                "quantity": int(quantity),
                "price": float(price),
                "expiration_date": expiration
            })
            if res.status_code == 200:
                self.show_snackbar("Product added!")
                self.root.get_screen("main").load_inventory()
                screen.ids.name_field.text = ""
                screen.ids.qty_field.text = ""
                screen.ids.price_field.text = ""
                screen.ids.exp_field.text = ""
            else:
                self.show_snackbar("Failed to add product.")
        except Exception as e:
            print("Add error:", e)
            self.show_snackbar("Error during product addition")

    def delete_product_from_manage(self):
        screen = self.root.get_screen("main")
        name = screen.ids.delete_field.text

        if not name:
            self.show_snackbar("Enter a product name to delete.")
            return

        try:
            res = requests.post(f"{API_BASE_URL}/get_product_by_name", json={"name": name})
            if res.status_code == 200:
                product_id = res.json()["id"]
                del_res = requests.post(f"{API_BASE_URL}/delete_product", json={"product_id": product_id})
                if del_res.status_code == 200:
                    self.show_snackbar("Product deleted")
                    screen.ids.delete_field.text = ""
                    self.root.get_screen("main").load_inventory()
                else:
                    self.show_snackbar("Delete failed")
            else:
                self.show_snackbar("Product not found")
        except Exception as e:
            print("Delete product error:", e)
            self.show_snackbar("Error deleting product")

if __name__ == '__main__':
    try:
        InventoryApp().run()
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")

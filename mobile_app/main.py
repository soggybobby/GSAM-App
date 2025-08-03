# main.py (updated with separate Add/Delete product screens and dropdown navigation)
import sys
import traceback
import requests
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineListItem
from functools import partial

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

    def submit_transaction(self):
        product_field = self.ids.product_field
        transaction_type_field = self.ids.transaction_type_field
        qty_field = self.ids.transaction_qty
        error_label = self.ids.transaction_error

        product = product_field.text
        transaction_type = transaction_type_field.text
        quantity = qty_field.text

        # Reset error message
        error_label.text = ""

        if not product or product == "Select Product":
            error_label.text = "Please select a product."
            return
        if transaction_type not in ["Stock In", "Stock Out"]:
            error_label.text = "Please select a transaction type."
            return
        if not quantity.isdigit() or int(quantity) <= 0:
            error_label.text = "Please enter a valid quantity."
            return

        # ✅ Only try to fetch product_id if all fields are valid
        app = MDApp.get_running_app()
        product_id = app.get_product_id_by_name(product)

        if not product_id:
            error_label.text = "Product not found."
            return

        try:
            res = requests.post(f"{API_BASE_URL}/stocklog", json={
                "product_id": product_id,
                "type": "in" if transaction_type == "Stock In" else "out",
                "quantity": int(quantity),
                "user_id": app.user_id
            })
            if res.status_code == 200:
                product_field.text = ""
                transaction_type_field.text = ""
                qty_field.text = ""
                error_label.text = "Transaction submitted!"
                error_label.theme_text_color = "Custom"
                error_label.text_color = (0, 0.5, 0, 1)  # green
            else:
                error_label.text = "Failed to submit transaction."
        except Exception as e:
            print("Transaction error:", e)
            error_label.text = "Unexpected error during transaction."


    def on_enter(self):
        self.load_inventory()
        self.populate_transaction_products()

    def populate_transaction_products(self):
        pass

class AddProductScreen(MDScreen):
    def add_product(self):
        name = self.ids.name_field.text
        quantity = self.ids.qty_field.text
        price = self.ids.price_field.text
        expiration = self.ids.exp_field.text

        # Reset warnings
        self.ids.name_warn.text = ""
        self.ids.qty_warn.text = ""
        self.ids.price_warn.text = ""
        self.ids.exp_warn.text = ""

        error = False
        if not name:
            self.ids.name_warn.text = "Required"
            error = True
        if not quantity:
            self.ids.qty_warn.text = "Required"
            error = True
        if not price:
            self.ids.price_warn.text = "Required"
            error = True
        if not expiration:
            self.ids.exp_warn.text = "Required"
            error = True

        if error:
            return

        try:
            res = requests.post(f"{API_BASE_URL}/add_product", json={
                "name": name,
                "quantity": int(quantity),
                "price": float(price),
                "expiration_date": expiration
            })
            if res.status_code == 200:
                self.dialog_popup("Product added!")
                self.manager.get_screen("main").load_inventory()
                self.ids.name_field.text = ""
                self.ids.qty_field.text = ""
                self.ids.price_field.text = ""
                self.ids.exp_field.text = ""
            else:
                self.dialog_popup("Failed to add product")
        except Exception as e:
            print("Add product error:", e)
            self.dialog_popup("Error adding product")

    def dialog_popup(self, text):
        MDDialog(title="Info", text=text).open()

class DeleteProductScreen(MDScreen):
    def delete_product(self):
        name = self.ids.delete_field.text
        if not name:
            self.dialog_popup("Enter a product name to delete.")
            return

        try:
            res = requests.post(f"{API_BASE_URL}/get_product_by_name", json={"name": name})
            if res.status_code == 200:
                product_id = res.json()["id"]
                del_res = requests.post(f"{API_BASE_URL}/delete_product", json={"product_id": product_id})
                if del_res.status_code == 200:
                    self.dialog_popup("Product deleted")
                    self.ids.delete_field.text = ""
                    self.manager.get_screen("main").load_inventory()
                else:
                    self.dialog_popup("Delete failed")
            else:
                self.dialog_popup("Product not found")
        except Exception as e:
            print("Delete product error:", e)
            self.dialog_popup("Error deleting product")

    def dialog_popup(self, text):
        MDDialog(title="Info", text=text).open()

class InventoryApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Pink"
        self.theme_cls.theme_style = "Light"
        self.user_id = None
        self.role = None
        self.product_menu = None
        return Builder.load_file("app.kv")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.product_menu = None 

    def submit_product(self):
        screen = self.root.get_screen("add_product")
        name = screen.ids.name_field.text
        quantity = screen.ids.qty_field.text
        price = screen.ids.price_field.text
        expiration = screen.ids.exp_field.text

        # Reset previous warnings
        screen.ids.name_warn.text = ""
        screen.ids.qty_warn.text = ""
        screen.ids.price_warn.text = ""
        screen.ids.exp_warn.text = ""

        error = False
        if not name:
            screen.ids.name_warn.text = "Product name is required"
            error = True
        if not quantity:
            screen.ids.qty_warn.text = "Quantity is required"
            error = True
        if not price:
            screen.ids.price_warn.text = "Price is required"
            error = True
        if not expiration:
            screen.ids.exp_warn.text = "Expiration date is required"
            error = True

        if error:
            return

        try:
            res = requests.post("http://127.0.0.1:5000/add_product", json={
                "name": name,
                "quantity": int(quantity),
                "price": float(price),
                "expiration_date": expiration
            })
            if res.status_code == 200:
                self.root.get_screen("main").load_inventory()
                screen.ids.name_field.text = ""
                screen.ids.qty_field.text = ""
                screen.ids.price_field.text = ""
                screen.ids.exp_field.text = ""
                self.show_popup("Success", "Product added.")
            else:
                self.show_popup("Failed", "Could not add product.")
        except Exception as e:
            print("Error:", e)
            self.show_popup("Error", "Server error.")

    def show_popup(self, title, text):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK", on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()

    def delete_product_from_manage(self):
        screen = self.root.get_screen("delete_product")
        name = screen.ids.delete_field.text

        # Clear previous warning
        screen.ids.delete_warn.text = ""

        if not name:
            screen.ids.delete_warn.text = "Product name is required."
            return

        try:
            res = requests.post(f"{API_BASE_URL}/get_product_by_name", json={"name": name})
            if res.status_code == 200:
                product_id = res.json()["id"]
                del_res = requests.post(f"{API_BASE_URL}/delete_product", json={"product_id": product_id})
                if del_res.status_code == 200:
                    screen.ids.delete_field.text = ""
                    screen.ids.delete_warn.text = "Product deleted successfully."
                    self.root.get_screen("main").load_inventory()
                else:
                    screen.ids.delete_warn.text = "Failed to delete product."
            else:
                screen.ids.delete_warn.text = "Product not found."
        except Exception as e:
            print("Delete product error:", e)
            screen.ids.delete_warn.text = "Error occurred during deletion."

    def reset_add_product_screen(self):
        screen = self.root.get_screen("add_product")
        screen.ids.name_field.text = ""
        screen.ids.qty_field.text = ""
        screen.ids.price_field.text = ""
        screen.ids.exp_field.text = ""
        screen.ids.name_warn.text = ""
        screen.ids.qty_warn.text = ""
        screen.ids.price_warn.text = ""
        screen.ids.exp_warn.text = ""

    def reset_delete_product_screen(self):
        screen = self.root.get_screen("delete_product")
        screen.ids.delete_field.text = ""
        screen.ids.delete_warn.text = ""

    def open_transaction_type_menu(self):
        from kivymd.uix.menu import MDDropdownMenu

        menu_items = [
            {
                "text": "Stock In",
                "on_release": lambda x="Stock In": self.set_transaction_type(x),
            },
            {
                "text": "Stock Out",
                "on_release": lambda x="Stock Out": self.set_transaction_type(x),
            },
        ]

        self.transaction_menu = MDDropdownMenu(
            caller=self.root.get_screen("main").ids.transaction_type_field,
            items=menu_items,
            width_mult=4,
        )
        self.transaction_menu.open()

    def set_transaction_type(self, selected_type):
        self.root.get_screen("main").ids.transaction_type_field.text = selected_type
        self.transaction_menu.dismiss()

    def update_product_suggestions(self, text):
        screen = self.root.get_screen("main")
        product_field = screen.ids.product_field

        if len(text.strip()) < 1:
            if self.product_menu:
                self.product_menu.dismiss()
            return

        try:
            res = requests.post(f"{API_BASE_URL}/search_products", json={"query": text})
            suggestions = res.json() if res.status_code == 200 else []
        except Exception as e:
            print("Search error:", e)
            suggestions = []

        if self.product_menu:
            self.product_menu.dismiss()

        if not suggestions:
            return

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": p,
                "on_release": lambda x=p: self.set_product(x),
            } for p in suggestions
        ]

        self.product_menu = MDDropdownMenu(
            caller=product_field,
            items=menu_items,
            width_mult=4,
        )
        self.product_menu.open()

    def set_product(self, product_name):
        screen = self.root.get_screen("main")
        screen.ids.product_field.text = product_name
        if self.product_menu:
            self.product_menu.dismiss()

    def get_product_id_by_name(self, name):
        try:
            res = requests.post(f"{API_BASE_URL}/get_product_by_name", json={"name": name})
            if res.status_code == 200:
                return res.json()["id"]
        except Exception as e:
            print("Error getting product ID:", e)
        return None

    def show_dialog(self, message):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.label import MDLabel

        dialog = MDDialog(
            title="Notice",
            type="custom",
            content_cls=MDLabel(text=message, halign="center"),
        )
        dialog.open()



if __name__ == '__main__':
    try:
        InventoryApp().run()
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")

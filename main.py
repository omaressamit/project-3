from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
import cv2
import pyzbar.pyzbar as pyzbar
import pyodbc
from kivymd.font_definitions import theme_font_styles
from kivy.core.text import LabelBase
import bidi.algorithm
import arabic_reshaper
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

class ScanPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_text_reference = None  # Reference to the server_text from connect_page screen

        arabic_font_path = "Arabic.ttf"
        LabelBase.register(name="arabic", fn_regular=arabic_font_path)
        self.output_label = MDTextField(multiline=False, write_tab=False, pos_hint={'center_x': 0.5, 'center_y': 0.8}, size_hint=(0.7, 0.3), halign='center', font_size=23, hint_text="Barcode")
        self.name_label = MDTextField(multiline=False, write_tab=False, pos_hint={'center_x': 0.5, 'center_y': 0.6}, size_hint=(0.7, 0.3), halign='center', font_size=23, font_name="arabic", hint_text="Name")
        self.price_label = MDTextField(multiline=False, write_tab=False, pos_hint={'center_x': 0.5, 'center_y': 0.4}, size_hint=(0.7, 0.3), halign='center', font_size=23, hint_text="Price")
        self.manual_btn = MDRectangleFlatButton(text='Manual Input', pos_hint={'center_x': 0.5, 'center_y': 0.11}, font_size=33, on_press=self.open_manual_input_dialog, theme_text_color="Custom",
                                                      text_color=(1, 0, 0, 1))
        self.add_widget(self.manual_btn)

    def update_name_label(self, arabic_text):
        reshaped_text = arabic_reshaper.reshape(arabic_text)
        bidi_text = bidi.algorithm.get_display(reshaped_text)
        self.name_label.text = bidi_text

    def open_manual_input_dialog(self, instance):
        manual_input_dialog = MDDialog(title="Manual Input", size_hint=(0.8, 0.5), text="Enter barcode data:", type="custom", content_cls=ManualInputDialogContent(self))
        manual_input_dialog.open()

    def process_manual_input(self, barcode_data):
        if self.server_text_reference and hasattr(self.server_text_reference, 'text'):
            server_name = "10.174." + self.server_text_reference.text + ".5"
        else:
            print("Error: server_text_reference is not set or does not have a 'text' attribute.")
            return

        # Rest of your code remains unchanged
        self.output_label.text = f"{barcode_data}"
        try:
            driver = '{SQL Server}'
            database = 'retail'
            username = 'gmlogins'
            password = 'retgomladb'
            DateTimeAllowed = 'Yes'

            # Construct the connection string
            connection_string = f'DRIVER={driver};SERVER={server_name};DATABASE={database};UID={username};PWD={password};{DateTimeAllowed}'
            # Attempt to connect to the database
            conn = pyodbc.connect(connection_string)

            cursor = conn.cursor()
            query = f"SELECT [a_name], [sell_price], [discountvalue] FROM [pos_items] WHERE [barcode] = '{barcode_data}'"
            cursor.execute(query)
            row = cursor.fetchone()

            if row:
                a_name = row.a_name
                sell_price = row.sell_price
                discount_value = row.discountvalue  # Retrieve discount value from the database

                self.update_name_label(a_name)

                if discount_value is not None:
                    # If discount_value is not NULL, subtract it from sell_price
                    discounted_price = sell_price - discount_value
                    self.price_label.text = f"{discounted_price} LE"
                else:
                    self.price_label.text = f"{sell_price} LE"  # Display the original sell_price
            else:
                self.name_label.text = "Product not found"
                self.price_label.text = ""

        except pyodbc.OperationalError as e:
            print(f"Error connecting to the database: {e}")



class ManualInputDialogContent(MDBoxLayout):
    def __init__(self, scan_page, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.width = 200
        self.height = 100
        self.scan_page = scan_page
        # Create text input for manual input
        self.manual_input_text = MDTextField(multiline=False, write_tab=False, halign='center', font_size=23, hint_text="Barcode")
        self.add_widget(self.manual_input_text)
        # Create OK button to submit manual input
        self.ok_btn = MDRectangleFlatButton(text='OK', font_size=20, on_press=self.submit_manual_input)
        self.add_widget(self.ok_btn)

    def submit_manual_input(self, instance):
        barcode_data = self.manual_input_text.text
        self.scan_page.process_manual_input(barcode_data)
        # Close the dialog after processing the manual input
        self.parent.parent.parent.dismiss()

class PriceApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.screen_manager = ScreenManager()
        self.screen = Screen(name='connect_page')
        self.scan_page = ScanPage(name='scan_page')

        gomla_label = MDLabel(text="Gomla Market", halign='center', pos_hint={'center_x': 0.5, 'center_y': 0.8}, theme_text_color="Custom", text_color=(1, 0.549, 0, 1), font_style="H3")
        self.screen.add_widget(gomla_label)
        omar_label = MDLabel(text="OMAR ESSAM", halign='center', pos_hint={'center_x': 0.5, 'center_y': 0.1}, theme_text_color="Custom", text_color=(1, 0, 0, 1), font_style="H4")
        self.screen.add_widget(omar_label)

        self.connect_btn = MDRectangleFlatButton(text='CONNECT', pos_hint={'center_x': 0.5, 'center_y': 0.4}, font_size=40, on_press=self.connect_to_db)
        self.screen.add_widget(self.connect_btn)

        self.server_text = MDTextField(multiline=False, write_tab=False, hint_text="Branch Subnet", pos_hint={'center_x': 0.5, 'center_y': 0.6}, size_hint=(0.7, 1), halign='center', icon_right="android", font_size=22,)
        self.screen.add_widget(self.server_text)

        self.scan_btn = MDRectangleFlatButton(text='Scan Now', pos_hint={'center_x': 0.5, 'center_y': 0.25}, font_size=40, on_press=self.start_scanning)
        self.scan_page.add_widget(self.scan_btn)
        self.scan_page.add_widget(self.scan_page.name_label)
        self.scan_page.add_widget(self.scan_page.output_label)
        self.scan_page.add_widget(self.scan_page.price_label)
        self.scan_page.server_text_reference = self.server_text

        self.screen_manager.add_widget(self.screen)
        self.screen_manager.add_widget(self.scan_page)

        # Create error dialog
        self.error_dialog = MDDialog(title="Error", text="Failed to connect to the database. Please check your connection settings.", buttons=[MDRectangleFlatButton(text="OK", on_release=self.dismiss_error_dialog)])
        return self.screen_manager

    def connect_to_db(self, instance):
        server_name = "10.174." + self.server_text.text + ".5"
        try:
            driver = '{SQL Server}'
            database = 'retail'
            username = 'gmlogins'
            password = 'retgomladb'
            DateTimeAllowed = 'Yes'
            conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server_name+';DATABASE='+database+';UID='+username+';PWD='+ password + ';'+ DateTimeAllowed)
            self.screen_manager.current = 'scan_page'
        except Exception as e:
            self.error_dialog.open()

    def start_scanning(self, instance):
        cap = cv2.VideoCapture(0)

        server_name = "10.174." + self.server_text.text + ".5" 
        driver = '{SQL Server}'
        database = 'retail'
        username = 'gmlogins'
        password = 'retgomladb'
        DateTimeAllowed = 'Yes'
        connection_string = f'DRIVER={driver};SERVER={server_name};DATABASE={database};UID={username};PWD={password};{DateTimeAllowed}'

        try:
            conn = pyodbc.connect(connection_string)

            while True:
                ret, frame = cap.read()
                if frame is None:
                    break
                barcodes = pyzbar.decode(frame)
                for barcode in barcodes:
                    barcode_data = barcode.data.decode("utf-8")
                    print(f"Decoded Barcode: {barcode_data}")

                    cursor = conn.cursor()
                    query = f"SELECT [a_name], [sell_price], [discountvalue] FROM [pos_items] WHERE [barcode] = '{barcode_data}'"
                    cursor.execute(query)
                    row = cursor.fetchone()

                    if row:
                        a_name = row.a_name
                        sell_price = row.sell_price
                        discount_value = row.discountvalue  # Retrieve discount value from the database

                        self.scan_page.output_label.text = f"{barcode_data}"
                        self.scan_page.update_name_label(a_name)

                        if discount_value is not None:
                            # If discount_value is not NULL, subtract it from sell_price
                            discounted_price = sell_price - discount_value
                            self.scan_page.price_label.text = f"{discounted_price} LE"
                        else:
                            self.scan_page.price_label.text = f"{sell_price} LE"  # Display the original sell_price
                    else:
                        self.scan_page.output_label.text = f"{barcode_data}"
                        self.scan_page.name_label.text = "Product not found"
                        self.scan_page.price_label.text = ""

                    cap.release()
                    cv2.destroyAllWindows()
                    return  # Exit the method and close the camera window

                cv2.imshow("Barcode Scanner", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except pyodbc.OperationalError as e:
            print(f"Error connecting to the database: {e}")

    def dismiss_error_dialog(self, instance):
        self.error_dialog.dismiss()

PriceApp().run()

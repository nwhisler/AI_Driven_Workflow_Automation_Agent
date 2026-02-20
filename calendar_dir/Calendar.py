import tkinter as tk
import os
import json
from tkinter import scrolledtext
from datetime import datetime
from pathlib import Path

CALENDAR_DIR = Path(__file__).resolve().parent
CALENDAR_PATH = CALENDAR_DIR / "calendar.json"
EVENT_COUNTER = 0

class Calendar_App:

    #Initializes a list of values that are extracted from the GUI.

    def __init__(self):

        self.values = []

    #Creates the add event instance of the calendar with the date and event box.

    def create_calendar(self):

        root = tk.Tk()
        root.title("Add Event")
        root.geometry("1000x600")

        data_label = tk.Label(root, text="Date:")
        data_label.grid(row=0, column=0)
        data_entry = tk.Entry(root, width=50)
        data_entry.grid(row=0, column=1)

        event_label = tk.Label(root, text="Event:")
        event_label.grid(row=1, column=0)
        event_text = tk.Text(root, height=10, width=50)
        event_text.grid(row=1, column=1)

        return data_entry, event_text, root

    #Adds an event to the calendar stored in json if generated from another app.

    def adding_data(self, path, current_data):

            with open(str(path), "r") as fh:
                json_object = json.load(fh)
            if not isinstance(json_object, dict):
                json_object = {}
            data = json_object.get("data", None)
            if data is None:
                data = []
            data.append(current_data)

            with open(str(path),"w") as fh:
                json.dump({"data":data}, fh)

    #Adds events to calendar.json if generated through the app.

    def file_handling(self, path, current_data=None):

        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            path.write_text("{}", encoding="utf-8")
        if current_data is None:
            current_data = {"Date":self.values[0],"Event":self.values[1]}
        self.adding_data(path, current_data)

    #Extracts the values from the GUI.

    def handle_event_data(self, entries):

        for idx, entry in enumerate(entries):
            if idx == len(entries) - 1:
                self.values.append(entry.get("1.0", "end-1c"))
            else:
                self.values.append(entry.get())

        self.file_handling(CALENDAR_PATH)

    #Hides the root window.

    def hide_window(self, root):

        root.withdraw()

    #Calls multiple methods when the send button is pressed.

    def button_wrapper(self, entries, root):

        self.handle_event_data(entries)
        self.hide_window(root)

    #Adds an event through the GUI

    def add_event(self):

        data_entry, event_text, root = self.create_calendar()
        entries = [data_entry, event_text]
        create_button = tk.Button(root, text="Create Event", command=lambda: self.button_wrapper(entries, root))
        create_button.grid(row=3, column=1)
        self.values = []

    #Extracts data list of dates and events stored in dictionaries.

    def data_extraction(self, path):

        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            path.write_text("{}", encoding="utf-8")
            data = []
        else:
            with open(str(path), "r") as fh:
                json_object = json.load(fh)
            if not isinstance(json_object, dict):
                json_object = {}
            data = json_object.get("data", [])
            if not isinstance(data, list):
                data = []

        return data

    #Destroys root window and closes it.
    
    def end_root_window(self, root):

        root.quit()
        root.destroy()

    #Displays the event associated with the date hyperlink.

    def display_event(self, root, event, data):

        new_window = tk.Toplevel(root)
        new_window.title(f"Event")
        new_window.geometry("400x300")

        text_area = scrolledtext.ScrolledText(new_window, wrap=tk.WORD, padx=10, pady=10)
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, data)
        text_area.config(state=tk.DISABLED)

    #Adds a date hyperlink with an event attached.

    def add_link(self, root, text_widget, anchor_text, data):
    
        start_index = text_widget.index(tk.END + "-1c")
        text_widget.insert(tk.END, anchor_text)
        end_index = text_widget.index(tk.END + "-1c")

        tag_name = f"link_{data}"

        text_widget.tag_add(tag_name, start_index, end_index)
        text_widget.tag_config(tag_name, foreground="blue", underline=True)
        text_widget.tag_bind(tag_name, "<Button-1>", lambda event: self.display_event(root, event, data))

    #Displays the calendar and all links while opening events when links are clicked on.

    def display_calendar(self):

        global EVENT_COUNTER
        data = self.data_extraction(CALENDAR_PATH)

        root = tk.Tk()
        root.protocol("WM_DELETE_WINDOW", lambda: self.end_root_window(root))
        year = datetime.now().year
        root.title("{year} Calendar")
        root.geometry("1000x600")

        main_text = tk.Text(root, wrap=tk.WORD, padx=10, pady=10)
        main_text.pack(expand=True, fill=tk.BOTH)
        main_text.insert(tk.END, "Click the links below to view the email contents:\n\n")

        for idx, data in enumerate(data):

            date = data["Date"]
            event = data["Event"]

            self.add_link(root, main_text, date + f"-Event:{EVENT_COUNTER}", event)
            main_text.insert(tk.END, "\n")
            EVENT_COUNTER += 1

        main_text.config(state=tk.DISABLED)

        root.mainloop()

if __name__ == "__main__":

    calendar_app = Calendar_App()

    #Inputs user action to be performed.

    action = ""

    while True:
        
        if action == "q" or action == "Q":
            break
        
        action = input("(Enter q to exit at anytime) To create an event enter create and to check the calendar enter check: ")

        if action == "create" or action == "Create":

            calendar_app.add_event()

        elif action == "check" or action == "Check":

            calendar_app.display_calendar()
import tkinter as tk
import asyncio
import sys
import os
import json
from aiosmtpd.controller import Controller
from smtplib import SMTP
from tkinter import scrolledtext
from pathlib import Path

EMAIL_DIR = Path(__file__).resolve().parent
EMAIL_PATH = EMAIL_DIR / "email.json"

#Handles the data sent over the establisehed session. This data is extracted and saved as a json.

class SMTP_Handler:

    async def handle_DATA(self, server, session, envelope):

        mail_from = envelope.mail_from
        mail_to = envelope.rcpt_tos[0]
        message = envelope.content.decode("utf-8")
        data = ""

        if EMAIL_PATH.exists() and EMAIL_PATH.is_file():
            with open(str(EMAIL_PATH), "r") as fh:
                json_object = json.load(fh)
            if not isinstance(json_object, dict):
                json_object = {}
            data = json_object.get("data")
            if not isinstance(data, list):
                data = []
            data.append({"From":mail_from, "To":mail_to, "Message":message})
            
            with open(str(EMAIL_PATH), "w") as fh:
                json.dump({"data":data}, fh)
        else:
            data = {"data":[{"From":mail_from, "To":mail_to, "Message":message}]}
            with open(str(EMAIL_PATH), "w") as fh:
                json.dump(data, fh)
        
        return '250 OK'

class Email_APP:

    #Initializes a list that will extract the values entered into the GUI.

    def __init__(self):

        self.values = []

    #Sends the email over the established session.
    
    def send_mail(self,hostname, port, message, mail_from, mail_to):

        client = SMTP(hostname, port)
        client.sendmail(mail_from, mail_to, message)

    #Extracts all emails and saves them in a list of dictionaries

    def get_mail_list(self, path):

        mail_list = []
        
        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            path.write_text("{}", encoding="utf-8")
        with open(str(path), "r") as fh:
            json_object = json.load(fh)
        if not isinstance(json_object, dict):
            json_object = {}
        data = json_object.get("data")
        if not isinstance(data, list):
            data = []

        for entry in data:
            if isinstance(entry, dict):
                mail_from = entry.get("From")
                mail_from = mail_from.strip() if isinstance(mail_from, str) else ""
                if not mail_from:
                    continue
                mail_to = entry.get("To")
                mail_to = mail_to.strip() if isinstance(mail_to, str) else ""
                if not mail_to:
                    continue
                mail_message = entry.get("Message")
                mail_message = mail_message.strip() if isinstance(mail_message, str) else ""
                if not mail_message:
                    continue
                mail_list.append({"From":mail_from, "To":mail_to, "Message":mail_message})

        return mail_list

    #Generates the GUI for the actual stored message attached to the from and to link.

    def get_mail(self,root, event, mail_data):

        mail_from = mail_data["From"]
        mail_message = mail_data["Message"]

        new_window = tk.Toplevel(root)
        new_window.title(f"From {mail_from}")
        new_window.geometry("400x300")

        text_area = scrolledtext.ScrolledText(new_window, wrap=tk.WORD, padx=10, pady=10)
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, mail_message)
        text_area.config(state=tk.DISABLED)

    #Adds a hyperlink to the inbox in the GUI.

    def add_link(self, root, text_widget, anchor_text, mail_data):
    
        start_index = text_widget.index(tk.END + "-1c")
        text_widget.insert(tk.END, anchor_text)
        end_index = text_widget.index(tk.END + "-1c")

        tag_name = f"link_{mail_data}"

        text_widget.tag_add(tag_name, start_index, end_index)

        text_widget.tag_config(tag_name, foreground="blue", underline=True)

        text_widget.tag_bind(tag_name, "<Button-1>", lambda event: self.get_mail(root, event, mail_data))

    #Recieves user input data for sending an email if done through the command prompt.

    def from_to_message(self):

        From = input("From: ")
        To = input("To: ")
        Message = input("Message: ")

        return From, To, Message

    #Destroys root window and closes it.

    def end_root_window(self, root):

        root.quit()
        root.destroy()

    #Generates inbox, adds links, and open messagees when links are clicked on.

    def check_inbox(self):

        mail_list = self.get_mail_list(EMAIL_PATH)

        root = tk.Tk()
        root.protocol("WM_DELETE_WINDOW", lambda: self.end_root_window(root))
        root.title("Inbox")
        root.geometry("500x200")

        main_text = tk.Text(root, wrap=tk.WORD, padx=10, pady=10)
        main_text.pack(expand=True, fill=tk.BOTH)

        main_text.insert(tk.END, "Click the links below to view the email contents:\n\n")

        for idx, data in enumerate(mail_list):

            mail_from = data["From"]
            mail_to = data["To"]

            self.add_link(root, main_text, "From: " + mail_from + " To: " + mail_to, data)
            main_text.insert(tk.END, "\n")

        main_text.config(state=tk.DISABLED)

        root.mainloop()

        return root

    #Extracts values input into the GUI.

    def get_entries(self,entries):

        for idx, entry in enumerate(entries):

            if idx == len(entries) - 1:
                self.values.append(entry.get("1.0", "end-1c"))
            else:
                self.values.append(entry.get())

    #Generates the From, To, and Message boxes in the GUI.

    def inbox_grid(self):

        root = tk.Tk()
        root.title("Python Email Client")
        root.geometry("1000x600")    

        to_label = tk.Label(root, text="To:")
        to_label.grid(row=0, column=0)
        to_entry = tk.Entry(root, width=50)
        to_entry.grid(row=0, column=1)

        from_label = tk.Label(root, text="From:")
        from_label.grid(row=1, column=0)
        from_entry = tk.Entry(root, width=50)
        from_entry.grid(row=1, column=1)

        body_label = tk.Label(root, text="Message:")
        body_label.grid(row=2, column=0)
        body_text = tk.Text(root, height=10, width=50)
        body_text.grid(row=2, column=1)

        return to_entry, from_entry, body_text, root

    #Calls multplie functions when the send button is pressed.

    def button_wrapper(self, entries, root, hostname, port):

        self.get_entries(entries)
        self.send_mail(hostname, port, self.values[2], self.values[1], self.values[0])
        root.destroy()

    #Hides the root window.

    def hide_window(self, root):

        root.withdraw()

    #Generates the send button and sends the email.

    def send(self, hostname, port):

        to_entry, from_entry, body_text, root = self.inbox_grid()

        entries = [to_entry, from_entry, body_text]

        send_button = tk.Button(root, text="Send Email", command=lambda: self.button_wrapper(entries, root, hostname, port))
        send_button.grid(row=3, column=1)
        root.mainloop()
        self.values = []


if __name__ == "__main__":

    #Instantiates a controller instance with specified hostname and port number. Then it starts the session.

    controller = Controller(SMTP_Handler(), hostname='127.0.0.1', port=8025, ready_timeout=5.0)
    controller.start()

    email_app = Email_APP()

    #Inputs the action desired by the user.
    
    action = ""

    while True:
        
        if action == "q" or action == "Q":
            break
        
        action = input("(Enter q to exit at anytime) Would you like to send an email or check inbox? ")

        if action == "send" or action == "Send":

            _ = email_app.send(controller.hostname, controller.port)

        elif action == "check" or action == "Check":

            email_app.check_inbox()


    
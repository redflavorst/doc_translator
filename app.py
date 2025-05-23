import webview
from server import app


def open_file_dialog(self=None):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("All supported", "*.pdf *.doc *.docx *.txt *.html"),
            ("PDF files", "*.pdf"),
            ("Word files", "*.doc *.docx"),
            ("Text files", "*.txt"),
            ("HTML files", "*.html"),
        ]
    )
    root.destroy()
    return file_path


def open_folder_dialog(self=None):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory()
    root.destroy()
    return folder


def create_window():
    api = type('Api', (), {'open_file_dialog': open_file_dialog, 'open_folder_dialog': open_folder_dialog})()
    webview.create_window('Doc Translator', app, width=1200, height=800, js_api=api)
    webview.start()


if __name__ == '__main__':
    create_window()

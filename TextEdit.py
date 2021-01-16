#!/usr/bin/python3
# -*- coding: utf-8 -*-

### created in January 2021 by Axel Schneider
### https://github.com/Axel-Erfurt/XTINF
### Credits: Florian Heinle for undo / redo
### https://github.com/fheinle/undobuffer

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version('Keybinder', '3.0')
from gi.repository import Gtk, Gdk, Keybinder, Pango
import sys
from os import path
import warnings
import undobuffer

warnings.filterwarnings("ignore")

class MyWindow(Gtk.Window):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__()

    def main(self, argv):
        
        self.current_file = ""
        self.current_filename = ""
        self.is_changed = False
        builder = Gtk.Builder()
        builder.add_from_file("ui.glade")

        screen = Gdk.Screen.get_default()    
        self.screenwidth = screen.get_width ()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('ui.css')

        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider,
          Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
          
        self.win = builder.get_object("window")
        
        self.q_icon = builder.get_object("question_icon")
        
        self.btn_save = builder.get_object("btn_save")
        self.btn_save.connect('clicked', self.save_file)
        self.btn_save.set_relief(Gtk.ReliefStyle.NONE)
        
        self.btn_save_as = builder.get_object("btn_save_as")
        self.btn_save_as.connect('clicked', self.on_save_file)
        self.btn_save_as.set_relief(Gtk.ReliefStyle.NONE)

        self.btn_new = builder.get_object("btn_new")
        self.btn_new.connect('clicked', self.on_new_file)
        self.btn_new.set_relief(Gtk.ReliefStyle.NONE)
        
        self.btn_open = builder.get_object("btn_open")
        self.btn_open.connect('clicked', self.on_open)
        self.btn_open.set_relief(Gtk.ReliefStyle.NONE)
        
        self.editor = builder.get_object("editor")
        self.editor.set_accepts_tab(True)
        tabs = Pango.TabArray(1, True)
        tabs.set_tab(0, Pango.TabAlign.LEFT, 16)
        self.editor.set_tabs(tabs)
        
        self.buffer = undobuffer.UndoableBuffer()
        self.buffer.connect('changed', self.is_modified)
        self.editor.set_buffer(self.buffer)
        
        self.findbox = builder.get_object("findbox")
        
        self.searchbar = builder.get_object("searchbar")
        self.searchbar.connect("search_changed", self.on_search_changed)
        
        self.replacebar = builder.get_object("replacebar")
        
        self.btn_show_find = builder.get_object("btn_show_find")
        self.btn_show_find.connect('clicked', self.toggle_findbox)
        self.btn_show_find.set_relief(Gtk.ReliefStyle.NONE)
        
        self.btn_replace = builder.get_object("btn_replace")
        self.btn_replace.connect('clicked', self.replace_one)
        self.btn_replace.set_relief(Gtk.ReliefStyle.NONE)


        self.btn_replace_all = builder.get_object("btn_replace_all")
        self.btn_replace_all.connect('clicked', self.replace_all)
        self.btn_replace_all.set_relief(Gtk.ReliefStyle.NONE)
        
        self.headerbar = builder.get_object("headerbar")
        
        self.status_label = builder.get_object("status_label")
        
        self.file_filter = Gtk.FileFilter()
        self.file_filter.set_name("Text Files")
        pattern = ["*.txt", "*.py", "*.c", "*.h", "*.cpp", "*.csv"]
        for p in pattern:
            self.file_filter.add_pattern(p)
        
        self.win.connect("delete-event", self.on_close)
        self.win.resize(800, 800)
        self.win.move(0, 0)
        self.win.show_all()
        ### focus on editor
        self.editor.grab_focus()
        self.findbox.set_visible(False)
        
        ### shortcuts
        Keybinder.init()
        Keybinder.set_use_cooked_accelerators(False)
        Keybinder.bind("<Ctrl>F", self.toggle_findbox)
        Keybinder.bind("<Ctrl>S", self.save_file)
        Keybinder.bind("<Ctrl>O", self.on_open)
        Keybinder.bind("<Ctrl>N", self.on_new_file)
        Keybinder.bind("<Ctrl><Shift>S", self.on_save_file)
        Keybinder.bind("<Ctrl>Z", self.buffer.undo)
        Keybinder.bind("<Ctrl><Shift>Z", self.buffer.redo)
        
        ### tags for search color
        self.tag_found = self.buffer.create_tag("found", background="#edd400")

        ### load sys.argv file
        if len(sys.argv) > 1:
            myfile = sys.argv[1]
            with open(myfile, 'r') as f:
                data = f.read()
                self.buffer.set_text(data)
                self.editor.set_buffer(self.buffer)
                self.current_file = myfile
                f.close()
                self.is_changed = False
                print("modified", self.is_changed)
                self.headerbar.set_subtitle(myfile)
                self.status_label.set_text(f"'{myfile}' loaded")
        else:
            self.status_label.set_text("Welcome to TextEdit")
        Gtk.main() 
        
    ### close window
    def on_close(self, *args):
        print(f"{self.current_file} changed: {self.is_changed}")
        if self.is_changed:
            if self.maybe_saved():
                Gtk.main_quit()
        else:
            Gtk.main_quit()
        
    ### get editor text
    def get_buffer(self):
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        text = self.buffer.get_text(start_iter, end_iter, True) 
        return text
    
    ### replace one  
    def replace_one(self, *args):
        if len(self.searchbar.get_text()) > 0:
            print("replace_one")
            search_text = self.searchbar.get_text()
            replace_text = self.replacebar.get_text()
            start_iter = self.buffer.get_start_iter()
            end_iter = self.buffer.get_end_iter()
            found = start_iter.forward_search(search_text, Gtk.TextSearchFlags(1), end_iter)
            if found:
                match_start,match_end = found
                self.buffer.select_range(match_start,match_end)
                
                self.buffer.insert_at_cursor(self.replacebar.get_text(), len(self.replacebar.get_text()))
                self.buffer.delete_selection(True, True)
                self.status_label.set_text(f"replaced '{search_text}' with '{replace_text}'")

    ### replace all
    def replace_all(self, *args):
        if len(self.searchbar.get_text()) > 0:
            print("replace_all")
            search_text = self.searchbar.get_text()
            replace_text = self.replacebar.get_text()
            self.status_label.set_text(f"replaced all '{search_text}' with '{replace_text}'")
            text = self.get_buffer()
            text = text.replace(search_text, replace_text)
            self.buffer.set_text(text)

    ### find all occurences in editor and select
    def on_search_changed(self, widget):   
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        self.buffer.remove_all_tags(start, end)
        self.find_text()
        
    def find_text(self, *args):
        search_text = self.searchbar.get_text()
        if not search_text == "":
            cursor_mark = self.buffer.get_insert()
            start = self.buffer.get_start_iter() ###get_iter_at_mark(cursor_mark)
            if start.get_offset() == self.buffer.get_char_count():
                start = self.buffer.get_start_iter()

            self.search_and_mark(search_text, start)

    ### mark matches
    def search_and_mark(self, text, start):
        end = self.buffer.get_end_iter()
        match = start.forward_search(text, 0, end)

        if match is not None:
            match_start, match_end = match
            self.buffer.apply_tag(self.tag_found, match_start, match_end)
            self.search_and_mark(text, match_end)

    ### show / hide findbox
    def toggle_findbox(self, *args):
        if self.findbox.is_visible():
            self.findbox.set_visible(False)
        else:
            self.findbox.set_visible(True)
            
    ### set modified   
    def is_modified(self, *args):
        self.is_changed = True
    
    ### new file clear editor
    def on_new_file(self, *args):
        if not self.is_changed:
            self.buffer = None
            self.editor.set_buffer(self.buffer)
            self.current_file = ""
        else:
            if self.maybe_saved():
                self.buffer = None
                self.editor.set_buffer(self.buffer)
                self.current_file = ""                   

    ### file save as ...
    def on_save_file(self, *args):
        myfile = ""
        dlg = Gtk.FileChooserDialog(title="Please choose a file", parent=None, action = 1)
        dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
             "Save", Gtk.ResponseType.OK)
        dlg.set_do_overwrite_confirmation (True)     
        dlg.add_filter(self.file_filter)

        if self.current_filename == "":
            dlg.set_current_name("new.txt")
        else:
            dlg.set_current_folder(path.dirname(self.current_file))
            dlg.set_current_name(self.current_filename)
        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            myfile = dlg.get_filename()
            
        else:
            infile = ("")
            
        dlg.destroy()
        if not myfile == "":
            print("saving", myfile)

            with open(myfile, 'w') as f:
                text = self.get_buffer()
                f.write(text)
                f.close()
                self.status_label.set_text(f"'{myfile}' saved")
                self.current_file = myfile
                self.current_filename = myfile.rpartition("/")[2]
                self.is_changed = False   
                
    ### save current file            
    def save_file(self, *args):
        myfile = self.current_file
        if not myfile == "":
            with open(myfile, 'w') as f:
                text = self.get_buffer()
                f.write(text)
                f.close()
                self.status_label.set_text(f"'{myfile}' saved")
                self.current_file = myfile
                self.current_filename = myfile.rpartition("/")[2]
                self.is_changed = False 
                print("modified", self.is_changed)
        else:
            self.on_save_file()

    ### ask to save changes
    def maybe_saved(self, *args):
        md = Gtk.MessageDialog(image=self.q_icon, title="TextEdit", 
                                text="The document was changed.\n\nSave changes?", 
                                parent=None)
        md.add_buttons("No", Gtk.ResponseType.CANCEL,
             "Yes", Gtk.ResponseType.OK)
        response = md.run()
        
        if response == Gtk.ResponseType.OK:
            ### save
            if not self.current_file == "":
                self.save_file(self.current_file)
            else:
                self.on_save_file()
        else:
            md.destroy()
        md.destroy()
        return True
            
    ### open file    
    def on_open(self, *args):       
        if self.is_changed:
            self.maybe_saved()
            self.on_open_file()
        else:
            self.on_open_file()
                
    def on_open_file(self, *args):
        data = ""
        myfile = ""
        dlg = Gtk.FileChooserDialog(title="Please choose a file", parent=None, action = 0)
        dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
             "Save", Gtk.ResponseType.OK)
        dlg.add_filter(self.file_filter)

        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            myfile = dlg.get_filename()
        else:
            myfile = ("")

        dlg.destroy()    
        
        
        if not myfile == "":
            self.buffer.set_text(data)
            print("loading:", myfile)
            with open(myfile, 'r') as f:
                data = f.read()
                self.buffer.set_text(data)
                self.editor.set_buffer(self.buffer)
                self.current_file = myfile
                self.current_filename = myfile.rpartition("/")[2]
                f.close()
                self.is_changed = False
                print("modified", self.is_changed)
                self.headerbar.set_subtitle(myfile)
                self.status_label.set_text(f"'{myfile}' loaded")

if __name__ == "__main__":
    w = MyWindow()
    w.main(sys.argv)
    

#!/usr/bin/python3
# -*- coding: utf-8 -*-

### created in January 2021 by Axel Schneider
### https://github.com/Axel-Erfurt/

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version('Keybinder', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, Gdk, GLib, GtkSource, GObject
import sys
from os import path
from urllib.request import url2pathname
import warnings


dnd_list = [Gtk.TargetEntry.new("text/uri-list", 0, 80)]

warnings.filterwarnings("ignore")

class MyWindow(Gtk.Window):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__()

    def main(self, argv):
        
        self.current_file = ""
        self.current_filename = ""
        self.current_folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS) ###path.expanduser("~")
        self.is_changed = False
        builder = Gtk.Builder()
        GObject.type_register(GtkSource.View)
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
        self.md_icon = builder.get_object("question_icon")
        
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
        
        ### textview
        self.editor = builder.get_object("editor")

        self.editor.drag_dest_set_target_list(dnd_list)
        self.editor.connect("drag_data_received", self.on_drag_data_received)
        
        self.editor.connect("key_press_event", self.editor_key_press)  
        
        self.lang_manager = GtkSource.LanguageManager()
        self.buffer = GtkSource.Buffer()
        self.editor.set_buffer(self.buffer)
        self.buffer.connect('changed', self.is_modified)
        
        # Settings for SourceView Find
        self.searchbar = builder.get_object("searchbar")
        self.settings = GtkSource.SearchSettings()
        self.searchbar.bind_property("text", self.settings, "search-text")
        self.settings.set_search_text("initial highlight")
        self.settings.set_wrap_around(True)
        self.search_context = GtkSource.SearchContext.new(self.buffer, self.settings)
        
        self.stylemanager = GtkSource.StyleSchemeManager()
        self.style = {1: "kate", 2: "builder", 3: "builder-dark", 4: "classic", 5: "tango", 6: "styles", 
                7: "cobalt", 8: "solarized-light", 9: "solarized-dark", 10: "classic"}
        scheme = self.stylemanager.get_scheme(self.style[1]) 
        self.buffer.set_style_scheme(scheme)
        
        self.style_box = builder.get_object("style_box")
        self.style_box.connect("changed", self.on_style_changed)
        
        self.findbox = builder.get_object("findbox")
        
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
        
        self.file_filter_text = Gtk.FileFilter()
        self.file_filter_text.set_name("Text Files")
        pattern = ["*.txt", "*.py", "*.c", "*.h", "*.cpp", "*.csv", "*.m3*", "*.vala", "*.tsv", "*.css"]
        for p in pattern:
            self.file_filter_text.add_pattern(p)
            
        self.file_filter_all = Gtk.FileFilter()
        self.file_filter_all.set_name("All Files")
        self.file_filter_all.add_pattern("*.*")     
        
        self.win.connect("delete-event", self.on_close)
        self.win.resize(800, 700)
        self.win.move(0, 0)
        self.win.show_all()
        ### focus on editor
        self.findbox.set_visible(False)

        ### load sys.argv file
        if len(sys.argv) > 1:
            myfile = sys.argv[1]
            self.open_file(myfile)
        else:
            self.status_label.set_text("Welcome to TextEdit")
        self.editor.grab_focus()
        self.is_changed = False
        Gtk.main() 
        
    def editor_key_press(self, widget, event):
        if (event.keyval == Gdk.keyval_from_name("n") and
            event.state == Gdk.ModifierType.CONTROL_MASK):
            self.on_new_file()
        if (event.keyval == Gdk.keyval_from_name("o") and
            event.state == Gdk.ModifierType.CONTROL_MASK):
            self.on_open_file()
        if (event.keyval == Gdk.keyval_from_name("s") and
            event.state == Gdk.ModifierType.CONTROL_MASK):
            self.save_file()
        if (event.keyval == Gdk.keyval_from_name("s") and
            event.state == Gdk.ModifierType.CONTROL_MASK and
            Gdk.ModifierType.SHIFT_MASK):
            self.on_save_file()
        if (event.keyval == Gdk.keyval_from_name("f") and
            event.state == Gdk.ModifierType.CONTROL_MASK):
            self.find_text()
        if (event.keyval == Gdk.keyval_from_name("q") and
            event.state == Gdk.ModifierType.CONTROL_MASK):
            self.on_close()
            
    def on_style_changed(self, *args):
        index = self.style_box.get_active()
        model = self.style_box.get_model()
        item = model[index]
        print(item[0])
        scheme = self.stylemanager.get_scheme(self.style[item[0]]) 
        self.buffer.set_style_scheme(scheme)
        
    ### drop file
    def on_drag_data_received(self, widget, context, x, y, selection, target_type, timestamp):
        myfile = ""
        if target_type == 80:
            uri = str(selection.get_data().decode().rstrip())
            myfile = url2pathname(uri)[7:]
            print(f'dropped file: {myfile}')
            if self.is_changed:
                self.maybe_saved()
                self.open_file(myfile)
            else:
                self.open_file(myfile)
        else:
            txt = selection.get_text()
            self.buffer.insert_at_cursor(txt)
                
                
    def open_file(self, myfile, *args):
        with open(myfile, 'r') as f:
            data = f.read()
            self.buffer.set_text(data)
            
            extension = myfile.rpartition(".")[2]
            if extension == "py":
                extension = "python"
            if extension == "qml":
                extension = "css"
            if extension == "csv":
                extension = "txt"
            self.buffer.set_language(self.lang_manager.get_language(extension))
            self.language = self.buffer.get_language()
            
            self.editor.set_buffer(self.buffer)
            self.current_file = myfile
            self.current_filename = myfile.rpartition("/")[2]
            self.current_folder = path.dirname(myfile)
            f.close()
            self.headerbar.set_subtitle(myfile)
            self.status_label.set_text(f"'{myfile}' loaded")
            self.headerbar.set_title("TextEdit")
            self.editor.grab_focus()
            self.is_changed = False
        
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

    def find_text(self, start_offset=1):
        if not self.findbox.is_visible():
            self.findbox.set_visible(True)
        self.searchbar.set_text("")
        self.searchbar.grab_focus()            
        if self.buffer.get_has_selection():
            a,b  = self.buffer.get_selection_bounds()
            mark = self.buffer.get_text(a, b, True)
            self.searchbar.set_text(mark)
        buf = self.buffer
        insert = buf.get_iter_at_mark(buf.get_insert())
        start, end = buf.get_bounds()
        insert.forward_chars(start_offset)
        match, start_iter, end_iter, wrapped = self.search_context.forward2(insert)

        if match:
            buf.place_cursor(start_iter)
            buf.move_mark(buf.get_selection_bound(), end_iter)
            self.view.scroll_to_mark(buf.get_insert(), 0.25, True, 0.5, 0.5)
            return True
        else:
            buf.place_cursor(buf.get_iter_at_mark(buf.get_insert()))

    ### show / hide findbox
    def toggle_findbox(self, *args):
        if not self.findbox.is_visible():
            self.findbox.set_visible(True)
        else:
            self.findbox.set_visible(False)
            
    ### set modified   
    def is_modified(self, *args):
        self.is_changed = True
        self.headerbar.set_title("TextEdit*")
    
    ### new file clear editor
    def on_new_file(self, *args):
        if self.is_changed:
            self.maybe_saved()
            self.buffer.set_text("")
            self.editor.set_buffer(self.buffer)
            self.current_file = ""
            self.current_filename = ""
            self.headerbar.set_title("TextEdit") 
            self.headerbar.set_subtitle("New")
            self.is_changed = False
        else:
            self.buffer.set_text("")
            self.editor.set_buffer(self.buffer)
            self.current_file = ""
            self.current_filename = ""
            self.headerbar.set_title("TextEdit")
            self.headerbar.set_subtitle("New")    
            self.is_changed = False
            
    ### open file    
    def on_open(self, *args):       
        if self.is_changed:
            self.maybe_saved()
            self.on_open_file()
            self.is_changed = False
        else:
            self.on_open_file()
            self.is_changed = False
                
    def on_open_file(self, *args):
        myfile = ""
        dlg = Gtk.FileChooserDialog(title="Please choose a file", parent=None, action = 0)
        dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
             "Open", Gtk.ResponseType.OK)
        dlg.add_filter(self.file_filter_text)
        dlg.add_filter(self.file_filter_all)
        dlg.set_current_folder(self.current_folder)
        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            myfile = dlg.get_filename()
        else:
            myfile = ("")

        dlg.destroy()    
        
        
        if not myfile == "":
            self.open_file(myfile)

    ### file save as ...
    def on_save_file(self, *args):
        myfile = ""
        dlg = Gtk.FileChooserDialog(title="Please choose a file", parent=None, action = 1)
        dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
             "Save", Gtk.ResponseType.OK)
        dlg.set_do_overwrite_confirmation (True)     
        dlg.add_filter(self.file_filter_text)
        dlg.add_filter(self.file_filter_all)
        if self.current_filename == "":
            dlg.set_current_name("new.txt")
        else:
            dlg.set_current_folder(path.dirname(self.current_file))
            dlg.set_current_name(self.current_filename)
        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            myfile = dlg.get_filename()
            
        else:
            myfile = ("")
            
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
                self.current_folder = path.dirname(myfile)
                self.is_changed = False
                self.headerbar.set_title("TextEdit")
                self.headerbar.set_subtitle(myfile)
                
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
                self.current_folder = path.dirname(myfile)
                self.is_changed = False 
                self.headerbar.set_title("TextEdit")
                self.headerbar.set_subtitle(myfile)
        else:
            self.on_save_file()
        return True

    ### ask to save changes
    def maybe_saved(self, *args):
        print("is modified", self.is_changed)
        md = Gtk.MessageDialog(title="TextEdit", 
                                text="The document was changed.\n\nSave changes?", 
                                parent=None, buttons=("Cancel", Gtk.ResponseType.CANCEL,
             "Yes", Gtk.ResponseType.YES, "No", Gtk.ResponseType.NO))
        md.set_image(self.q_icon)
        response = md.run()
        if response == Gtk.ResponseType.YES:
            ### save
            self.save_file()
            md.destroy()
            return False
        elif response == Gtk.ResponseType.NO:
            md.destroy()
            return False
        elif response == Gtk.ResponseType.CANCEL:
            md.destroy()
            return True
        md.destroy()
        
    ### close window
    def on_close(self, *args):
        print(f"{self.current_file} changed: {self.is_changed}")
        if self.is_changed:
            b = self.maybe_saved()
            print (f"close: {b}")
            if b: 
                return True
            else:
                Gtk.main_quit()
        else:
            Gtk.main_quit()
            

if __name__ == "__main__":
    w = MyWindow()
    w.main(sys.argv)
    

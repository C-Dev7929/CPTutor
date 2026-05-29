import sublime
import os

def create_or_focus_chat_view(window):
    # Find existing chat view
    chat_view = None
    for view in window.views():
        if view.name() == "CPTutor Chat":
            chat_view = view
            break
            
    if chat_view:
        window.focus_view(chat_view)
        # Ensure it's in the right group (group 1 in 2-column layout, or group 4 in the 5-group layout)
        # We'll let the layout logic handle the group, but we return the view
        return chat_view
            
    # Create new view
    view = window.new_file()
    view.set_name("CPTutor Chat")
    view.set_scratch(True) # Don't prompt to save
    view.set_read_only(False) # Allow initial loading
    
    # Try to set markdown syntax
    view.set_syntax_file("Packages/Markdown/Markdown.sublime-syntax")
    
    # Settings for better chat experience
    view_settings = view.settings()
    view_settings.set("word_wrap", True)
    view_settings.set("line_numbers", False)
    view_settings.set("gutter", False)
    view_settings.set("draw_centered", False)
    view_settings.set("scroll_past_end", True)
    
    return view

def append_to_chat(view, text):
    view.run_command("append", {"characters": text})
    view.show(view.size())

def get_chat_content(view):
    return view.substr(sublime.Region(0, view.size()))

def load_history(view, filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                view.run_command("append", {"characters": content})
                view.show(view.size())
        except Exception as e:
            print("CPTutor: Load history failed: {0}".format(e))

def save_history(view, filepath):
    content = get_chat_content(view)
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print("CPTutor: Save history failed: {0}".format(e))

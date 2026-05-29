import sublime
import os
import re

def get_open_files_context(window, root_dir):
    context_parts = []
    for view in window.views():
        # Skip chat view and special views
        if view.name() == "CPTutor Chat" or view.is_scratch() or view.settings().get('is_widget'):
            continue
            
        file_path = view.file_name()
        if file_path:
            # Only include files within the root directory for security
            if not file_path.startswith(root_dir):
                continue
                
            rel_path = os.path.relpath(file_path, root_dir)
            
            content = ""
            if view.is_dirty():
                content = view.substr(sublime.Region(0, view.size()))
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    content = view.substr(sublime.Region(0, view.size()))
            
            # Simple language detection
            ext = os.path.splitext(file_path)[1].lower()
            lang = "cpp" if ext == ".cpp" else "python" if ext == ".py" else "text"
            
            context_parts.append("File: {0}\n```{1}\n{2}\n```".format(rel_path, lang, content))
        else:
            # Unsaved buffer (not associated with a file yet)
            name = view.name() or "unsaved_buffer"
            content = view.substr(sublime.Region(0, view.size()))
            context_parts.append("File: unsaved/{0}\n```\n{1}\n```".format(name, content))
            
    return "\n\n".join(context_parts)

def parse_file_blocks(response_text):
    # Regex for ```file:path\ncontent```
    pattern = r'```file:(.+?)\n(.+?)```'
    matches = re.findall(pattern, response_text, re.DOTALL)
    return matches

def apply_file_change(window, root_dir, rel_path, content):
    abs_path = os.path.join(root_dir, rel_path)
    
    # Confirm with user
    msg = "Bạn có muốn áp dụng thay đổi cho file '{0}' không?".format(rel_path)
    if sublime.yes_no_cancel_dialog(msg, "Có", "Không") == sublime.DIALOG_YES:
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Open or refresh the file in the window
            window.open_file(abs_path)
            return True
        except Exception as e:
            sublime.error_message("Lỗi khi ghi file {0}: {1}".format(rel_path, str(e)))
    return False

import sublime
import sublime_plugin
import os
import threading

# Import local modules
try:
    from . import api
    from . import chat_view
    from . import file_handler
except ImportError:
    import api
    import chat_view
    import file_handler

def get_root_dir(window):
    """Lấy thư mục gốc của project (thư mục đầu tiên trong sidebar)"""
    folders = window.folders()
    if folders:
        return folders[0]
    return ""

class CptutorStartCommand(sublime_plugin.WindowCommand):
    def run(self, no_layout=False):
        settings = sublime.load_settings("CPTutor.sublime-settings")
        api_key = settings.get("gemini_api_key")
        
        if not api_key and not settings.get("use_cli_mode", False):
            self.window.show_input_panel("Nhập Gemini API Key:", "", self.on_done_key, None, None)
        else:
            self.setup_ui(no_layout)

    def on_done_key(self, key):
        if key:
            settings = sublime.load_settings("CPTutor.sublime-settings")
            settings.set("gemini_api_key", key)
            sublime.save_settings("CPTutor.sublime-settings")
            self.setup_ui()
        else:
            sublime.status_message("Bỏ qua nhập API Key. Bạn có thể dùng chế độ CLI.")
            self.setup_ui()

    def setup_ui(self, no_layout=False):
        if not no_layout:
            # Layout 2 cột mặc định
            self.window.set_layout({
                "cols": [0.0, 0.5, 1.0],
                "rows": [0.0, 1.0],
                "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
            })
        
        view = chat_view.create_or_focus_chat_view(self.window)
        
        if no_layout:
            current_group = self.window.active_group()
            self.window.set_view_index(view, current_group, 0)
        else:
            self.window.set_view_index(view, 1, 0)
        
        plugin_dir = os.path.join(sublime.packages_path(), "CPTutor")
        history_file = os.path.join(plugin_dir, "CPTutor_chat.md")
        
        if view.size() == 0:
            chat_view.load_history(view, history_file)
            if view.size() == 0:
                chat_view.append_to_chat(view, "# CPTutor Chat\n\nHãy đặt câu hỏi để bắt đầu.\n\n---\n")
        
        self.window.focus_view(view)

class CptutorChangeApiKeyCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings("CPTutor.sublime-settings")
        current_key = settings.get("gemini_api_key", "")
        self.window.show_input_panel("Nhập Gemini API Key mới:", current_key, self.on_done, None, None)

    def on_done(self, key):
        if key:
            settings = sublime.load_settings("CPTutor.sublime-settings")
            settings.set("gemini_api_key", key)
            sublime.save_settings("CPTutor.sublime-settings")
            sublime.status_message("Đã cập nhật API Key.")

class CptutorToggleCliModeCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings("CPTutor.sublime-settings")
        current = settings.get("use_cli_mode", False)
        settings.set("use_cli_mode", not current)
        sublime.save_settings("CPTutor.sublime-settings")
        mode = "Google Login (CLI)" if not current else "API Key"
        sublime.message_dialog("Đã chuyển sang chế độ: {0}".format(mode))

class CptutorSendMessageCommand(sublime_plugin.WindowCommand):
    def run(self):
        active_view = self.window.active_view()
        if active_view and active_view.name() == "CPTutor Chat":
            content = active_view.substr(sublime.Region(0, active_view.size()))
            parts = content.split("---")
            user_text = parts[-1].strip()
            
            if user_text.startswith("**Bạn:**"):
                user_text = user_text[len("**Bạn:**"):].strip()
            
            if user_text:
                last_divider_pos = content.rfind("---")
                if last_divider_pos != -1:
                    erase_region = sublime.Region(last_divider_pos + 3, active_view.size())
                    active_view.run_command("cptutor_erase_region", {"start": erase_region.begin(), "end": erase_region.end()})
                self.process_message(user_text, active_view)
            else:
                sublime.status_message("Hãy nhập câu hỏi sau dấu ---")
        else:
            self.window.show_input_panel("Câu hỏi cho Gemini:", "", self.on_done_panel, None, None)

    def on_done_panel(self, text):
        if not text: return
        view = None
        for v in self.window.views():
            if v.name() == "CPTutor Chat":
                view = v
                break
        if not view:
            sublime.error_message("Hãy chạy 'CPTutor: Start' trước.")
            return
        self.process_message(text, view)

    def process_message(self, text, view):
        chat_view.append_to_chat(view, "\n**Bạn:** {0}\n\n---\n".format(text))
        sublime.status_message("Đang chờ Gemini...")
        threading.Thread(target=self.worker, args=(text, view)).start()

    def worker(self, user_text, view):
        settings = sublime.load_settings("CPTutor.sublime-settings")
        api_key = settings.get("gemini_api_key")
        use_cli_mode = settings.get("use_cli_mode", False)
        root_dir = get_root_dir(self.window)
        
        context = file_handler.get_open_files_context(self.window, root_dir)
        
        plugin_dir = os.path.join(sublime.packages_path(), "CPTutor")
        role_file = os.path.join(plugin_dir, "gemini-role.md")
        system_instruction = "Lựa chọn ngôn ngữ: Tiếng Việt."
        if os.path.exists(role_file):
            try:
                with open(role_file, 'r', encoding='utf-8') as f:
                    system_instruction = f.read()
            except: pass
        
        prompt = "{0}\n\nContext:\n{1}".format(user_text, context)
        if use_cli_mode:
            response = api.query_gemini_cli(system_instruction, prompt)
        else:
            response = api.query_gemini(api_key, system_instruction, prompt)
        
        sublime.set_timeout(lambda: self.on_response(response, view, root_dir), 0)

    def on_response(self, response, view, root_dir):
        chat_view.append_to_chat(view, "**Gemini:**\n{0}\n\n---\n".format(response))
        plugin_dir = os.path.join(sublime.packages_path(), "CPTutor")
        history_file = os.path.join(plugin_dir, "CPTutor_chat.md")
        chat_view.save_history(view, history_file)
        
        blocks = file_handler.parse_file_blocks(response)
        for rel_path, content in blocks:
            if root_dir and file_handler.apply_file_change(self.window, root_dir, rel_path, content):
                chat_view.append_to_chat(view, "*Đã cập nhật: {0}*\n\n".format(rel_path))
                chat_view.save_history(view, history_file)

class CptutorEraseRegionCommand(sublime_plugin.TextCommand):
    def run(self, edit, start, end):
        self.view.erase(edit, sublime.Region(start, end))

import customtkinter as ctk
import threading
import keyboard
import config
import screenshot_utils
import n8n_client
import settings_manager
import voice_utils
import tts_utils


class HotkeyCapture(ctk.CTkFrame):
    """Widget for capturing hotkey input with a Set button."""

    def __init__(self, parent, initial_value="", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.hotkey_value = initial_value
        self.is_capturing = False
        self.pressed_keys = set()
        self.capture_hook = None

        # Layout
        self.grid_columnconfigure(0, weight=1)

        # Display current hotkey
        self.hotkey_display = ctk.CTkLabel(
            self,
            text=initial_value or "(not set)",
            fg_color="gray20",
            corner_radius=5,
            height=32,
            anchor="center"
        )
        self.hotkey_display.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Set button
        self.set_btn = ctk.CTkButton(
            self,
            text="Set",
            width=60,
            command=self.start_capture
        )
        self.set_btn.grid(row=0, column=1)

    def start_capture(self):
        """Start capturing hotkey input."""
        if self.is_capturing:
            return

        self.is_capturing = True
        self.pressed_keys = set()
        self.set_btn.configure(text="...", state="disabled")
        self.hotkey_display.configure(text="Press keys...")

        # Hook keyboard events
        self.capture_hook = keyboard.hook(self._on_key_event, suppress=False)

    def _on_key_event(self, event):
        """Handle keyboard events during capture."""
        if not self.is_capturing:
            return

        if event.event_type == "down":
            # Normalize key name
            key = event.name.lower()
            # Handle modifiers
            if key in ["ctrl", "control", "left ctrl", "right ctrl"]:
                key = "ctrl"
            elif key in ["alt", "left alt", "right alt"]:
                key = "alt"
            elif key in ["shift", "left shift", "right shift"]:
                key = "shift"
            elif key in ["windows", "left windows", "right windows", "win"]:
                key = "win"

            self.pressed_keys.add(key)
            self._update_display()

        elif event.event_type == "up":
            # When any key is released, finalize the capture
            if self.pressed_keys:
                self.after(50, self._finalize_capture)

    def _update_display(self):
        """Update the display with current pressed keys."""
        parts = []

        # Add modifiers first in order
        for mod in ["ctrl", "alt", "shift", "win"]:
            if mod in self.pressed_keys:
                parts.append(mod)

        # Add other keys
        for key in sorted(self.pressed_keys):
            if key not in ["ctrl", "alt", "shift", "win"]:
                parts.append(key)

        display_text = "+".join(parts) if parts else "Press keys..."
        self.hotkey_display.configure(text=display_text)

    def _finalize_capture(self):
        """Finalize the hotkey capture."""
        if not self.is_capturing:
            return

        self.is_capturing = False

        # Unhook keyboard
        if self.capture_hook:
            keyboard.unhook(self.capture_hook)
            self.capture_hook = None

        # Build hotkey string
        parts = []

        # Add modifiers first in order
        for mod in ["ctrl", "alt", "shift", "win"]:
            if mod in self.pressed_keys:
                parts.append(mod)

        # Add other keys
        for key in sorted(self.pressed_keys):
            if key not in ["ctrl", "alt", "shift", "win"]:
                parts.append(key)

        if parts:
            self.hotkey_value = "+".join(parts)
            self.hotkey_display.configure(text=self.hotkey_value)
        else:
            self.hotkey_display.configure(text=self.hotkey_value or "(not set)")

        self.set_btn.configure(text="Set", state="normal")
        self.pressed_keys = set()

    def get(self):
        """Get the current hotkey value."""
        return self.hotkey_value

    def set(self, value):
        """Set the hotkey value."""
        self.hotkey_value = value
        self.hotkey_display.configure(text=value or "(not set)")


class OverlayApp(ctk.CTk):
    def __init__(self, update_hotkey_callback=None):
        super().__init__()

        self.update_hotkey_callback = update_hotkey_callback
        self.title("Helper AI Overlay")
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT_INITIAL}")
        self.overrideredirect(True) # Frameless window
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)  # Slight transparency
        self.resizable(False, False)
        
        # Center the window roughly
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - config.WINDOW_WIDTH) // 2
        y = (screen_height // 3) # Position in upper third
        self.geometry(f"+{x}+{y}")

        # Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Configure main grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Input row
        self.grid_rowconfigure(2, weight=1)  # Result row (expandable)

        # Drag functionality
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)
        self.x = 0
        self.y = 0

        # ============ ROW 0: TOP TOOLBAR ============
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        self.toolbar_frame.grid_columnconfigure(1, weight=1)  # Spacer

        # Left: New Chat button
        self.new_chat_btn = ctk.CTkButton(
            self.toolbar_frame, 
            text="+ New Chat", 
            width=90, 
            height=28,
            font=("Arial", 12),
            command=self.new_chat
        )
        self.new_chat_btn.grid(row=0, column=0, sticky="w")

        # Right: History + Settings + Hide + Close
        self.right_toolbar = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        self.right_toolbar.grid(row=0, column=2, sticky="e")

        self.history_btn = ctk.CTkButton(
            self.right_toolbar,
            text="History",
            width=70,
            height=28,
            font=("Arial", 12),
            fg_color="transparent",
            border_width=1,
            command=self.show_history
        )
        self.history_btn.pack(side="left", padx=(0, 5))

        self.settings_btn = ctk.CTkButton(
            self.right_toolbar,
            text="⚙",
            width=28,
            height=28,
            command=self.open_settings
        )
        self.settings_btn.pack(side="left", padx=(0, 5))

        self.hide_btn = ctk.CTkButton(
            self.right_toolbar,
            text="👁",
            width=28,
            height=28,
            fg_color="gray30",
            hover_color="gray40",
            command=self.hide_overlay
        )
        self.hide_btn.pack(side="left", padx=(0, 5))

        self.close_btn = ctk.CTkButton(
            self.right_toolbar,
            text="✕",
            width=28,
            height=28,
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.close_app
        )
        self.close_btn.pack(side="left")

        # ============ ROW 1: INPUT WITH EMBEDDED SEND ============
        self.input_frame = ctk.CTkFrame(self, corner_radius=10)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Ask a question...", 
            height=45, 
            font=("Arial", 14),
            border_width=0
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(10, 0), pady=5)
        self.entry.bind("<Return>", self.on_submit)
        self.entry.bind("<Escape>", self.hide_overlay)

        # Mic Button
        self.mic_btn = ctk.CTkButton(
            self.input_frame, 
            text="🎤", 
            width=40, 
            height=35,
            font=("Arial", 16),
            fg_color="gray30",
            command=self.toggle_recording
        )
        self.mic_btn.grid(row=0, column=1, padx=(5, 0), pady=5)

        # Send Button
        self.send_btn = ctk.CTkButton(
            self.input_frame, 
            text="➤", 
            width=40, 
            height=35,
            font=("Arial", 16),
            command=self.on_submit
        )
        self.send_btn.grid(row=0, column=2, padx=5, pady=5)

        self.is_recording = False
        self.is_ptt_recording = False  # Track push-to-talk for auto-send

        # ============ ROW 2: BOTTOM CONTROLS ============
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 10))
        self.controls_frame.grid_columnconfigure(1, weight=1)  # Spacer

        # Left: Complexity Segmented Button
        self.complexity_var = ctk.StringVar(value="Low")
        self.complexity_segment = ctk.CTkSegmentedButton(
            self.controls_frame,
            values=["Low", "High"],
            variable=self.complexity_var,
            font=("Arial", 12)
        )
        self.complexity_segment.grid(row=0, column=0, sticky="w")

        # Center: Monitor Selection
        monitors = screenshot_utils.get_monitors()
        self.monitor_names = [m["name"] for m in monitors]
        self.monitor_map = {m["name"]: m["index"] for m in monitors}
        
        saved_monitor = settings_manager.get_selected_monitor()
        saved_name = f"Screen {saved_monitor}" if f"Screen {saved_monitor}" in self.monitor_names else self.monitor_names[0]
        self.monitor_var = ctk.StringVar(value=saved_name)
        
        self.monitor_menu = ctk.CTkOptionMenu(
            self.controls_frame,
            values=self.monitor_names,
            variable=self.monitor_var,
            command=self.on_monitor_select,
            width=90,
            font=("Arial", 11)
        )
        self.monitor_menu.grid(row=0, column=1, padx=10)

        self.highlight_window = None
        self._dropdown_bindings_set = False

        # Bind to detect when dropdown opens
        self.monitor_menu.bind("<Button-1>", self._on_dropdown_click)

        # Right: Screenshot Toggle
        self.screenshot_var = ctk.BooleanVar(value=settings_manager.get_include_screenshot())
        self.screenshot_switch = ctk.CTkSwitch(
            self.controls_frame, 
            text="📷", 
            variable=self.screenshot_var, 
            command=self.toggle_screenshot_setting,
            font=("Arial", 12)
        )
        self.screenshot_switch.grid(row=0, column=2, sticky="e")

        # ============ RESULT FRAME (Hidden initially) ============
        self.result_frame = ctk.CTkFrame(self, corner_radius=10)
        self.result_textbox = ctk.CTkTextbox(self.result_frame, font=("Arial", 12), wrap="word")
        self.result_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.retry_btn = ctk.CTkButton(self.result_frame, text="Retry", command=self.on_submit)

        # Loading Indicator (will be shown in input_frame)
        self.progress_bar = ctk.CTkProgressBar(self.input_frame, height=3)
        self.progress_bar.set(0)

        self.is_visible = True
        self.settings_window = None
        self.history_window = None
        self.current_session_id = None
        self.chat_messages = []  # Track current conversation
        self.voice_hotkey_id = None
        self.setup_window = None

        # Register voice hotkey
        self.register_voice_hotkey(settings_manager.get_voice_hotkey())

        # Check for first-time setup
        if settings_manager.is_first_run():
            self.after(100, self.show_first_run_setup)

    def register_voice_hotkey(self, hotkey):
        """Register or update the voice hotkey."""
        # Remove old hotkey if exists
        if self.voice_hotkey_id:
            try:
                keyboard.remove_hotkey(self.voice_hotkey_id)
            except:
                pass
        
        # Register new hotkey
        try:
            voice_mode = settings_manager.get_voice_mode()
            if voice_mode == "push_to_talk":
                # Hold to record, release to stop
                keyboard.on_press_key(hotkey.split('+')[-1], self._on_voice_key_down, suppress=False)
                keyboard.on_release_key(hotkey.split('+')[-1], self._on_voice_key_up, suppress=False)
            else:
                # Toggle mode - press to start/stop
                self.voice_hotkey_id = keyboard.add_hotkey(hotkey, self.toggle_recording)
        except Exception as e:
            print(f"Failed to register voice hotkey: {e}")

    def _on_voice_key_down(self, event):
        """Push-to-talk: start recording on key down."""
        if not self.is_recording and self.is_visible:
            self.after(0, self._start_ptt_recording)

    def _on_voice_key_up(self, event):
        """Push-to-talk: stop recording on key up."""
        if self.is_recording:
            self.after(0, self._stop_ptt_recording)

    def _start_ptt_recording(self):
        self.is_recording = True
        self.is_ptt_recording = True  # Track that this is PTT mode
        self.mic_btn.configure(fg_color="red", text="⏹")
        self.entry.configure(placeholder_text="Listening...")
        voice_utils.start_recording(callback=self.on_transcription)

    def _stop_ptt_recording(self):
        self.is_recording = False
        self.mic_btn.configure(fg_color="orange", text="...")
        self.entry.configure(placeholder_text="Transcribing...")
        voice_utils.stop_recording()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def toggle_screenshot_setting(self):
        settings_manager.set_include_screenshot(self.screenshot_var.get())

    def on_monitor_select(self, selected_name):
        """Handle monitor selection."""
        monitor_index = self.monitor_map.get(selected_name, 1)
        settings_manager.set_selected_monitor(monitor_index)
        # Show brief highlight to confirm
        self.show_monitor_highlight(None)
        self.after(500, self.hide_monitor_highlight)

    def _on_dropdown_click(self, event=None):
        """Handle dropdown click - bind hover events to dropdown options after a delay."""
        # Small delay to let dropdown render
        self.after(50, self._bind_dropdown_hover_events)

    def _bind_dropdown_hover_events(self):
        """Bind hover events to each dropdown option."""
        try:
            # Access the internal dropdown menu
            dropdown = self.monitor_menu._dropdown_menu
            if dropdown and dropdown.winfo_exists():
                # Get all button widgets in the dropdown
                for child in dropdown.winfo_children():
                    # The dropdown contains a frame with buttons
                    if hasattr(child, 'winfo_children'):
                        for button in child.winfo_children():
                            if hasattr(button, 'cget'):
                                try:
                                    text = button.cget("text")
                                    if text in self.monitor_names:
                                        button.bind("<Enter>", lambda e, name=text: self.show_monitor_highlight_for(name))
                                        button.bind("<Leave>", self.hide_monitor_highlight)
                                except:
                                    pass

                # Also bind to dropdown closing
                dropdown.bind("<Unmap>", self.hide_monitor_highlight)
        except Exception as e:
            pass  # Dropdown might not exist yet

    def show_monitor_highlight_for(self, monitor_name):
        """Show highlight border around a specific monitor by name."""
        # First hide any existing highlight
        self.hide_monitor_highlight()

        monitor_index = self.monitor_map.get(monitor_name, 1)
        bounds = screenshot_utils.get_monitor_bounds(monitor_index)

        if not bounds:
            return

        # Create transparent window with colored border
        self.highlight_window = ctk.CTkToplevel(self)
        self.highlight_window.overrideredirect(True)
        self.highlight_window.attributes("-topmost", True)
        self.highlight_window.attributes("-alpha", 0.3)

        # Position at monitor bounds
        border = 8
        self.highlight_window.geometry(
            f"{bounds['width']}x{bounds['height']}+{bounds['left']}+{bounds['top']}"
        )

        # Create colored frame as border
        frame = ctk.CTkFrame(
            self.highlight_window,
            fg_color="#00CED1",  # Teal
            corner_radius=0
        )
        frame.pack(fill="both", expand=True)

        # Inner transparent area
        inner = ctk.CTkFrame(
            frame,
            fg_color="#1a1a1a",
            corner_radius=0
        )
        inner.pack(fill="both", expand=True, padx=border, pady=border)

    def show_monitor_highlight(self, event=None):
        """Show highlight border around selected monitor."""
        selected_name = self.monitor_var.get()
        self.show_monitor_highlight_for(selected_name)

    def hide_monitor_highlight(self, event=None):
        """Hide the monitor highlight."""
        if self.highlight_window and self.highlight_window.winfo_exists():
            self.highlight_window.destroy()
            self.highlight_window = None

    def toggle_recording(self):
        if self.is_recording:
            # Stop recording
            self.is_recording = False
            self.mic_btn.configure(fg_color="orange", text="...")
            self.entry.configure(placeholder_text="Transcribing...")
            voice_utils.stop_recording()
        else:
            # Start recording
            self.is_recording = True
            self.mic_btn.configure(fg_color="red", text="⏹")
            self.entry.configure(placeholder_text="Listening... (click to stop)")
            voice_utils.start_recording(callback=self.on_transcription)

    def on_transcription(self, text, error):
        """Called when transcription completes."""
        self.after(0, self._update_after_transcription, text, error)

    def _update_after_transcription(self, text, error):
        was_ptt = self.is_ptt_recording
        self.is_recording = False
        self.is_ptt_recording = False
        self.mic_btn.configure(fg_color="gray30", text="🎤")
        self.entry.configure(placeholder_text="Ask a question...")

        if error:
            self.entry.delete(0, 'end')
            self.entry.insert(0, f"[Mic Error: {error}]")
        elif text:
            current = self.entry.get()
            if current:
                self.entry.insert('end', " " + text)
            else:
                self.entry.insert(0, text)
            self.entry.focus_set()

            # Auto-send if this was push-to-talk mode
            if was_ptt and text.strip():
                self.after(100, self.on_submit)

    def show_overlay(self):
        self.deiconify()
        self.entry.focus_set()
        self.is_visible = True
        # Don't clear entry if we are in a session and just hiding/showing
        # But if it's a fresh start or we want to clear input, we can.
        # For now, let's keep input if it wasn't submitted.
        self.reset_ui()

    def hide_overlay(self, event=None):
        self.withdraw()
        self.is_visible = False
        # Also close settings/history if open
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
            self.settings_window = None
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.destroy()
            self.history_window = None

    def close_app(self):
        """Close the application completely."""
        self.destroy()

    def reset_ui(self):
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT_INITIAL}")
        self.result_frame.grid_forget()
        self.progress_bar.grid_forget()
        self.entry.configure(state="normal")
        
        # If we have a session with messages, we might want to show the last response?
        # For now, let's keep it simple: reset UI hides result. 
        # But if user wants to see history, they click History.

    def new_chat(self):
        self.current_session_id = None
        self.chat_messages = []
        self.entry.delete(0, 'end')
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("0.0", "end")
        self.result_textbox.configure(state="disabled")
        self.reset_ui()

    def on_submit(self, event=None):
        query = self.entry.get()
        if not query:
            return

        complexity = self.complexity_var.get()

        if not self.current_session_id:
            self.current_session_id = settings_manager.create_session()

        # Add user message to chat immediately
        self.chat_messages.append({"role": "user", "content": query})
        self.display_chat()

        include_screenshot = self.screenshot_var.get()
        screenshot_bytes = None

        if include_screenshot:
            # Hide window to take screenshot
            self.withdraw()
            # Force update to ensure window is gone
            self.update()
            
            # specific wait might be needed for some compositors, but update() usually suffices
            # Capture screen immediately while hidden
            try:
                monitor_index = settings_manager.get_selected_monitor()
                screenshot_bytes = screenshot_utils.capture_screen_bytes(monitor_index)
            except Exception as e:
                print(f"Error capturing screen: {e}")
                screenshot_bytes = None
            
            # Restore window
            self.deiconify()

        # Show loading state
        self.entry.configure(state="disabled")
        self.send_btn.configure(state="disabled", text="...")
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.progress_bar.start()
        self.retry_btn.pack_forget() # Hide retry button while loading

        # Start background thread, passing the captured screenshot
        threading.Thread(target=self.process_query, args=(query, screenshot_bytes, complexity, self.current_session_id), daemon=True).start()

    def process_query(self, query, screenshot_bytes, complexity, session_id):
        try:
            # If screenshot was requested but failed, we might still want to proceed?
            # Or if it wasn't requested, it is None.
            # n8n_client handles None.
            
            # Send to n8n
            response = n8n_client.send_query(query, screenshot_bytes, complexity, session_id)
            
            # Save to history (session)
            settings_manager.save_interaction(session_id, query, response)

            # Update UI on main thread
            self.after(0, self.show_result, response)
        except Exception as e:
            self.after(0, self.show_result, f"Error: {str(e)}", True)

    def show_result(self, text, is_error=False):
        self.progress_bar.stop()
        self.progress_bar.grid_forget()

        # Add assistant response to chat messages
        if not is_error:
            self.chat_messages.append({"role": "assistant", "content": text})

        self.display_chat()

        if is_error:
            self.retry_btn.pack(pady=5)
        else:
            self.retry_btn.pack_forget()

        self.entry.configure(state="normal")
        self.send_btn.configure(state="normal", text="➤")
        self.entry.focus_set()
        # Clear entry to allow follow-up question
        if not is_error:
            self.entry.delete(0, 'end')

        # Play TTS if enabled and not an error
        if not is_error and settings_manager.get_tts_enabled():
            self._play_tts(text)

    def _play_tts(self, text):
        """Play text-to-speech for the given text."""
        voice = settings_manager.get_tts_voice()
        speed = settings_manager.get_tts_speed()

        def on_tts_complete(error):
            if error:
                print(f"TTS Error: {error}")

        tts_utils.speak(
            text=text,
            voice=voice,
            speed=speed,
            callback=on_tts_complete
        )

    def stop_tts(self):
        """Stop any ongoing TTS playback."""
        tts_utils.stop()

    def display_chat(self):
        """Display the full chat conversation."""
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT_EXPANDED}")
        self.result_frame.grid(row=3, column=0, sticky="nsew", padx=15, pady=(5, 15))

        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("0.0", "end")

        for msg in self.chat_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                self.result_textbox.insert("end", "You: ", "user_label")
                self.result_textbox.insert("end", f"{content}\n\n")
            else:
                self.result_textbox.insert("end", "AI: ", "ai_label")
                self.result_textbox.insert("end", f"{content}\n\n")

        # Configure tags for styling
        self.result_textbox.tag_config("user_label", foreground="#4da6ff")
        self.result_textbox.tag_config("ai_label", foreground="#50fa7b")

        self.result_textbox.configure(state="disabled")
        # Scroll to bottom
        self.result_textbox.see("end")

    def open_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
            self.settings_window = None
            return

        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("Settings")
        self.settings_window.geometry("420x600")
        self.settings_window.minsize(420, 400)
        self.settings_window.attributes("-topmost", True)
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)

        # Scrollable content frame
        content = ctk.CTkScrollableFrame(self.settings_window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # Overlay Hotkey with capture widget
        ctk.CTkLabel(content, text="Overlay Hotkey:", anchor="w").pack(fill="x", pady=(10, 5))
        hotkey_capture = HotkeyCapture(content, initial_value=settings_manager.get_hotkey())
        hotkey_capture.pack(fill="x", pady=(0, 10))

        # Webhook URL
        ctk.CTkLabel(content, text="Webhook URL:", anchor="w").pack(fill="x", pady=(10, 5))
        url_entry = ctk.CTkEntry(content, width=350)
        url_entry.insert(0, settings_manager.get_webhook_url())
        url_entry.pack(fill="x", pady=(0, 10))

        # Voice Mode
        ctk.CTkLabel(content, text="Voice Mode:", anchor="w").pack(fill="x", pady=(10, 5))
        voice_mode_var = ctk.StringVar(value=settings_manager.get_voice_mode())
        voice_mode_menu = ctk.CTkSegmentedButton(
            content,
            values=["toggle", "push_to_talk"],
            variable=voice_mode_var
        )
        voice_mode_menu.pack(fill="x", pady=(0, 10))

        # Voice Hotkey with capture widget
        ctk.CTkLabel(content, text="Voice Hotkey:", anchor="w").pack(fill="x", pady=(10, 5))
        voice_hotkey_capture = HotkeyCapture(content, initial_value=settings_manager.get_voice_hotkey())
        voice_hotkey_capture.pack(fill="x", pady=(0, 10))

        # TTS Settings Section
        tts_separator = ctk.CTkFrame(content, height=2, fg_color="gray50")
        tts_separator.pack(fill="x", pady=(10, 10))

        ctk.CTkLabel(content, text="Text-to-Speech", anchor="w", font=("Arial", 14, "bold")).pack(fill="x", pady=(0, 5))

        # TTS Enable Toggle
        tts_enabled_var = ctk.BooleanVar(value=settings_manager.get_tts_enabled())
        tts_switch = ctk.CTkSwitch(
            content,
            text="Enable TTS (speak AI responses)",
            variable=tts_enabled_var
        )
        tts_switch.pack(fill="x", pady=(0, 10))

        # Voice selection
        ctk.CTkLabel(content, text="Voice:", anchor="w").pack(fill="x", pady=(5, 5))
        tts_voice_var = ctk.StringVar(value=settings_manager.get_tts_voice())
        voice_menu = ctk.CTkOptionMenu(
            content,
            values=["jenny", "guy", "aria", "davis", "jane", "jason", "sara", "tony", "nancy"],
            variable=tts_voice_var
        )
        voice_menu.pack(fill="x", pady=(0, 10))

        # Speed slider
        ctk.CTkLabel(content, text="Speed:", anchor="w").pack(fill="x", pady=(5, 5))

        speed_frame = ctk.CTkFrame(content, fg_color="transparent")
        speed_frame.pack(fill="x", pady=(0, 10))
        speed_frame.grid_columnconfigure(0, weight=1)

        tts_speed_var = ctk.DoubleVar(value=settings_manager.get_tts_speed())
        speed_label = ctk.CTkLabel(speed_frame, text=f"{tts_speed_var.get():.2f}x", width=50)
        speed_label.grid(row=0, column=1, padx=(10, 0))

        def update_speed_label(val):
            speed_label.configure(text=f"{float(val):.2f}x")

        speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=0.5,
            to=2.0,
            variable=tts_speed_var,
            command=update_speed_label
        )
        speed_slider.grid(row=0, column=0, sticky="ew")

        # Speed description
        speed_desc = ctk.CTkLabel(
            content,
            text="0.5x = slow, 1.0x = normal, 2.0x = fast",
            anchor="w",
            font=("Arial", 10),
            text_color="gray"
        )
        speed_desc.pack(fill="x", pady=(0, 10))

        def save():
            new_hotkey = hotkey_capture.get()
            new_url = url_entry.get()
            new_voice_mode = voice_mode_var.get()
            new_voice_hotkey = voice_hotkey_capture.get()

            settings_manager.set_hotkey(new_hotkey)
            settings_manager.set_webhook_url(new_url)
            settings_manager.set_voice_mode(new_voice_mode)
            settings_manager.set_voice_hotkey(new_voice_hotkey)

            # Save TTS settings
            settings_manager.set_tts_enabled(tts_enabled_var.get())
            settings_manager.set_tts_voice(tts_voice_var.get())
            settings_manager.set_tts_speed(tts_speed_var.get())

            if self.update_hotkey_callback:
                self.update_hotkey_callback(new_hotkey)

            # Update voice hotkey
            self.register_voice_hotkey(new_voice_hotkey)

            self.close_settings()

        save_btn = ctk.CTkButton(
            content,
            text="Save",
            command=save,
            font=("Arial", 14, "bold"),
            height=40
        )
        save_btn.pack(fill="x", pady=20)

    def close_settings(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None

    def show_first_run_setup(self):
        """Show first-time setup wizard for configuring hotkeys."""
        if self.setup_window is not None and self.setup_window.winfo_exists():
            return

        self.setup_window = ctk.CTkToplevel(self)
        self.setup_window.title("Welcome to Helper AI")
        self.setup_window.geometry("450x380")
        self.setup_window.attributes("-topmost", True)
        self.setup_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent closing
        self.setup_window.grab_set()  # Make modal

        # Center the window
        self.setup_window.update_idletasks()
        x = (self.setup_window.winfo_screenwidth() - 450) // 2
        y = (self.setup_window.winfo_screenheight() - 380) // 2
        self.setup_window.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(self.setup_window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=20)

        # Title
        title = ctk.CTkLabel(
            content,
            text="Welcome to Helper AI!",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10))

        # Description
        desc = ctk.CTkLabel(
            content,
            text="Let's set up your hotkeys to get started.\nClick 'Set' and press the key combination you want to use.",
            font=("Arial", 12),
            text_color="gray"
        )
        desc.pack(pady=(0, 20))

        # Overlay Hotkey
        ctk.CTkLabel(content, text="Overlay Hotkey (show/hide this window):", anchor="w").pack(fill="x", pady=(10, 5))
        overlay_hotkey = HotkeyCapture(content, initial_value=settings_manager.get_hotkey())
        overlay_hotkey.pack(fill="x", pady=(0, 15))

        # Voice Hotkey
        ctk.CTkLabel(content, text="Voice Hotkey (start voice input):", anchor="w").pack(fill="x", pady=(10, 5))
        voice_hotkey = HotkeyCapture(content, initial_value=settings_manager.get_voice_hotkey())
        voice_hotkey.pack(fill="x", pady=(0, 20))

        def complete_setup():
            # Save hotkeys
            new_overlay = overlay_hotkey.get()
            new_voice = voice_hotkey.get()

            if new_overlay:
                settings_manager.set_hotkey(new_overlay)
                if self.update_hotkey_callback:
                    self.update_hotkey_callback(new_overlay)

            if new_voice:
                settings_manager.set_voice_hotkey(new_voice)
                self.register_voice_hotkey(new_voice)

            # Mark setup as complete
            settings_manager.set_setup_complete(True)

            # Close setup window
            self.setup_window.grab_release()
            self.setup_window.destroy()
            self.setup_window = None

            # Focus main window
            self.entry.focus_set()

        # Complete button
        complete_btn = ctk.CTkButton(
            content,
            text="Get Started",
            font=("Arial", 14),
            height=40,
            command=complete_setup
        )
        complete_btn.pack(pady=20)

    def show_history(self):
        if self.history_window is not None and self.history_window.winfo_exists():
            self.close_history()
            return

        self.history_window = ctk.CTkToplevel(self)
        self.history_window.title("History")
        
        # Restore saved position or use default
        saved_pos = getattr(self, '_history_pos', None)
        if saved_pos:
            self.history_window.geometry(f"400x500+{saved_pos[0]}+{saved_pos[1]}")
        else:
            self.history_window.geometry("400x500")
            
        self.history_window.attributes("-topmost", True)
        self.history_window.protocol("WM_DELETE_WINDOW", self.close_history)
        
        sessions = settings_manager.get_sessions()
        
        scrollable_frame = ctk.CTkScrollableFrame(self.history_window)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for session in sessions:
            title = session.get("title", "Untitled")
            sid = session.get("id")
            
            row_frame = ctk.CTkFrame(scrollable_frame)
            row_frame.pack(fill="x", pady=2)
            
            # Chat Title Button
            btn = ctk.CTkButton(
                row_frame, 
                text=f"{title[:35]}...", 
                command=lambda s=sid: self.load_session(s, self.history_window),
                anchor="w",
                fg_color="transparent",
                border_width=1,
                text_color=("gray10", "gray90")
            )
            btn.pack(side="left", fill="x", expand=True, padx=2)
            
            # Delete Button
            del_btn = ctk.CTkButton(
                row_frame,
                text="X",
                width=30,
                fg_color="red",
                command=lambda s=sid, w=self.history_window: self.delete_session_ui(s, w)
            )
            del_btn.pack(side="right", padx=2)

    def close_history(self):
        if self.history_window:
            # Save position before closing
            self._history_pos = (self.history_window.winfo_x(), self.history_window.winfo_y())
            self.history_window.destroy()
            self.history_window = None

    def load_session(self, session_id, history_window=None):
        """Load a previous session and display its messages."""
        self.current_session_id = session_id
        self.chat_messages = settings_manager.get_session_messages(session_id)
        self.display_chat()
        self.entry.delete(0, 'end')
        self.entry.focus_set()
        # Close history window
        if history_window and history_window.winfo_exists():
            self.close_history()

    def delete_session_ui(self, session_id, history_window):
        """Delete a session and refresh the history window."""
        settings_manager.delete_session(session_id)
        # If we deleted the current session, reset
        if self.current_session_id == session_id:
            self.new_chat()
        # Refresh history window
        if history_window and history_window.winfo_exists():
            self.close_history()
            self.show_history()


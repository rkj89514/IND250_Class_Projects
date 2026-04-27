import os
import threading
import time
import re
import pyttsx3
import fitz  # PyMuPDF
import customtkinter as ctk
from tkinter import filedialog
import windnd

class PDFReaderApp(ctk.CTk):
    """
    Main Application Class: Manages UI, PDF extraction, and TTS playback.
    """
    def __init__(self):
        super().__init__()
        
        # --- Window Configuration ---
        self.title("Read To Me - PDF Narrator")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        # --- State Management ---
        self.pdf_text_list = []      # List of processed sentences/segments
        self.is_paused = False       
        self.is_stopped = True       
        self.current_idx = 0         
        self.is_seeking = False      
        self.elapsed_seconds = 0     
        self.total_estimated_seconds = 0 

        # --- TTS Voice Initialization ---
        # Query system for available voices
        temp_engine = pyttsx3.init()
        self.voices = temp_engine.getProperty('voices')
        self.selected_voice_id = self.voices[0].id if self.voices else None
        del temp_engine

        # --- Component Bootstrapping ---
        self.setup_ui()
        self.update_ui_loop()        # Syncs UI with playback index every 200ms
        self.start_timer_thread()    # Background clock logic
        
        # Allow files to be dragged directly into the window
        windnd.hook_dropfiles(self, self.handle_drop)

    def setup_ui(self):
        """Builds the sidebar controls and the main text display area."""
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)

        ctk.CTkLabel(self.sidebar, text="READ TO ME", font=("Arial", 22, "bold")).pack(pady=25)
        self.label_file = ctk.CTkLabel(self.sidebar, text="No File Loaded", wraplength=250, text_color="gray")
        self.label_file.pack(pady=10)

        # Buttons
        ctk.CTkButton(self.sidebar, text="📁 Load PDF", command=self.load_pdf).pack(pady=10, padx=20)
        self.btn_play = ctk.CTkButton(self.sidebar, text="▶ Start Reading", command=self.start_speaking)
        self.btn_play.pack(pady=5, padx=20)
        self.btn_pause = ctk.CTkButton(self.sidebar, text="⏸ Pause / Resume", command=self.pause_speaking)
        self.btn_pause.pack(pady=5, padx=20)
        self.btn_stop = ctk.CTkButton(self.sidebar, text="⏹ Stop & Reset", command=self.stop_speaking, fg_color="#a13232")
        self.btn_stop.pack(pady=5, padx=20)

        # Timer & Stats
        self.timer_label = ctk.CTkLabel(self.sidebar, text="00:00 / 00:00", font=("Arial", 16, "bold"))
        self.timer_label.pack(pady=(20, 0))
        self.stats_label = ctk.CTkLabel(self.sidebar, text="Sentence: 0 / 0", font=("Arial", 12))
        self.stats_label.pack(pady=(5, 15))
        
        # Progress Slider
        self.progress_slider = ctk.CTkSlider(self.sidebar, from_=0, to=100, command=self.seek_playback)
        self.progress_slider.set(0)
        self.progress_slider.pack(pady=10, padx=20)

        # Voice & Theme settings
        self.voice_dropdown = ctk.CTkOptionMenu(self.sidebar, values=[v.name for v in self.voices], command=self.change_voice)
        self.voice_dropdown.pack(pady=10, padx=20)
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Light Mode", command=self.toggle_theme)
        self.theme_switch.pack(side="bottom", pady=40)

        # --- Text Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20)
        self.text_display = ctk.CTkTextbox(self.main_frame, font=("Arial", 18), wrap="word", spacing2=10)
        self.text_display.pack(fill="both", expand=True, pady=20)
        
        # Visual highlight configuration
        self.text_display.tag_config("highlight", background="#1f538d", foreground="white")

    def format_time(self, seconds):
        """Converts raw seconds to MM:SS."""
        mins, secs = divmod(int(seconds), 60)
        return f"{mins:02d}:{secs:02d}"

    def update_timer_display(self):
        """Updates the elapsed and total time labels."""
        elapsed = self.format_time(self.elapsed_seconds)
        total = self.format_time(self.total_estimated_seconds)
        self.timer_label.configure(text=f"{elapsed} / {total}")

    def start_timer_thread(self):
        """Runs a background clock to track reading time."""
        def run_timer():
            while True:
                if not self.is_stopped and not self.is_paused:
                    self.elapsed_seconds += 1
                    self.update_timer_display()
                time.sleep(1)
        threading.Thread(target=run_timer, daemon=True).start()

    def update_ui_loop(self):
        """Recursively syncs the UI slider and text highlighting with the current reading index."""
        if self.pdf_text_list and not self.is_stopped:
            self.stats_label.configure(text=f"Sentence: {self.current_idx + 1} / {len(self.pdf_text_list)}")
            if not self.is_seeking:
                self.progress_slider.set(self.current_idx)
                self.highlight_current_sentence()
        self.after(200, self.update_ui_loop)

    def highlight_current_sentence(self):
        """Visually marks the text currently being read."""
        self.text_display.tag_remove("highlight", "1.0", "end")
        if 0 <= self.current_idx < len(self.pdf_text_list):
            target = self.pdf_text_list[self.current_idx].strip()
            if target:
                start_idx = self.text_display.search(target, "1.0", stopindex="end")
                if start_idx:
                    end_idx = f"{start_idx} + {len(target)} chars"
                    self.text_display.tag_add("highlight", start_idx, end_idx)
                    self.text_display.see(start_idx)

    def speak_logic(self):
        """Worker thread for TTS. Handles pauses and engine reset."""
        self.is_stopped = False
        while self.current_idx < len(self.pdf_text_list) and not self.is_stopped:
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            worker = pyttsx3.init()
            worker.setProperty('rate', 165)
            worker.setProperty('voice', self.selected_voice_id)
            
            sentence = self.pdf_text_list[self.current_idx]
            if sentence.strip():
                try:
                    worker.say(sentence)
                    worker.runAndWait()
                    del worker
                    
                    if not self.is_paused and not self.is_stopped:
                        time.sleep(0.4) 
                except Exception:
                    break
            
            if not self.is_paused and not self.is_stopped:
                self.current_idx += 1
        
        if self.current_idx >= len(self.pdf_text_list):
            self.is_stopped = True

    def start_speaking(self):
        """Begins the reading process."""
        if self.is_paused: 
            self.is_paused = False
        elif self.is_stopped and self.pdf_text_list:
            if self.current_idx == 0:
                self.elapsed_seconds = 0
                self.update_timer_display()
            threading.Thread(target=self.speak_logic, daemon=True).start()

    def pause_speaking(self):
        """Toggles pause and cuts current audio."""
        self.is_paused = not self.is_paused
        pyttsx3.init().stop()

    def stop_speaking(self):
        """Resets all playback state."""
        self.is_stopped = True
        self.is_paused = False
        self.current_idx = 0
        self.elapsed_seconds = 0
        self.update_timer_display()
        pyttsx3.init().stop()
        self.text_display.tag_remove("highlight", "1.0", "end")
        self.progress_slider.set(0)

    def seek_playback(self, value):
        """Jumps to a specific sentence in the text."""
        self.is_seeking = True
        self.current_idx = int(value)
        if self.pdf_text_list:
            progress_ratio = self.current_idx / len(self.pdf_text_list)
            self.elapsed_seconds = int(self.total_estimated_seconds * progress_ratio)
            self.update_timer_display()
        pyttsx3.init().stop()
        self.is_seeking = False

    def handle_drop(self, files):
        """Handles drag-and-drop loading."""
        try:
            path = files[0].decode('utf-8')
        except UnicodeDecodeError:
            path = files[0].decode('gbk')
        if path.lower().endswith('.pdf'): 
            self.process_pdf(path)

    def load_pdf(self):
        """Opens file dialog for PDF loading."""
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path: 
            self.process_pdf(path)

    def process_pdf(self, path):
        """Extracts text, cleans it, and identifies Title/Author for early pauses."""
        self.stop_speaking()
        try:
            doc = fitz.open(path)
        except Exception:
            return

        all_lines = []
        full_raw_text = ""
        simple_titles = {"Mr.": "Mister", "Mrs.": "Misses", "Ms.": "Miss", "Dr.": "Doctor"}

        for page in doc:
            page_text = page.get_text()
            full_raw_text += page_text + " "
            for short, full in simple_titles.items():
                page_text = page_text.replace(short, full)
            
            # Sanitization Fix (Backslash and Citations)
            page_text = re.sub(r'\\', '', page_text) 
            page_text = re.sub(r'St\.\s+(?=[A-Z])', 'Saint ', page_text)
            page_text = re.sub(r'St\.', 'Street', page_text)
            page_text = re.sub(r'\', '', page_text, flags=re.IGNORECASE)
            
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            all_lines.extend(lines)

        if not all_lines: 
            return

        # Time Estimation
        words = len(full_raw_text.split())
        base_seconds = (words / 165) * 60
        
        # --- TITLE AND AUTHOR LOGIC RESTORED ---
        # We manually separate the first two lines to ensure a clean pause after Title/Author
        processed_sentences = []
        if len(all_lines) >= 1:
            processed_sentences.append(all_lines[0] + ".") # Treat Line 1 as Title
        if len(all_lines) >= 2:
            processed_sentences.append(all_lines[1] + ".") # Treat Line 2 as Author
        
        # Group the remaining lines and split into sentences
        if len(all_lines) > 2:
            body_text = " ".join(all_lines[2:])
            # Split by punctuation but keep the sentence together
            body_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', body_text) if len(s.strip()) > 2]
            processed_sentences.extend(body_sentences)

        self.total_estimated_seconds = base_seconds + (len(processed_sentences) * 0.4)
        self.pdf_text_list = processed_sentences
        
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", "\n\n".join(processed_sentences))
        self.label_file.configure(text=f"Loaded: {os.path.basename(path)}")
        self.progress_slider.configure(from_=0, to=max(0, len(self.pdf_text_list) - 1))
        self.current_idx = 0
        self.update_timer_display()

    def change_voice(self, choice):
        """Dropdown selector for voice change."""
        for v in self.voices:
            if v.name == choice: 
                self.selected_voice_id = v.id
        pyttsx3.init().stop()

    def toggle_theme(self):
        """Light/Dark mode toggle."""
        ctk.set_appearance_mode("light" if self.theme_switch.get() == 1 else "dark")

if __name__ == "__main__":
    app = PDFReaderApp()
    app.mainloop()

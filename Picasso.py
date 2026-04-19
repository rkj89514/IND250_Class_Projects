import tkinter as tk
from tkinter import colorchooser, messagebox, filedialog, ttk
from PIL import Image, ImageDraw, ImageTk, ImageFont
import math
import random

class Picasso:
    def __init__(self, root):
        self.root = root
        self.root.title("Picasso v23.0 - Geometry Patch")
        self.root.geometry("1550x950")

        self.color_rgb = (0, 0, 0) 
        self.tool = "pen"
        self.history = []
        self.active_layer_idx = 0
        self.cursor_id = None 
        self.temp_id = None
        self.start_x = self.start_y = None
        
        self.width, self.height = 1200, 900
        self.layers = [[Image.new("RGBA", (self.width, self.height), (255, 255, 255, 255)), 1.0]]
        self.draw_buffer = ImageDraw.Draw(self.layers[0][0])
        
        self.setup_ui()
        self.setup_bindings()
        self.refresh_display()

    def setup_ui(self):
        # Top Bar
        self.layer_bar = tk.Frame(self.root, bg="#2c3e50", pady=5)
        self.layer_bar.pack(side=tk.TOP, fill=tk.X)
        self.layer_listbox = tk.Listbox(self.layer_bar, bg="#ecf0f1", height=2, exportselection=False)
        self.layer_listbox.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.layer_listbox.insert(0, "Layer 0 (Background)")
        self.layer_listbox.select_set(0)
        self.layer_listbox.bind("<<ListboxSelect>>", self.on_layer_change)
        tk.Button(self.layer_bar, text="+ Add", command=self.add_layer).pack(side=tk.LEFT, padx=2)
        tk.Button(self.layer_bar, text="- Del", command=self.delete_layer, bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=2)
        self.layer_alpha_slider = tk.Scale(self.layer_bar, from_=0, to=100, orient=tk.HORIZONTAL, label="Opacity %", bg="#2c3e50", fg="white", highlightthickness=0, command=self.update_layer_opacity)
        self.layer_alpha_slider.set(100); self.layer_alpha_slider.pack(side=tk.LEFT, padx=20)

        # Left Sidebar
        self.left_sidebar = tk.Frame(self.root, bg="#34495e", width=200, padx=10, pady=10)
        self.left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        def add_label(text): tk.Label(self.left_sidebar, text=text, bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(pady=(10, 2))
        
        add_label("TOOLS")
        for text, mode in [("🖊️ Pen", "pen"), ("🧽 Eraser", "eraser"), ("🪣 Fill", "fill"), ("T Text", "text")]:
            tk.Button(self.left_sidebar, text=text, command=lambda m=mode: self.set_tool(m), width=18).pack(pady=2)

        add_label("BRUSH")
        self.style_var = tk.StringVar(value="solid")
        for text, mode in [("Solid", "solid"), ("Charcoal", "charcoal"), ("Spray", "spray")]:
            tk.Radiobutton(self.left_sidebar, text=text, variable=self.style_var, value=mode, bg="#34495e", fg="white", selectcolor="#2c3e50").pack(anchor=tk.W)

        add_label("SHAPES")
        self.shape_var = tk.StringVar(value="square")
        self.shape_menu = ttk.Combobox(self.left_sidebar, textvariable=self.shape_var, state="readonly", width=17)
        self.shape_menu['values'] = ("square", "circle", "triangle", "star", "line")
        self.shape_menu.pack(pady=2)
        self.shape_menu.bind("<<ComboboxSelected>>", lambda e: self.set_tool(self.shape_var.get()))

        add_label("SIZE")
        self.width_slider = tk.Scale(self.left_sidebar, from_=1, to=100, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0)
        self.width_slider.set(10); self.width_slider.pack(fill=tk.X)

        add_label("ACTIONS")
        tk.Button(self.left_sidebar, text="🎨 Color", command=self.pick_color, width=18).pack(pady=2)
        tk.Button(self.left_sidebar, text="↩️ Undo", command=self.undo, width=18).pack(pady=2)
        tk.Button(self.left_sidebar, text="💾 Save", bg="#27ae60", fg="white", command=self.save_file, width=18).pack(pady=10)

        self.canvas = tk.Canvas(self.root, bg="#bdc3c7", highlightthickness=0, cursor="none")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # --- Shape Math ---
    def get_star_pts(self, x0, y0, x1, y1):
        pts = []; cx, cy = (x0+x1)/2, (y0+y1)/2; out_r = max(abs(x1-x0)/2, 2); in_r = out_r/2.5
        for i in range(10):
            angle = math.radians(i*36-90); r = out_r if i%2==0 else in_r
            pts.append((cx+r*math.cos(angle), cy+r*math.sin(angle)))
        return pts

    def get_tri_pts(self, x0, y0, x1, y1):
        """Calculates vertices for an isosceles triangle within the selection box."""
        return [(x0 + (x1 - x0) / 2, y0), (x0, y1), (x1, y1)]

    # --- Interaction ---
    def on_draw(self, event):
        if self.start_x is None: return
        self.update_cursor(event)
        if self.tool in ["pen", "eraser"]:
            dist = math.hypot(event.x - self.start_x, event.y - self.start_y)
            steps = int(dist / 2) + 1
            for i in range(steps):
                tx = self.start_x + (event.x - self.start_x) * (i / steps)
                ty = self.start_y + (event.y - self.start_y) * (i / steps)
                self.paint_dab(tx, ty)
            self.start_x, self.start_y = event.x, event.y
            self.refresh_display()
        else:
            if self.temp_id: self.canvas.delete(self.temp_id)
            rgb_hex = '#%02x%02x%02x' % self.color_rgb
            w = self.width_slider.get()
            if self.tool == "square": self.temp_id = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline=rgb_hex, width=w)
            elif self.tool == "circle": self.temp_id = self.canvas.create_oval(self.start_x, self.start_y, event.x, event.y, outline=rgb_hex, width=w)
            elif self.tool == "line": self.temp_id = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, fill=rgb_hex, width=w)
            elif self.tool == "star": self.temp_id = self.canvas.create_polygon(self.get_star_pts(self.start_x, self.start_y, event.x, event.y), outline=rgb_hex, fill="", width=w)
            elif self.tool == "triangle": self.temp_id = self.canvas.create_polygon(self.get_tri_pts(self.start_x, self.start_y, event.x, event.y), outline=rgb_hex, fill="", width=w)

    def on_release(self, event):
        if self.start_x is None or self.tool in ["pen", "eraser", "text", "fill"]: return
        w, color = self.width_slider.get(), self.color_rgb + (255,)
        if self.tool == "square": self.draw_buffer.rectangle([self.start_x, self.start_y, event.x, event.y], outline=color, width=w)
        elif self.tool == "circle": self.draw_buffer.ellipse([self.start_x, self.start_y, event.x, event.y], outline=color, width=w)
        elif self.tool == "line": self.draw_buffer.line([self.start_x, self.start_y, event.x, event.y], fill=color, width=w)
        elif self.tool == "star": self.draw_buffer.polygon(self.get_star_pts(self.start_x, self.start_y, event.x, event.y), outline=color, width=w)
        elif self.tool == "triangle": self.draw_buffer.polygon(self.get_tri_pts(self.start_x, self.start_y, event.x, event.y), outline=color, width=w)
        self.start_x = self.start_y = self.temp_id = None
        self.refresh_display()

    # --- Core Logic ---
    def paint_dab(self, x, y):
        w, alpha = self.width_slider.get(), 255
        color = (0, 0, 0, 0) if self.tool == "eraser" else self.color_rgb + (alpha,)
        style = self.style_var.get()
        if style == "solid" or self.tool == "eraser":
            self.draw_buffer.ellipse([x-w/2, y-w/2, x+w/2, y+w/2], fill=color)
        elif style == "charcoal":
            for _ in range(int(w)):
                rx, ry = x + random.uniform(-w/2, w/2), y + random.uniform(-w/2, w/2)
                self.draw_buffer.point((rx, ry), fill=color)
        elif style == "spray":
            for _ in range(int(w/3)):
                rx, ry = x + random.gauss(0, w/2), y + random.gauss(0, w/2)
                self.draw_buffer.point((rx, ry), fill=color)

    def on_press(self, event):
        if self.tool == "text": self.place_text(event); return
        self.save_history()
        self.start_x, self.start_y = event.x, event.y
        if self.tool in ["pen", "eraser"]: self.paint_dab(event.x, event.y); self.refresh_display()
        elif self.tool == "fill":
            ImageDraw.floodfill(self.layers[self.active_layer_idx][0], (event.x, event.y), self.color_rgb + (255,))
            self.refresh_display()

    def undo(self):
        if self.history:
            idx, img = self.history.pop()
            self.layers[idx][0] = img
            self.active_layer_idx = idx
            self.draw_buffer = ImageDraw.Draw(self.layers[self.active_layer_idx][0])
            self.refresh_display()

    def refresh_display(self):
        final = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 255))
        for img, opacity in self.layers:
            if opacity < 1.0:
                item = img.copy(); alpha = item.getchannel('A').point(lambda p: p * opacity); item.putalpha(alpha)
                final.alpha_composite(item)
            else: final.alpha_composite(img)
        self.tk_img = ImageTk.PhotoImage(final)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_img, anchor=tk.NW)

    def on_layer_change(self, e): 
        sel = self.layer_listbox.curselection()
        if sel: 
            self.active_layer_idx = sel[0]
            self.draw_buffer = ImageDraw.Draw(self.layers[self.active_layer_idx][0])

    def add_layer(self): 
        self.layers.append([Image.new("RGBA", (self.width, self.height), (0,0,0,0)), 1.0])
        self.layer_listbox.insert(tk.END, f"Layer {len(self.layers)-1}")
        self.layer_listbox.select_clear(0, tk.END); self.layer_listbox.select_set(tk.END)
        self.on_layer_change(None)

    def delete_layer(self):
        if self.active_layer_idx == 0: return
        self.layers.pop(self.active_layer_idx); self.layer_listbox.delete(self.active_layer_idx)
        self.active_layer_idx = 0; self.layer_listbox.select_set(0); self.on_layer_change(None); self.refresh_display()

    def update_layer_opacity(self, v): self.layers[self.active_layer_idx][1] = int(v)/100.0; self.refresh_display()

    def place_text(self, event):
        self.text_entry = tk.Entry(self.canvas, font=("Arial", 36), fg='#%02x%02x%02x' % self.color_rgb, bg="white", borderwidth=0)
        self.canvas.create_window(event.x, event.y, window=self.text_entry, anchor="nw")
        self.text_entry.focus_set()
        self.text_entry.bind("<Return>", lambda e: self.finalize_text(event.x, event.y))

    def finalize_text(self, x, y):
        txt = self.text_entry.get()
        if txt:
            self.draw_buffer.text((x, y), txt, fill=self.color_rgb + (255,))
            self.refresh_display()
        self.text_entry.destroy()

    def update_cursor(self, event):
        if self.cursor_id: self.canvas.delete(self.cursor_id)
        r = self.width_slider.get() / 2
        self.cursor_id = self.canvas.create_oval(event.x-r, event.y-r, event.x+r, event.y+r, outline="black")

    def setup_bindings(self):
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_draw)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.update_cursor)

    def set_tool(self, mode): self.tool = mode
    def pick_color(self):
        c = colorchooser.askcolor()[1]
        if c: r,g,b = self.root.winfo_rgb(c); self.color_rgb = (r//256, g//256, b//256)
    def save_history(self):
        self.history.append((self.active_layer_idx, self.layers[self.active_layer_idx][0].copy()))
        if len(self.history) > 20: self.history.pop(0)
    def save_file(self):
        f = filedialog.asksaveasfilename(defaultextension=".png")
        if f:
            save_img = Image.new("RGB", (self.width, self.height), (255, 255, 255))
            for img, _ in self.layers: save_img.paste(img, (0,0), img)
            save_img.save(f)

if __name__ == "__main__":
    root = tk.Tk(); app = Picasso(root); root.mainloop()

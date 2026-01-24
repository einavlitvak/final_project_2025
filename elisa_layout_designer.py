import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import string
import copy

# Configuration
COLS = 8
ROWS = 12
CELL_SIZE = 50
MARGIN = 60
WIN_WIDTH = COLS * CELL_SIZE + 2 * MARGIN
WIN_HEIGHT = ROWS * CELL_SIZE + 2 * MARGIN

COL_LABELS = [chr(i) for i in range(ord('A'), ord('A') + COLS)]
ROW_LABELS = [str(i + 1) for i in range(ROWS)]

CALIBRATION_CONCS = [6.4, 3.2, 1.6, 0.8, 0.4, 0.2, 0.1, 0.0]

# Pastel Palette for Experiments
EXP_PALETTE = [
    "#ccffcc", # Green
    "#ccccff", # Blue
    "#ffffcc", # Yellow
    "#ffccff", # Pink
    "#ccffff", # Cyan
    "#ffeebb", # Orange-ish
]

class ElisaPlateDesigner:
    def __init__(self, root):
        self.root = root
        self.root.title("ELISA Plate Designer")
        
        # Data Structure: (col, row) -> dict
        # { 'type': 'CAL' or 'EXP', 'exp': int, 'subj': int, 'samp': int, 'rep': int, 'conc': float/None }
        self.grid_data = {}
        
        # State
        self.history = []
        self.current_exp = 1
        self.current_subj = 1
        self.next_sample_id = 0 # Next sample ID for the current subject (t0)
        self.subject_closed = False # Triggered by Space
        self.orientation = 'vertical' # 'vertical' or 'horizontal'
        
        # Sidebar State
        self.subject_names = {} # (exp, subj) -> StringVar
        self.sidebar_widgets = {} # (exp, subj) -> Frame
        self.exp_headers = {} # exp -> Label
        
        # Selection
        self.start_sel = None
        self.cur_sel = None
        
        self._init_grid_data()
        self._init_ui()
        self.update_status()

    def _init_grid_data(self):
        # Initialize calibration rows (0 and 1)
        # Cols A(0) -> H(7) map to concentrations
        for r in [0, 1]:
            for c in range(COLS):
                self.grid_data[(c, r)] = {
                    'type': 'CAL',
                    'conc': CALIBRATION_CONCS[c],
                    'id_str': f"Cal {CALIBRATION_CONCS[c]}"
                }

    def _init_ui(self):
        # Main Layout
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left Panel: Canvas
        left_panel = tk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(left_panel, width=WIN_WIDTH, height=WIN_HEIGHT, bg='white')
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Right Panel: Sidebar
        right_panel = tk.Frame(main_frame, width=300, bg="#f0f0f0")
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False) # Enforce width
        
        tk.Label(right_panel, text="Subject List", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        
        # Scrollable Sidebar Area
        self.sidebar_canvas = tk.Canvas(right_panel, bg="#f0f0f0")
        scrollbar = tk.Scrollbar(right_panel, orient="vertical", command=self.sidebar_canvas.yview)
        self.sidebar_inner = tk.Frame(self.sidebar_canvas, bg="#f0f0f0")
        
        self.sidebar_inner.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
        )
        
        self.sidebar_window = self.sidebar_canvas.create_window((0, 0), window=self.sidebar_inner, anchor="nw")
        
        # Make inner frame fill width of canvas
        def configure_window(event):
            self.sidebar_canvas.itemconfig(self.sidebar_window, width=event.width)
        self.sidebar_canvas.bind("<Configure>", configure_window)

        self.sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Status Bar
        self.lbl_status = tk.Label(self.root, text="Ready", font=("Arial", 10), anchor="w", padx=10)
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bindings
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.root.bind("<space>", self.on_space)
        self.root.bind("e", self.on_e)
        self.root.bind("r", self.on_r)
        self.root.bind("<Control-z>", self.on_undo)
        
        # Generate Menu
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Export PNG", command=self.export_png)
        filemenu.add_command(label="Export CSV", command=self.export_csv)
        filemenu.add_command(label="Import CSV", command=self.import_csv)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)
        
        self.draw_grid()

    def refresh_sidebar(self):
        # Identify current unique subjects
        current_subjs = set()
        for cell in self.grid_data.values():
            if cell['type'] == 'EXP':
                current_subjs.add((cell['exp'], cell['subj']))
        
        sorted_subjs = sorted(list(current_subjs))
        
        # 1. Clean up removed subjects
        to_remove = []
        for key in self.sidebar_widgets:
            if key not in current_subjs:
                to_remove.append(key)
        
        for key in to_remove:
            widget = self.sidebar_widgets.pop(key)
            widget.destroy()
            # Clean up name data? No, keep it in case of Redo/re-add, 
            # or clean if truly gone. Let's keep data in subject_names for now.

        # 2. Add new subjects
        # We need to maintain order: Exp 1 (Header) -> S1, S2... Exp 2 (Header) -> S1...
        
        # To do this correctly with headers, we might need to repack everything 
        # or use grid with calculated rows.
        # Simplest approach: Clear all and rebuild is easiest but loses focus if typing.
        # Hybrid: Grid layout.
        
        # Let's organize by Experiment
        grouped = {}
        for exp, subj in sorted_subjs:
            if exp not in grouped: grouped[exp] = []
            grouped[exp].append(subj)
            
        # Clear inner frame and rebuild (it's fast enough for this scale)
        # To preserve focus/text, we keep the StringVars (self.subject_names)
        
        for widget in self.sidebar_inner.winfo_children():
            widget.destroy()
            
        row_idx = 0
        for exp in sorted(grouped.keys()):
            # Experiment Header
            header = tk.Label(self.sidebar_inner, text=f"Experiment {exp}", 
                             font=("Arial", 10, "bold"), bg="#ddd", anchor="w")
            header.pack(fill=tk.X, padx=5, pady=(10, 2))
            
            # Subjects
            for subj in sorted(grouped[exp]):
                key = (exp, subj)
                if key not in self.subject_names:
                    self.subject_names[key] = tk.StringVar()
                
                # Add trace to auto-update grid when name changes
                # Only add if not already added? trace persists on the variable.
                # Since we check 'if key not in', we only create it once.
                # But wait, we destroyed widgets but kept StringVars. 
                # If we create a new StringVar every time, we lose data.
                # We are NOT creating new StringVars if they exist.
                # So we should ensure trace is added only once or just lazily.
                # Actually, trace triggers are fine.
                
                # If we rely on existing StringVar, we don't need to add trace again if it's there.
                # But implementation above: `if key not in ... self.subject_names[key] = ...`
                # So we only init once.
                
                if not self.subject_names[key].trace_info():
                     self.subject_names[key].trace_add("write", lambda *args: self.draw_grid())

                f = tk.Frame(self.sidebar_inner, bg="#f0f0f0")
                f.pack(fill=tk.X, padx=10, pady=2)
                
                lbl = tk.Label(f, text=f"S{subj}:", width=5, anchor="w", bg="#f0f0f0")
                lbl.pack(side=tk.LEFT)
                
                entry = tk.Entry(f, textvariable=self.subject_names[key])
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def draw_grid(self):
        self.canvas.delete("all")
        
        # Draw Labels
        for c in range(COLS):
            x = MARGIN + c * CELL_SIZE + CELL_SIZE / 2
            self.canvas.create_text(x, MARGIN / 2, text=COL_LABELS[c], font=("Arial", 12, "bold"))
            
        for r in range(ROWS):
            y = MARGIN + r * CELL_SIZE + CELL_SIZE / 2
            self.canvas.create_text(MARGIN / 2, y, text=ROW_LABELS[r], font=("Arial", 12, "bold"))

        # Draw Cells
        for r in range(ROWS):
            for c in range(COLS):
                x1 = MARGIN + c * CELL_SIZE
                y1 = MARGIN + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                
                cell = self.grid_data.get((c, r))
                
                fill_color = "white"
                text = ""
                outline_color = "lightgray"
                width = 1
                
                if cell:
                    if cell['type'] == 'CAL':
                        fill_color = "#ffcccc" # Light red for Cal
                        text = f"{cell['conc']}"
                        outline_color = "#ff8888"
                    elif cell['type'] == 'EXP':
                        # Cycle colors based on Experiment ID
                        color_idx = (cell['exp'] - 1) % len(EXP_PALETTE)
                        fill_color = EXP_PALETTE[color_idx]
                        
                        # Get Name
                        s_name = self.subject_names.get((cell['exp'], cell['subj']), tk.StringVar()).get()
                        if not s_name: s_name = f"S{cell['subj']}"
                        
                        text = f"{s_name}\nt{cell['samp']}"
                        outline_color = "gray"
                
                # Selection Highlight
                if self.cur_sel:
                    c1, r1, c2, r2 = self.cur_sel
                    if c1 <= c <= c2 and r1 <= r <= r2:
                        fill_color = "#e0e0e0" # Neutral highlight during drag
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=outline_color, width=width)
                if text:
                     self.canvas.create_text(x1+CELL_SIZE/2, y1+CELL_SIZE/2, text=text, font=("Arial", 8))

        # Draw Subject Borders and Replicate Lines
        self.draw_overlays()

    def draw_overlays(self):
        # We need to draw borders around contiguous blocks of the same Subject AND Experiment
        
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.grid_data.get((c, r))
                if not cell or cell['type'] != 'EXP':
                    continue
                
                x1 = MARGIN + c * CELL_SIZE
                y1 = MARGIN + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                
                # Check neighbors
                # Helper to check if neighbor is "different" (different Exp or different Subj)
                def is_different(neighbor):
                    if not neighbor: return True
                    if neighbor['type'] != 'EXP': return True
                    if neighbor['exp'] != cell['exp']: return True
                    if neighbor['subj'] != cell['subj']: return True
                    return False

                # Top
                top = self.grid_data.get((c, r-1))
                if is_different(top):
                     self.canvas.create_line(x1, y1, x2, y1, width=3, fill="black")
                # Bottom
                bot = self.grid_data.get((c, r+1))
                if is_different(bot):
                     self.canvas.create_line(x1, y2, x2, y2, width=3, fill="black")
                # Left
                left = self.grid_data.get((c-1, r))
                if is_different(left):
                     self.canvas.create_line(x1, y1, x1, y2, width=3, fill="black")
                # Right
                right = self.grid_data.get((c+1, r))
                if is_different(right):
                     self.canvas.create_line(x2, y1, x2, y2, width=3, fill="black")


        # 2. Replicate Lines
        # Connect R1 to R2, R2 to R3 etc within same Sample
        # We iterate over all cells, find their next replicate
        # Wait, simple approach: check neighbors. If same Sample, draw line between centers.
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.grid_data.get((c, r))
                if not cell or cell['type'] != 'EXP':
                    continue
                
                cx = MARGIN + c * CELL_SIZE + CELL_SIZE / 2
                cy = MARGIN + r * CELL_SIZE + CELL_SIZE / 2
                
                # Check right (Horizontal Reps)
                right = self.grid_data.get((c+1, r))
                if (right and right.get('type') == 'EXP' and 
                    right.get('exp') == cell['exp'] and 
                    right.get('subj') == cell['subj'] and 
                    right.get('samp') == cell['samp']):
                    n_cx = MARGIN + (c+1) * CELL_SIZE + CELL_SIZE / 2
                    self.canvas.create_line(cx, cy, n_cx, cy, width=2, fill="blue")
                
                # Check down (Vertical Reps)
                down = self.grid_data.get((c, r+1))
                if (down and down.get('type') == 'EXP' and 
                    down.get('exp') == cell['exp'] and 
                    down.get('subj') == cell['subj'] and 
                    down.get('samp') == cell['samp']):
                    n_cy = MARGIN + (r+1) * CELL_SIZE + CELL_SIZE / 2
                    self.canvas.create_line(cx, cy, cx, n_cy, width=2, fill="blue")


    def get_cell_coords(self, event):
        x = event.x - MARGIN
        y = event.y - MARGIN
        c = int(x / CELL_SIZE)
        r = int(y / CELL_SIZE)
        if 0 <= c < COLS and 0 <= r < ROWS:
            return c, r
        return None

    def on_press(self, event):
        coords = self.get_cell_coords(event)
        if coords:
            self.start_sel = coords
            self.cur_sel = (coords[0], coords[1], coords[0], coords[1])
            self.draw_grid()

    def on_drag(self, event):
        if not self.start_sel: return
        coords = self.get_cell_coords(event)
        if coords:
            c1 = min(self.start_sel[0], coords[0])
            r1 = min(self.start_sel[1], coords[1])
            c2 = max(self.start_sel[0], coords[0])
            r2 = max(self.start_sel[1], coords[1])
            self.cur_sel = (c1, r1, c2, r2)
            self.draw_grid()

    def on_release(self, event):
        if self.cur_sel:
            self.save_state()
            self.apply_selection()
            self.refresh_sidebar() # Update list
            self.cur_sel = None
            self.start_sel = None
            self.draw_grid()
            self.update_status()

    def save_state(self):
        # Deep copy grid_data, restore variables
        # Note: We probably shouldn't undo subject names logic here, 
        # but if we undo a subject creation, the name field should eventually disappear.
        state = {
            'grid': copy.deepcopy(self.grid_data),
            'exp': self.current_exp,
            'subj': self.current_subj,
            'samp': self.next_sample_id,
            'subj_closed': self.subject_closed
        }
        self.history.append(state)

    def on_undo(self, event=None):
        if self.history:
            state = self.history.pop()
            self.grid_data = state['grid']
            self.current_exp = state['exp']
            self.current_subj = state['subj']
            self.next_sample_id = state['samp']
            self.subject_closed = state['subj_closed']
            self.draw_grid()
            self.update_status()
            self.refresh_sidebar() # Update list

    def apply_selection(self):
        c1, r1, c2, r2 = self.cur_sel
        
        # Validate: Don't overwrite Calibration (Rows 0-1)
        if r1 < 2:
            messagebox.showwarning("Invalid Selection", "Cannot overwrite calibration rows (1-2).")
            # If selection overlaps, we could trim, but simple rejection is safer
            return

        # Check subject closure logic
        if self.subject_closed:
            self.current_subj += 1
            self.next_sample_id = 0
            self.subject_closed = False

        # Fill Logic
        # Experiment ID: self.current_exp
        # Subject ID: self.current_subj
        
        cells_to_fill = []
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                cells_to_fill.append((c, r))

        if not cells_to_fill: return

        # Strategy:
        # vertical mode: Unique samples vary by COLUMN.
        #                Replicates vary by ROW within column.
        # horizontal mode: Unique samples vary by ROW.
        #                  Replicates vary by COLUMN within row.
        
        # We need to map (c, r) -> (sample_offset, replicate_offset)
        # origin (c1, r1)
        
        # However, what if selection is non-uniform? It is a rect.
        
        if self.orientation == 'vertical':
            # Cols define samples, Rows define replicates
            for c in range(c1, c2 + 1):
                # New Sample
                s_id = self.next_sample_id
                self.next_sample_id += 1
                
                rep_count = 1
                for r in range(r1, r2 + 1):
                   self.grid_data[(c, r)] = {
                        'type': 'EXP',
                        'exp': self.current_exp,
                        'subj': self.current_subj,
                        'samp': s_id,
                        'rep': rep_count
                   }
                   rep_count += 1
        
        else: # horizontal
            # Rows define samples, Cols define replicates
            for r in range(r1, r2 + 1):
                # New Sample
                s_id = self.next_sample_id
                self.next_sample_id += 1
                
                rep_count = 1
                for c in range(c1, c2 + 1):
                    self.grid_data[(c, r)] = {
                        'type': 'EXP',
                        'exp': self.current_exp,
                        'subj': self.current_subj,
                        'samp': s_id,
                        'rep': rep_count
                   }
                    rep_count += 1

    def on_space(self, event):
        self.subject_closed = True
        self.update_status()
    
    def on_e(self, event):
        self.save_state()
        self.current_exp += 1
        self.next_sample_id = 0
        # Subject logic: Spec says "next subjects will be part of the next experiment".
        # Does subject ID reset? Usually yes.
        self.current_subj = 1
        self.subject_closed = False # Reset flag for clean start
        self.update_status()

    def on_r(self, event):
        self.orientation = 'horizontal' if self.orientation == 'vertical' else 'vertical'
        self.update_status()

    def update_status(self):
        orientation_sym = "||" if self.orientation == 'vertical' else "="
        
        status = f"Exp: {self.current_exp} | Subject: {self.current_subj} | Mode: {self.orientation} {orientation_sym}"
        if self.subject_closed:
            status += " | SUBJ CLOSED (Next drag -> New Subj)"
            
        status += "   [Space]: Close Subj | [E]: Close Exp | [R]: Rotate | [Ctrl+Z]: Undo"
        self.lbl_status.config(text=status)

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not filename: return
        
        data_rows = []
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.grid_data.get((c, r))
                row_label = ROW_LABELS[r]
                col_label = COL_LABELS[c]
                well_id = f"{col_label}{row_label}"
                
                if cell:
                    c_type = cell['type']
                    if c_type == 'CAL':
                        data_rows.append({
                            'Well': well_id, 'Type': 'Calibration', 
                            'Concentration': cell['conc'], 
                            'Experiment': '', 'Subject': '', 'Sample': '', 'Replicate': '',
                            'Subject Name': ''
                        })
                    else:
                        exp = cell['exp']
                        subj = cell['subj']
                        subj_name = self.subject_names.get((exp, subj), tk.StringVar()).get()
                        
                        data_rows.append({
                            'Well': well_id, 'Type': 'Experiment',
                            'Concentration': '',
                            'Experiment': exp,
                            'Subject': subj,
                            'Sample': cell['samp'],
                            'Replicate': cell['rep'],
                            'Subject Name': subj_name
                        })
                else:
                    data_rows.append({
                        'Well': well_id, 'Type': 'Empty', 
                        'Concentration': '', 'Experiment': '', 'Subject': '', 'Sample': '', 'Replicate': '',
                        'Subject Name': ''
                    })
        
        df = pd.DataFrame(data_rows)
        df.to_csv(filename, index=False)
        messagebox.showinfo("Success", f"Exported to {filename}")

    def import_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not filename: return
        
        try:
            df = pd.read_csv(filename)
            self.save_state()
            self.grid_data = {}
            self.subject_names = {} # clear names
            
            # Reset counters based on Max values found
            max_exp = 0
            
            # Rebuild grid
            for _, row in df.iterrows():
                # Well -> (c, r)
                well = row['Well']
                
                col_char = well[0]
                row_str = well[1:]
                c = ord(col_char) - ord('A')
                r = int(row_str) - 1
                
                if 0 <= c < COLS and 0 <= r < ROWS:
                    t = row['Type']
                    if t == 'Calibration':
                        self.grid_data[(c, r)] = {
                            'type': 'CAL',
                            'conc': row['Concentration']
                        }
                    elif t == 'Experiment':
                         exp = int(row['Experiment'])
                         subj = int(row['Subject'])
                         samp = int(row['Sample'])
                         rep = int(row['Replicate'])
                         
                         # Check for name
                         name = str(row.get('Subject Name', ''))
                         if name == 'nan': name = ''
                         
                         if (exp, subj) not in self.subject_names:
                             v = tk.StringVar(value=name)
                             self.subject_names[(exp, subj)] = v
                         
                         self.grid_data[(c, r)] = {
                             'type': 'EXP',
                             'exp': exp,
                             'subj': subj,
                             'samp': samp,
                             'rep': rep
                         }
                         if exp > max_exp: max_exp = exp
            
            # Restore state vars
            self.current_exp = max(1, max_exp)
            max_subj_in_curr = 0
            max_samp_in_curr_subj = 0
            
            for cell in self.grid_data.values():
                if cell.get('type') == 'EXP' and cell['exp'] == self.current_exp:
                    if cell['subj'] > max_subj_in_curr:
                        max_subj_in_curr = cell['subj']
            # Find max sample in the max subject
            for cell in self.grid_data.values():
                 if cell.get('type') == 'EXP' and cell['exp'] == self.current_exp and cell['subj'] == max_subj_in_curr:
                     if cell['samp'] > max_samp_in_curr_subj:
                         max_samp_in_curr_subj = cell['samp']

            self.current_subj = max_subj_in_curr if max_subj_in_curr > 0 else 1
            # If nothing imported logic might differ, 
            # but if we imported data, we want next sample to be +1 of max.
            # If no data for this subject, start at 0.
            # We must verify if max_samp_in_curr_subj is truly "set".
            # Initial max_samp_in_curr_subj = 0.
            # If data exists: e.g. t0, t1. Max is 1. Next should be 2.
            # If data exists: t0. Max is 0. Next should be 1.
            # If NO data: Max is 0 (default). Next should be 0.
            
            # Count cells for this subject
            count_subj_cells = 0
            for cell in self.grid_data.values():
                 if cell.get('type') == 'EXP' and cell['exp'] == self.current_exp and cell['subj'] == max_subj_in_curr:
                     count_subj_cells += 1
            
            if count_subj_cells > 0:
                self.next_sample_id = max_samp_in_curr_subj + 1
            else:
                self.next_sample_id = 0
            
            self.draw_grid()
            self.refresh_sidebar()
            self.update_status()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {e}")

    def export_png(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not filename: return

        # Create Image
        img_width = WIN_WIDTH
        img_height = WIN_HEIGHT
        img = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(img)
        
        # Load Fonts (Default simple)
        try:
            font = ImageFont.truetype("arial.ttf", 15)
            small_font = ImageFont.truetype("arial.ttf", 10)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw Labels
        for c in range(COLS):
            x = MARGIN + c * CELL_SIZE + CELL_SIZE / 2
            draw.text((x, MARGIN / 2), COL_LABELS[c], fill="black", font=font, anchor="mm")
            
        for r in range(ROWS):
            y = MARGIN + r * CELL_SIZE + CELL_SIZE / 2
            draw.text((MARGIN / 2, y), ROW_LABELS[r], fill="black", font=font, anchor="mm")
            
        # Draw Grid
        for r in range(ROWS):
            for c in range(COLS):
                x1 = MARGIN + c * CELL_SIZE
                y1 = MARGIN + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                
                cell = self.grid_data.get((c, r))
                
                fill_color = "white"
                outline_color = "lightgray"
                text = ""
                
                if cell:
                    if cell['type'] == 'CAL':
                        fill_color = "#ffcccc"
                        text = f"{cell['conc']}"
                        outline_color = "#ff8888"
                    elif cell['type'] == 'EXP':
                        color_idx = (cell['exp'] - 1) % len(EXP_PALETTE)
                        fill_color = EXP_PALETTE[color_idx]
                        
                        # Get Name
                        s_name = self.subject_names.get((cell['exp'], cell['subj']), tk.StringVar()).get()
                        if not s_name: s_name = f"S{cell['subj']}"
                        
                        text = f"{s_name}\nt{cell['samp']}"
                        outline_color = "gray"
                
                draw.rectangle([x1, y1, x2, y2], fill=fill_color, outline=outline_color)
                if text:
                    draw.text((x1+CELL_SIZE/2, y1+CELL_SIZE/2), text, fill="black", font=small_font, anchor="mm")

        # Draw Borders (Subject/Experiment Delimiter)
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.grid_data.get((c, r))
                if not cell or cell['type'] != 'EXP':
                    continue
                
                x1 = MARGIN + c * CELL_SIZE
                y1 = MARGIN + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                # Helper to check if neighbor is "different" (different Exp or different Subj)
                def is_different_img(neighbor):
                    if not neighbor: return True
                    if neighbor['type'] != 'EXP': return True
                    if neighbor['exp'] != cell['exp']: return True
                    if neighbor['subj'] != cell['subj']: return True
                    return False
                
                # Check neighbors and draw lines
                # Top
                top = self.grid_data.get((c, r-1))
                if is_different_img(top):
                    draw.line([x1, y1, x2, y1], fill="black", width=3)
                # Bottom
                bot = self.grid_data.get((c, r+1))
                if is_different_img(bot):
                    draw.line([x1, y2, x2, y2], fill="black", width=3)
                # Left
                left = self.grid_data.get((c-1, r))
                if is_different_img(left):
                    draw.line([x1, y1, x1, y2], fill="black", width=3)
                # Right
                right = self.grid_data.get((c+1, r))
                if is_different_img(right):
                    draw.line([x2, y1, x2, y2], fill="black", width=3)
        
        # Draw Replicate Lines
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.grid_data.get((c, r))
                if not cell or cell['type'] != 'EXP':
                    continue
                
                cx = MARGIN + c * CELL_SIZE + CELL_SIZE / 2
                cy = MARGIN + r * CELL_SIZE + CELL_SIZE / 2
                
                # Right
                right = self.grid_data.get((c+1, r))
                if (right and right.get('type') == 'EXP' and 
                    right.get('exp') == cell['exp'] and 
                    right.get('subj') == cell['subj'] and 
                    right.get('samp') == cell['samp']):
                    n_cx = MARGIN + (c+1) * CELL_SIZE + CELL_SIZE / 2
                    draw.line([cx, cy, n_cx, cy], fill="blue", width=2)
                
                # Down
                down = self.grid_data.get((c, r+1))
                if (down and down.get('type') == 'EXP' and 
                    down.get('exp') == cell['exp'] and 
                    down.get('subj') == cell['subj'] and 
                    down.get('samp') == cell['samp']):
                    n_cy = MARGIN + (r+1) * CELL_SIZE + CELL_SIZE / 2
                    draw.line([cx, cy, cx, n_cy], fill="blue", width=2)
        
        img.save(filename)
        messagebox.showinfo("Success", f"Exported to {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ElisaPlateDesigner(root)
    root.mainloop()

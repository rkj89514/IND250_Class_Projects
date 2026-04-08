"""
A Modern Tip Calculator App
Calculates the tip, total bill, and split amount automatically as values change.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class TipCalculatorApp:
    """Main application class for the Tip Calculator."""

    def __init__(self, root):
        self.root = root
        self.root.title("Modern Tip Calculator")
        self.root.geometry("400x450")
        
        # Applies a modern theme
        self.style = ttk.Style("flatly")

        # --- Tkinter Variables ---
        # These special variables allow us to "track" changes. 
        # When the user types or clicks, these variables update automatically.
        self.bill_amount_var = tk.StringVar(value="")
        self.tip_percent_var = tk.DoubleVar(value=0.15)  # Default to 15%
        self.num_diners_var = tk.IntVar(value=1)         # Default to 1 diner

        # --- Triggers (Event Binding) ---
        # "trace_add" tells Python to run the 'calculate_totals' function 
        # any time the value in these variables is written to ("write").
        self.bill_amount_var.trace_add("write", self.calculate_totals)
        self.tip_percent_var.trace_add("write", self.calculate_totals)
        self.num_diners_var.trace_add("write", self.calculate_totals)

        # Build the user interface
        self.create_widgets()
        
        # Run the initial calculation just to set the labels to $0.00
        self.calculate_totals()

    def create_widgets(self):
        """Creates and places all the GUI elements on the window."""
        
        # Main padding frame to keep things neat
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # --- Bill Amount Input ---
        ttk.Label(main_frame, text="Total Bill Amount ($):", font=("Helvetica", 12)).pack(anchor=W, pady=(0, 5))
        
        self.bill_entry = ttk.Entry(
            main_frame, 
            textvariable=self.bill_amount_var, 
            font=("Helvetica", 14),
            bootstyle=PRIMARY
        )
        self.bill_entry.pack(fill=X, pady=(0, 15))

        # --- Tip Percentage Selection ---
        ttk.Label(main_frame, text="Tip Percentage:", font=("Helvetica", 12)).pack(anchor=W, pady=(0, 5))
        
        # Frame to hold radio buttons horizontally
        tip_frame = ttk.Frame(main_frame)
        tip_frame.pack(fill=X, pady=(0, 15))

        # Create radio buttons for 10%, 15%, and 20%
        percentages = [("10%", 0.10), ("15%", 0.15), ("20%", 0.20)]
        for text, value in percentages:
            ttk.Radiobutton(
                tip_frame, 
                text=text, 
                value=value, 
                variable=self.tip_percent_var,
                bootstyle=(PRIMARY, TOOLBUTTON) # Makes it look like a clickable button
            ).pack(side=LEFT, padx=(0, 10))

        # --- Number of Diners ---
        ttk.Label(main_frame, text="Number of Diners:", font=("Helvetica", 12)).pack(anchor=W, pady=(0, 5))
        
        # Spinbox allows the user to click up/down arrows or type a number (1 to 6)
        ttk.Spinbox(
            main_frame, 
            from_=1, 
            to=6, 
            textvariable=self.num_diners_var, 
            font=("Helvetica", 12),
            bootstyle=INFO
        ).pack(fill=X, pady=(0, 20))

        # --- Separator Line ---
        ttk.Separator(main_frame, orient=HORIZONTAL).pack(fill=X, pady=10)

        # --- Results Display ---
        # We use Labels to show the calculated results.
        self.result_tip_label = ttk.Label(main_frame, text="Tip Amount: $0.00", font=("Helvetica", 12, "bold"))
        self.result_tip_label.pack(anchor=W, pady=2)

        self.result_total_label = ttk.Label(main_frame, text="Total Bill: $0.00", font=("Helvetica", 12, "bold"))
        self.result_total_label.pack(anchor=W, pady=2)

        self.result_per_person_label = ttk.Label(main_frame, text="Per Person: $0.00", font=("Helvetica", 14, "bold"), bootstyle=SUCCESS)
        self.result_per_person_label.pack(anchor=W, pady=(10, 20))

        # --- Exit Button ---
        ttk.Button(
            main_frame, 
            text="Exit Application", 
            command=self.root.destroy, #closes the window and quits the app
            bootstyle=DANGER
        ).pack(fill=X, side=BOTTOM)

    def calculate_totals(self, *args):
        """
        Calculates the tip, total, and split amount. 
        This is triggered automatically whenever an input variable changes.
        """
        
        # Get the bill amount from the entry box
        bill_text = self.bill_amount_var.get()
        
        # Error Handling: Check if the user entered a valid number
        try:
            # Try to convert the typed text into a decimal number (float)
            # If it's blank or letters, this will cause a ValueError
            if bill_text.strip() == "":
                bill_amount = 0.0
            else:
                bill_amount = float(bill_text)
                
            # Change entry style back to normal if it was previously invalid
            self.bill_entry.configure(bootstyle=PRIMARY)
            
        except ValueError:
            # If the user typed something invalid (like "abc"), highlight the box red
            self.bill_entry.configure(bootstyle=DANGER)
            bill_amount = 0.0 # Default to 0 so math doesn't break

        # Get the tip percentage and number of diners
        tip_percent = self.tip_percent_var.get()
        
        try:
            num_diners = self.num_diners_var.get()
            # Prevent dividing by zero if the user manually deletes the spinbox value
            if num_diners < 1:
                num_diners = 1
        except tk.TclError:
            # Catch error if spinbox is empty or invalid
            num_diners = 1 

        #Perform the mathematical calculations
        tip_amount = bill_amount * tip_percent
        total_bill = bill_amount + tip_amount
        per_person = total_bill / num_diners

        # 5. Update the result labels with formatted strings (2 decimal places)
        self.result_tip_label.config(text=f"Tip Amount: ${tip_amount:.2f}")
        self.result_total_label.config(text=f"Total Bill: ${total_bill:.2f}")
        self.result_per_person_label.config(text=f"Per Person: ${per_person:.2f}")

# --- Application Startup ---
if __name__ == "__main__":
    # Create the main window instance
    app_window = ttk.Window(themename="flatly")
    
    # Instantiate our class and pass the window to it
    app = TipCalculatorApp(app_window)
    
    # Start the GUI event loop (keeps the window open and listening for clicks)
    app_window.mainloop()

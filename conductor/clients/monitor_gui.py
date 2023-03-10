import tkinter as tk
import labrad
from twisted.internet.defer import inlineCallbacks
import json


class Window(tk.Tk):
    geometry = "400x400"
    name = "Stop_Experiment"
    servername = "conductor"

    def __init__(self,):
        tk.Tk.__init__(self, )
        self.configure(bg="#2b2b2b")
        self.title("Experiment control client")
        
        # Main text box
        self.textbox = tk.Text(self, font=("Helvetica", 12), bg="#1e1e1e", fg="white")
        self.textbox.pack(side="top", fill="both", expand=True, padx=20, pady=20)

        # get parameter button
        self.get_param_button = tk.Button(self, text="Get Active Parameters", command=self.get_active_parameters, font=("Helvetica", 14), bg="#4f4f4f", fg="white")
        self.get_param_button.pack(side="left", padx=20, pady=20)

        # stop experiment button
        self.stop_exp_button = tk.Button(self, text="Stop Experiment", command=self.stop_exp, font=("Helvetica", 14), bg="#4f4f4f", fg="white")
        self.stop_exp_button.pack(side="left", padx=20, pady=20)

        # check loaded sequences button
        self.stop_exp_button = tk.Button(self, text="Get Sequences", command=self.get_sequences, font=("Helvetica", 14), bg="#4f4f4f", fg="white")
        self.stop_exp_button.pack(side="left", padx=20, pady=20)

    @inlineCallbacks
    def get_sequences(self):
        cxn = yield labrad.connect()
        if cxn.connected:
            self.textbox.insert(1.0, "Connected to the server. \n")
            input_str = yield cxn.sequencer.sequence()
        else:
            self.textbox.insert(1.0, "Connection failed. \n")

        yield cxn.disconnect()
        if not cxn.connected:
            self.textbox.insert(1.0, "Disconnected. \n")

        # Parse the input string as a JSON object
        data = json.loads(input_str)
        # Extract the loaded sequences
        sequences = ['"' + seq + '"\n' for seq in data['abcd']]
        # Construct the final string
        output_str = "Loaded sequences: [\n %s]" % ( " ".join(sequences))  
        self.textbox.insert(1.0, output_str+" \n")

    @inlineCallbacks
    def stop_exp(self):
        cxn = yield labrad.connect()
        if cxn.connected:
            self.textbox.insert(1.0, "Connected to the server. \n")
            yield cxn.conductor.stop()
            self.textbox.insert(1.0, "Experiment stopped. \n")
        else:
            self.textbox.insert(1.0, "Connection failed. \n")

        yield cxn.disconnect()
        if not cxn.connected:
            self.textbox.insert(1.0, "Disconnected. \n")

    @inlineCallbacks
    def get_active_parameters(self):
        cxn = yield labrad.connect()
        if cxn.connected:
            self.textbox.insert(1.0, "Connected to the server. \n")
            param_names = yield cxn.conductor.get_active_parameters()
            param_names = json.loads(param_names)
            param_vals = yield [cxn.conductor.get_parameter_values(json.dumps({k:v})) for k, v in param_names.items()]
        else:
            self.textbox.insert(1.0, "Connection failed. \n")
        yield cxn.disconnect()
        if not cxn.connected:
            self.textbox.insert(1.0, "Disconnected. \n")

        # Parse each string in the input list as a JSON object and extract the key-value pairs
        pairs = [(json.loads(s).items()[0]) for s in param_vals]
        pairs = sorted(pairs, key=lambda x: x[0])

        # Create a new Toplevel window to display the key-value pairs
        popup = tk.Toplevel(self)
        popup.configure()
        popup.title("Active Parameters")
        popup.geometry("600x600")

        # Add a scrollbar to the popup window
        scroll = tk.Scrollbar(popup, orient="vertical")
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a canvas to hold the table of key-value pairs
        canvas = tk.Canvas(popup, bg="#f2f2f2", bd=0, highlightthickness=0, yscrollcommand=scroll.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=canvas.yview)

        # Create a table to display the key-value pairs
        table = tk.Frame(canvas, bg="#f2f2f2")
        table.pack(side=tk.TOP, padx=5, pady=5)
        canvas.create_window((0, 0), window=table, anchor=tk.NW)

        # Add the key-value pairs to the table
        for i, (k, v) in enumerate(pairs):
            bg_color = "#a10000" if i % 2 == 0 else "#0014ab"
            label1 = tk.Entry(table, disabledbackground =bg_color, disabledforeground = bg_color, fg=bg_color, bd=0, highlightthickness=0)
            label1.insert(0, str(k))
            label1.configure(state="readonly", font=("Helvetica", 12))
            label1.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            label2 = tk.Entry(table, disabledbackground =bg_color, fg=bg_color, bd=0, highlightthickness=0)
            label2.insert(0, str(v))
            label2.configure(state="readonly", font=("Helvetica", 12))
            label2.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

        # Update the canvas scroll region
        table.update_idletasks()
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        # Add a button to close the popup window
        close_button = tk.Button(popup, text="Close", command=popup.destroy, font=("Helvetica", 14), bg="#4f4f4f", fg="white")
        close_button.pack(side=tk.BOTTOM, padx=5, pady=5)

        # Center the popup window on the screen
        popup.update_idletasks()
        w = popup.winfo_width()
        h = popup.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        popup.geometry('{}x{}+{}+{}'.format(w, h, x, y))



if __name__ == '__main__':
    gui = Window()
    gui.mainloop()

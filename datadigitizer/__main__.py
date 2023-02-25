r"""
Main.
"""
from datadigitizer.gui import App, tk

def run():
    root = tk.Tk()
    app = App(master=root)
    app.run()

if __name__ == "__main__":
    run()
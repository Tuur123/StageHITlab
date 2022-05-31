from GUI.MainWindow import MainWindow
import gc

if __name__ == "__main__":
    gc.disable()
    app = MainWindow()
    app.mainloop() 
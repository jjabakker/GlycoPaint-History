

from tkinter import filedialog, messagebox, ttk
from src.Application.Support.Convert_BF_from_nd2_to_jpg import convert_bf_images

if __name__ == "__main__":
    class ConvertDialog:

        def __init__(self, root):
            self.root = root
            self.root.title('Convert BF Images from .nd2 to .jpg')

            self.image_directory = ""
            self.paint_directory = ""

            content = ttk.Frame(self.root)
            frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
            frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

            #  Do the lay-out
            content.grid(column=0, row=0)
            frame_directory.grid(column=0, row=1, padx=5, pady=5)
            frame_buttons.grid(column=0, row=2, padx=5, pady=5)

            # Fill the button frame
            btn_process = ttk.Button(frame_buttons, text='Process', command=self.process)
            btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
            btn_process.grid(column=0, row=1)
            btn_exit.grid(column=0, row=2)

            # Fill the directory frame
            btn_image_dir = ttk.Button(frame_directory, text='Image Source Directory', width=20,
                                       command=self.change_image_dir)
            self.lbl_image_dir = ttk.Label(frame_directory, text=self.image_directory, width=50)

            btn_paint_dir = ttk.Button(frame_directory, text='Experiment Directory', width=20,
                                       command=self.change_paint_dir)
            self.lbl_paint_dir = ttk.Label(frame_directory, text=self.paint_directory, width=50)

            btn_image_dir.grid(column=0, row=0, padx=10, pady=5)
            self.lbl_image_dir.grid(column=1, row=0, padx=20, pady=5)

            btn_paint_dir.grid(column=0, row=1, padx=10, pady=5)
            self.lbl_paint_dir.grid(column=1, row=1, padx=20, pady=5)

        def change_image_dir(self):
            self.image_directory = filedialog.askdirectory(initialdir=self.image_directory)
            if len(self.image_directory) != 0:
                self.lbl_image_dir.config(text=self.image_directory)

        def change_paint_dir(self):
            self.paint_directory = filedialog.askdirectory(initialdir=self.paint_directory)
            if len(self.paint_directory) != 0:
                self.lbl_paint_dir.config(text=self.paint_directory)

        def process(self):
            if self.image_directory == "" or self.paint_directory == "":
                message = 'The image directory needs to point to where the images are.\n\n'
                message += 'The experiment directory is where the experiment_info.csv will be placed.'
                messagebox.showwarning(title='Warning', message=message)
            else:
                # prepare_experiment_info_file(self.image_directory, self.paint_directory)
                self.exit_dialog()

        def exit_dialog(self):
            self.root.destroy()


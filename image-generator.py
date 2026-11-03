
import sys
import os

# i couldnt show the image any other way without using this gui library so it is mandatory for this project
from tkinter import Tk, Canvas
# PIL library is used for image processing tasks also impossible to do without it
from PIL import Image, ImageDraw, ImageStat, ImageTk


import queue
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

class MinecraftPicturesGenerator:
    def __init__(self, root, image_path, square_size, mode):
        self.root = root
        self.square_size = square_size
        self.mode = mode
        self.original = Image.open(image_path).convert("RGB")
        self.width, self.height = self.original.size
        self.x = 0
        self.y = 0
        self.result = self.original.copy()
        self.root.title("Minecraft Pictures Generator")
        self.root.geometry("800x600")
        self.canvas = Canvas(root,background="black",highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.photo = None
        self.canvas.bind("<Configure>", self.display_image)
        self.root.after(100, self.process_next_square)

    def display_image(self, event=None):

        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)

        scale = min(
            canvas_width / self.width,
            canvas_height / self.height
        )

        new_width = max(1, int(self.width * scale))
        new_height = max(1, int(self.height * scale))

        display = self.result.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )
        self.photo = ImageTk.PhotoImage(display)
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width//2,
            canvas_height//2,
            image=self.photo,
            anchor="center"
        )

    def start_processing(self):
        if hasattr(self, 'running') and self.running:
            return
        self.running = True
        thread = threading.Thread(
            target=self.processing_thread,
            daemon=True
        )
        thread.start()



    def processing_thread(self):
        if self.mode == False:
            self.process_next_square()
        elif self.mode == True:
            self.multi_processing()

    def multi_processing(self):
        pass


    #recursive processing couldnt find better solution
    def process_next_square(self):
        if self.y >= self.height:
            print("Processing completed")
            self.running = False
            return

        x_end = min(self.x + self.square_size, self.width)
        y_end = min(self.y + self.square_size, self.height)

        block = self.original.crop(
            (self.x, self.y, x_end, y_end)
        )

        average_color = tuple(
            int(value)
            for value in ImageStat.Stat(block).mean
        )

        draw = ImageDraw.Draw(self.result)

        draw.rectangle(
            (self.x, self.y, x_end - 1, y_end - 1),
            fill=average_color
        )
        self.x += self.square_size
        if self.x >= self.width:
            self.x = 0
            self.y += self.square_size
        self.display_image()

        self.root.after(1, self.process_next_square)


def main():

    if len(sys.argv) != 4:
        print("Usage: python main.py <filename.jpg> <square_size> <S|M>")
        return

    image_path = sys.argv[1]

    try:
        square_size = int(sys.argv[2])
    except ValueError as error:
        print(f"Error: {error}")
        return

    if not os.path.isfile(f"img/{image_path}"):
        print("Error: image file does not exist.")
        return

    if not image_path.lower().endswith((".jpg", ".jpeg")):
        print("Error: input file must be JPG.")
        return

    if sys.argv[3] not in ("S", "M"):
        print("Error: third argument must be 'S' or 'M'.")
        return

    if sys.argv[3] == "S":
        mode=False
    else:
        mode=True

    root = Tk(useTk=1)

    MinecraftPicturesGenerator(
        root,
        f"img/{image_path}",
        square_size,
        mode
    )

    root.mainloop()



if __name__ == "__main__":
    main()

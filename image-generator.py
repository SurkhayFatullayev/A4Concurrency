
import sys
import os

# i couldnt show the image any other way without using this gui library so it is mandatory for this project
from tkinter import Tk, Canvas
# PIL library is used for image processing tasks also impossible to do without it
from PIL import Image, ImageDraw, ImageTk, ImageStat

import queue
import multiprocessing
from concurrent.futures import ProcessPoolExecutor


def initialize_worker(width, height, image_bytes):
    global _worker_image
    _worker_image = Image.frombytes("RGB", (width, height), image_bytes)

def process_square(image, square):
    x, y, square_size = square
    x_end = min(x + square_size, image.width)
    y_end = min(y + square_size, image.height)
    block = image.crop((x, y, x_end, y_end))
    average_color = tuple(int(value) for value in ImageStat.Stat(block).mean)
    return x, y, x_end, y_end, average_color


def process_square_in_worker(square):
    if _worker_image is None:
        raise RuntimeError("Worker image has not been initialized")
    return process_square(_worker_image, square)

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
        self.squares = ( 
            (x, y, self.square_size)
            for y in range(0, self.height, self.square_size)
            for x in range(0, self.width, self.square_size)
        )
        if self.mode is False:
            self.single_processing()
        elif self.mode is True:
            self.multi_processing()
    
    #recursive processing couldnt find better solution
    def single_processing(self):
        try:
            square = next(self.squares)
        except StopIteration:
            print("Processing completed")
            return

        self.apply_square_result(process_square(self.original, square))
        self.display_image()
        self.root.after(1, self.single_processing)

    def apply_square_result(self, result):
        x, y, x_end, y_end, average_color = result
        draw = ImageDraw.Draw(self.result)
        draw.rectangle((x, y, x_end - 1, y_end - 1), fill=average_color)

    def multi_processing(self):
        #ToDo: i will change ig for blocks of squares

        image_bytes = self.original.tobytes()
        self.results_queue = queue.Queue()
        self.squares_done = 0

        self.executor = ProcessPoolExecutor(
            max_workers=multiprocessing.cpu_count(),
            initializer=initialize_worker,initargs=(self.width, self.height, image_bytes)
        )
        print(multiprocessing.cpu_count())
        squares = list(self.squares)

        self.total_squares = len(squares)

        for block in squares:
            future = self.executor.submit(process_square_in_worker, block)
            future.add_done_callback(self.square_finished)

        self.root.after(100, self.update_multiprocessing)

    def square_finished(self, future):
        try:
            result = future.result()
            self.results_queue.put(result)
        except Exception as error:
            self.results_queue.put(error)

    def update_multiprocessing(self):
        updated = False
        while True:
            try:
                result = self.results_queue.get_nowait()
            except queue.Empty:
                break
            self.squares_done += 1
            if isinstance(result, Exception):
                print(f"Processing error: {result}")
                continue
            self.apply_square_result(result)

            updated = True

        if updated:
            self.display_image()

        if self.squares_done >= self.total_squares:
            print("Processing completed")
            self.executor.shutdown(wait=False)
            self.executor = None
            return

        self.root.after(10, self.update_multiprocessing)

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
    if square_size <= 0:
        print("Error: square_size must be a positive integer.")
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

    generator = MinecraftPicturesGenerator(
        root,
        f"img/{image_path}",
        square_size,
        mode
    )
    generator.start_processing()

    root.mainloop()



if __name__ == "__main__":
    main()

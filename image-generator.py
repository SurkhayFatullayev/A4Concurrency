
import sys
import os

# i couldnt show the image any other way without using this gui library so it is mandatory for this project
from tkinter import Tk, Canvas
# PIL library is used for image processing tasks also impossible to do without it
from PIL import Image, ImageDraw, ImageTk, ImageStat

import queue
import multiprocessing

def initialize_worker(width, height, image_bytes, squares, result_queue):
    image = Image.frombytes("RGB", (width, height), image_bytes)

    try:
        for square in squares:
            result_queue.put(process_square(image, square))
    except Exception as error:
        result_queue.put(("error", str(error)))
    finally:
        result_queue.put(None)

def process_square(image, square):
    x, y, square_size = square
    x_end = min(x + square_size, image.width)
    y_end = min(y + square_size, image.height)
    block = image.crop((x, y, x_end, y_end))
    average_color = tuple(int(value) for value in ImageStat.Stat(block).mean)
    return x, y, x_end, y_end, average_color

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

    def display_image(self, _event=None):

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
            self.finish()
            return

        self.apply_square_result(process_square(self.original, square))
        self.display_image()
        self.root.after(1, self.single_processing)

    def apply_square_result(self, result):
        x, y, x_end, y_end, average_color = result
        draw = ImageDraw.Draw(self.result)
        draw.rectangle((x, y, x_end - 1, y_end - 1), fill=average_color)

    def multi_processing(self):
        image_bytes = self.original.tobytes()
        #Dividing code to multiple lines
        rows = [
            [
                (x, y, self.square_size)
                for x in range(0, self.width, self.square_size)
            ]
            for y in range(0, self.height, self.square_size)
        ]

        lines = min(multiprocessing.cpu_count(), len(rows))
        rows_per_cpu = (len(rows) + lines-1)//lines
        self.processes = []
        self.worker_queues = []
        self.finished_workers = 0

        for i in range(lines):
            assigned_rows = rows[
                i * rows_per_cpu : (i+1) * rows_per_cpu
            ]

            squares = [
                square
                for row in assigned_rows
                for square in row
            ]

            if not squares:
                continue

            result_queue = multiprocessing.Queue(maxsize=lines)
            self.worker_queues.append(result_queue)

            process = multiprocessing.Process(
                target=initialize_worker,
                args=(
                    self.width,
                    self.height,
                    image_bytes,
                    squares,
                    result_queue
                )
            )

            self.processes.append(process)
            process.start()

        print(f"Started {len(self.processes)} processes")

        self.update_multiprocessing()

    def update_multiprocessing(self):
        updated = False

        for result_queue in self.worker_queues:
            try:
                result = result_queue.get_nowait()
            except queue.Empty:
                continue

            if result is None:
                self.finished_workers += 1
                continue

            if result[0] == "error":
                print(f"Worker error: {result[1]}")
                continue

            self.apply_square_result(result)
            updated = True

        if updated:
            self.display_image()

        if self.finished_workers == len(self.processes):
            print("Processing completed")

            for process in self.processes:
                process.join()

            for result_queue in self.worker_queues:
                result_queue.close()

            self.finish()
            return

        #Put Timeout here
        self.root.after(20,self.update_multiprocessing)

    def finish(self):
        self.display_image()
        self.result.save("result.jpg")
        print(f"Processing completed, saved to result.jpg")



def main():

    if len(sys.argv) != 4:
        print("Wrong amount of arguments. Please provide <filename.jpg>('Should be in img folder') <square_size> <S|M>")
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

    if sys.argv[3] == "S":
        mode=False
    elif sys.argv[3] == "M":
        mode=True
    else:
        print("Error: third argument must be 'S' or 'M'.")
        return

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

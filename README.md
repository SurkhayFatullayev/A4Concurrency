# Part 1: Image Generator Using Multiprocessing

## What we do?

We create a pixelated version of a JPG image by dividing it into square regions. For each square, the program calculates the average color and fills that region with the result.

The image is shown in a window while it is being processed. The program can work in two modes:

- **Single process (`S`):** processes one square at a time in the main process.
- **Multiprocessing (`M`):** splits rows of squares between worker processes.

The square size controls the appearance of the result. A larger value creates larger blocks and a more pixelated image, while a smaller value keeps more detail.

## Running the Program

The program uses Pillow for image processing. Install the project dependency with:

```shell
python3 -m pip install -r requirements.txt
```

Tkinter is also required to display the window and is included with many Python installations. The project was tested with Python 3.14.

Place a JPG or JPEG image in the `img` folder, then run the program from the project directory. For example:

```shell
python3 image-generator.py GTA6PromoArt.jpg 40 M
```

The command takes three arguments:

- The image filename inside `img`.
- A positive integer for the square size.
- `S` for single-process mode or `M` for multiprocessing mode.

The following command processes the same image sequentially:

```shell
python3 image-generator.py GTA6PromoArt.jpg 40 S
```

## How It Works

The program checks its arguments, opens the selected image, and creates the Tkinter window. It then passes the image path, square size, and selected mode to the generator:

```python
generator = MinecraftPicturesGenerator(
    root,
    f"img/{image_path}",
    square_size,
    mode
)
generator.start_processing()
```

The main window is created before the generator starts:

```python
root = Tk(useTk=1)
```

The `start_processing()` function calculates squares count(leftover from previous multithread implementation where it also needed it now only single needs so can be removed from there) and then based on mode parameter chooses if it should executemulti or single processor solution.

```python
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
```

## Single-Process Mode

`single_processing()` goes from square to squareб сomputes the average from the original, paints it onto result, then refreshes the preview.
the comment above this function is also left over just decided to leave it here

```python
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
```

## Calculating Each Square

Both modes use `process_square()` to calculate the average RGB color for a square. The `min` calls keep the last square inside the image when its width or height is not evenly divisible by the square size.

```python
def process_square(image, square):
    x, y, square_size = square
    x_end = min(x + square_size, image.width)
    y_end = min(y + square_size, image.height)
    block = image.crop((x, y, x_end, y_end))
    average_color = tuple(int(value) for value in ImageStat.Stat(block).mean)
    return x, y, x_end, y_end, average_color
```

The main process uses the returned coordinates and color to draw the square on the result image.

## Multiprocessing Mode

`multi_processing()` creates rows of square coordinates. Splitting by row makes it straightforward to give each worker a continuous band of the image.

```python
lines = min(multiprocessing.cpu_count(), len(rows))
```

This limits the number of workers to the smaller of the available CPU count and the number of image rows. The rows are divided between those workers:

```python
rows_per_cpu = (len(rows) + lines - 1) // lines
for i in range(lines):
    assigned_rows = rows[i * rows_per_cpu : (i + 1) * rows_per_cpu]
    squares = [square for row in assigned_rows for square in row]
```

Worker i takes the slice of rows from i * rows_per_cpu up to (i+1) * rows_per_cpu, and then flattens those rows into one list of blocks

```python
#Put Timeout here
self.root.after(20,self.update_multiprocessing)
```
The main process checks the queues every 20 milliseconds. When it receives a square result, it updates the result image and refreshes the preview. An empty queue does not stop it from checking the other workers.

```python
try:
    result = result_queue.get_nowait()
except queue.Empty:
    continue
```
if result is None:
    self.finished_workers += 1
    continue
```

If a worker encounters an error, it sends an error message and still sends its completion signal. After all workers have finished, the program closes the queues and saves the result.

## Output

When processing completes, the pixelated image is saved as `result.jpg` in the project directory. Running the program again replaces that file. The result is also left visible in the window.

Multiprocessing can help with larger images because multiple workers calculate squares at the same time. For smaller images, the time needed to start processes and pass image data between them can reduce or remove that benefit.



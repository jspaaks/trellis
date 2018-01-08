*system dependencies*

```bash
sudo apt install python3
sudo apt install python3-dev
sudo apt install python3-tk
```

*pip dependencies*

```bash
pip install -r requirements.txt
```


*example output*

sample of the data:

```
[{
    "block_size_x": 16,
    "block_size_y": 1,
    "tile_size_x": 1,
    "tile_size_y": 1,
    "num_streams": 1,
    "time": 20.404076766967773
}, {
    "block_size_x": 16,
    "block_size_y": 1,
    "tile_size_x": 1,
    "tile_size_y": 1,
    "num_streams": 2,
    "time": 15.670905494689942
}, {
    "block_size_x": 16,
    "block_size_y": 1,
    "tile_size_x": 1,
    "tile_size_y": 1,
    "num_streams": 4,
    "time": 13.029843139648438
}, {
    "block_size_x": 16,
    "block_size_y": 1,
    "tile_size_x": 1,
    "tile_size_y": 1,
    "num_streams": 8,
    "time": 11.713497543334961
}, ...
]
```


Default visualization with nearest-neighbor interpolation as background to the matrix of scatter:
![example-output-2.png](https://github.com/jspaaks/trellis/raw/master/images/example-output-2.png "Example output 2")

As previous, not showing the nearest-neighbor interpolation:
![example-output-3.png](https://github.com/jspaaks/trellis/raw/master/images/example-output-3.png "Example output 3")

As previous, but with more efficient use of figure space:
![example-output-4.png](https://github.com/jspaaks/trellis/raw/master/images/example-output-4.png "Example output 4")

As previous, with manually set color axis limits:
![example-output-5.png](https://github.com/jspaaks/trellis/raw/master/images/example-output-5.png "Example output 5")

As previous, with different ``matplotlib`` colormap (``PRGn``)
![example-output-6.png](https://github.com/jspaaks/trellis/raw/master/images/example-output-6.png "Example output 6")

As previous, with different ``matplotlib`` colormap (``hsv``)
![example-output-7.png](https://github.com/jspaaks/trellis/raw/master/images/example-output-7.png "Example output 7")

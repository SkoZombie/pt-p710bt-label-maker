# P-Touch Cube (PT-P710BT) label maker

**Fork of https://github.com/robby-cornelissen/pt-p710bt-label-maker**

## Key Changes in Fork

* Added support to use `-i`/`--info` to just query the printer information
* Added ability to define default BT address to save typing it in each time
* Added support for multiple tape widths (tested on 12mm)
* Detects tape width to try to use automatically
* Changed some function comments to be docstrings
* Moved some legacy string formatting to f-strings
* Updated rasterizer to support widths other than 128px

## Introduction

This is a small application script to allow printing from the command line on the Brother P-Touch Cube (PT-P710BT). It is based on the _["Raster Command Reference"](https://download.brother.com/welcome/docp100064/cv_pte550wp750wp710bt_eng_raster_101.pdf)_ made available by Brother on their support website. Theoretically, it should also work with other label printers that use the same command set, such as the PT-E550W and PT-P750W, but since I don't have access to these devices, I have not been able to verify this.
The script converts a PNG image to the raster format expected by the label printer, and communicates this to the printer over Bluetooth. 


## Rationale

I wrote this script because of layout limitations encountered in the smartphone apps provided by the manufacturer. While they do make a desktop application available that seems to be more full-featured, it is only available for Microsoft Windows and Mac OS X, neither of which is my operating system of choice. In addition, I wanted the ability to execute label printing operations from the command-line to allow for easy integration with various pipelines.

Similar scripts that exist for the older P-Touch Cube (PT-P300BT), as can be found [here](https://gist.github.com/stecman/ee1fd9a8b1b6f0fdd170ee87ba2ddafd) and [here](https://gist.github.com/dogtopus/64ae743825e42f2bb8ec79cea7ad2057), didn't completely suit my purpose, but provided helpful reference material.


## Requirements and installation

The application script depends on the following packages:

 * [`pybluez`](https://github.com/pybluez/pybluez), for Bluetooth communication
 * [`pypng`](https://github.com/drj11/pypng), to read PNG images
 * [`packbits`](https://github.com/psd-tools/packbits), to compress data to TIFF format

These can all be installed using `pip`:
```
pip install -r requirements.txt
```

Note that the installation of `pybluez` requires the presence of the [`bluez`](http://www.bluez.org/) development libraries and `libbluetooth` header files (`libbluetooth3-dev`). For most Linux distributions, these should be available through your regular package management system. On Debian based systems (Ubuntu/ Linux Mint) you can type: `sudo apt install libbluetooth-dev`.


## Usage

The application can be called to print as follows:

```
python label_maker.py --image <image-path> <bt-address>
```

The expected parameters are the following:

 * **`image-path`**  \
 The path to the PNG file to be printed. The image needs to be the correct number of pixels high for the size of your tape. The width is variable depending on how long you want your label to be. The script bases itself on the PNG image's alpha channel, and prints all pixels that are not fully transparent (alpha channel value greater than 0).
 * **`bt-address`**  \
The Bluetooth address of the printer. The `bluetoothctl` application (part of the aforementioned `bluez` stack) can be used to discover the printer's address, and pair with it from the command line:
    ```
    $> bluetoothctl
    [bluetooth]# scan on
    [NEW] Device A0:66:10:CA:E9:22 PT-P710BT6522
    [bluetooth]# pair A0:66:10:CA:E7:42
    [bluetooth]# exit
    $>
    ```

There are other options available, use `python lable_maker.py --help` to see them. 


## Size Information

Different sized tapes require different pixel heights to print to the tape.

The sizes apply to style TZe tapes only.

| Tape Height | Pixel Height |
|-------------|--------------|
| 3.5mm       | 24           |
| 6mm         | 32           |
| 9mm         | 50           |
| 12mm        | 70           |     
| 18mm        | 112          |
| 24mm        | 128          |


## Limitations

In its current version, the program only prints one label at the time.

## License
<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0; vertical-align: middle;" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br>This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.

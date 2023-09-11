# TreeDetect

This is a python module for detecting trees with aerial photography and LiDAR data from PDOK geo-data sources.

![Example of detected trees](Example.png)

## Getting Started

These instructions provides information on how to setup a copy of the project, install any requirements, and how to run it on your local machine for development and testing purposes. 

### Prerequisites

Necessary python components for this module are numpy, pandas and scipy for mathematical operations; Pillow, matplotlib and scikit-image for image processing and visualization; and OWSLib for input/output of geo-data. 

To install the dependencies automatically, run:

```
cd <path to this folder, where the requirements.txt is located>
pip install .
```

## Usage

For an example on how to use the , see the example folder for a couple of ipython notebooks.

* Background_Info_Notebook - the background to the processing

Alternatively, you can use the `single_analysis_main.py` file in the root folder of the repo (outside of the src folder), alter any settings you wish to change therein and/or in the `confs/conf.yml` file, and then call it as follows:

```
python single_analysis_main.py
```

## Authors

* **Tim Bergman** - *Initial work* - [timbergman-personal@proton.me](timbergman-personal@proton.me)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.


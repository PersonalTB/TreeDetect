# TreeDetect

This is a python module for detecting trees with aerial photography from geo-data sources.

![Example of detected trees](Example.png)

## Getting Started

These instructions provides information on how to setup a copy of the project, install any requirements, and how to run it on your local machine for development and testing purposes. 

### Prerequisites

Necessary python components for this module are numpy, pandas and scipy for mathematical operations; Pillow, matplotlib and scikit-image for image processing and visualization; and OWSLib for input/output of geo-data. 

To install the dependencies automatically, run:

```
cd <path to the root folder, where the requirements.txt is located>
pip install .
```

## Usage

For an example on how to use the module, see: 
*  `example/Background_Info_Notebook.ipynb` - a notebook on the background to the tree detection method and processing. 
*  `single_analysis_main.py` - python script in the root folder, alter any settings you wish to change therein and/or in the `confs/conf.yml` file, and then call it with `python single_analysis_main.py`

## Authors

* **Tim Bergman** - *Initial work* - [timbergman-personal@proton.me](timbergman-personal@proton.me)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.


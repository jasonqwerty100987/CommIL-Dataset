# CommIL-Dataset
The official github for the CommIL V2V dataset

# Download Link
Click links below to download the data needed to generate masks for train, validate, and test sets from the [OPV2V](https://github.com/DerrickXuNu/OpenCOOD) benchmark.

[Train](https://rutgers.box.com/s/wj5ctzx88xxn1qrha6kvd6q35p5h51qg), [Validate](https://rutgers.box.com/s/52usnmla0aa9gufswn2mgahs64zrmiu6), [Test](https://rutgers.box.com/s/lujnlsl67xeoatkbethcutljhi0bm7hp)

# Usage
Download the data from links above and unzip them to the same root directory of the original OPV2V dataset, which can be download from [here](https://drive.google.com/drive/folders/1dkDeHlwOVbmgXcDazZvO6TFEZ6V_7WUu).
You may also need the additional data from [here](https://drive.google.com/drive/folders/1dkDeHlwOVbmgXcDazZvO6TFEZ6V_7WUu) to enable camera-based coorperative perception implementation.

The directories should look like the following (this example showing the directories for train dataset):

```bash
|dataset root
| --train
|     ----2021_08_16_22_26_54
|     ----2021_08_18_09_02_56
|     ----....
|
| --comm_sim
|     ----1e+02_1e+02_1e-01
|         ----2021_08_16_22_26_54
|         ----2021_08_18_09_02_56
|         ----....
|     ----1e+03_1e+02_1e-01
|         ----2021_08_16_22_26_54
|         ----2021_08_18_09_02_56
|         ----....
|     ----....
```

The name of sub-directories is in the following format {feature_size}\_{payload_size}\_{send_delay}. You can set the feature\_size and payload\_size that are used to generate masks in yaml files, and the generated masks are used to select which part of features are droped during the transmission process. 

# Communication Overhead
To account for communication overhead, the dataset will also return the time difference between when the first packet been sent and when the last packet is recieved. By default, the propagation delay is calculated based on the [Log Distance Propagation Delay Model](https://www.nsnam.org/docs/models/html/propagation.html) and the waypoints of CAVs. The time difference will be used to retrive the coresponding groundtruth after the delay.

# Data Format
In the comm\_sim folders, the sub-directories represent what are the configurations used for the communication simulation. The sub-sub-directories are scenario folders. Inside each of the scenario folders, there is a file called comm\_sim.json. This JSON file records all the transmitted and received packets for each of the CAVs in a given scenario . The records include the packet number and their trainmitted/recieved time and they will be used to construct masks to drop information from shared features. The basic structure of a comm\_sim.json file is as following:
```bash
|{time_stamp 1}
| --{CAV_Number 1}
|     ----{received}
|         ----[time, packet_number]
|         ----[time, packet_number]
|         ----....
|     ----{transmitted}
|         ----[time, packet_number]
|         ----[time, packet_number]
|         ----....
| --{CAV_Number 2}
|     ----{received}
|         ----....
|     ----{transmitted}
|         ----....
| --....
|{time_stamp 2}
|....
```
# Mask Format and Usage
Masks are generated based on the comm\_sim.json files and they are loaded as a Python dictionary object. You can access the mask through
```python
from generate_masks import generate_mask
loaded_mask = generate_mask(comm_sim_folder_name)
mask = loaded_mask[scenario_folder_name][time_stamp][ego_CAV_Number][peer_CAV_Number]
```
The comm_sim_folder_name is the folder name of the confige folders (e.g., "1e+02_1e+02_1e-01"), and the scenario_folder_name is the folder name of a scenario folder (e.g., 2021_08_16_22_26_54). 

The mask is a 1D numpy boolean array with values to indicate whether to keep the data at a given index and the size of the mask is the same as the feature size. The values of a mask at indices correpsonsed to dropped packets have a value 0.

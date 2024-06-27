import os
import yaml
import re
import json

DELTA_TIME = 0.05 # The time difference in second between two adjacent time stamp

def _parse_time_stamps(path:str, in_order = True) -> list:
    stamps = []
    for filename in os.listdir(path):
        if filename.endswith(".pcd"):
            stamps.append(filename.split(".")[0])

    if in_order:
        stamps.sort()

    return stamps

def _get_yaml_loader():
    loader = yaml.Loader
    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(u'''^(?:
         [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
        |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
        |\\.[0-9_]+(?:[eE][-+][0-9]+)?
        |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
        |[-+]?\\.(?:inf|Inf|INF)
        |\\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))
    
    return loader

def _read_yaml_files(path:str, stamps:list, fields:list) -> list:
    results = []
    loader = _get_yaml_loader()
    for stamp in stamps:
        yaml_path = os.path.join(path, stamp+".yaml")
        with open(yaml_path, 'r') as fp:
            yaml_file = yaml.load(fp, Loader=loader)
            if "yaml_parser" in yaml_file:
                yaml_file = eval(yaml_file["yaml_parser"])(yaml_file)
        temp_dict = {}

        for field in fields:
            temp_dict[field] = yaml_file[field]
        results.append(temp_dict)
    
    return results

def _post_process(stamps:list, yaml_files:list, fields:list) -> list:
    result = []
    int_stamps = [int(ele) for ele in stamps]
    origin = min(int_stamps)
    for stamp, file in zip(int_stamps, yaml_files):
        row = [(stamp - origin)*DELTA_TIME]
        row.extend([file[field] for field in fields])
        result.append(row)
    return result

def _parse_agent_id(path:str) -> str:
    return os.path.basename(path)

def _save_to_json(content, path:str) -> None:
    agent_id = _parse_agent_id(path)
    filename = agent_id+".json"

    with open(os.path.join(path, filename), "w+") as fp:
        json.dump(content, fp)
    
def parse_one_agent(path):
    print(f"Parsing Folder {path}")
    stamps = _parse_time_stamps(path)
    fields = ["true_ego_pos"]
    yaml_files = _read_yaml_files(path, stamps, fields)
    processed = _post_process(stamps, yaml_files, fields)
    _save_to_json(processed, path)


def main(path):
    for sub_folder in os.listdir(path):
        sub_folder_dir = os.path.join(path, sub_folder)
        if os.path.isdir(sub_folder_dir):
            for agent_folder in os.listdir(sub_folder_dir):
                agent_folder_path = os.path.join(sub_folder_dir, agent_folder)
                if os.path.isdir(agent_folder_path):
                    parse_one_agent(agent_folder_path)

if __name__ == "__main__":
    path = "/home/cps-tingcong/Downloads/opencood_test/test/"
    main(path)
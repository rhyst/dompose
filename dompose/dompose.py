#!python3
import sys
import os
import re
import yaml
import pprint
import operator
from functools import reduce
from pathlib import Path
from dotenv import load_dotenv
import argparse
import shutil

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", metavar="command", default="run", help="command to use: run, enable, disable", nargs="?")
    ap.add_argument("service_name", metavar="service name", help="name of service to enable or disable", nargs="?")
    ap.add_argument("--env-file", default=".env", help="path to the environment variables file")
    ap.add_argument("--available-dir", default="./services-available", help="path to the available folder")
    ap.add_argument("--enabled-dir", default="./services-enabled", help="path to the enabled folder")
    ap.add_argument("-o", "--output", default="docker-compose.yml", help="name of the output file")
    ap.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    args = vars(ap.parse_args())

    command = args['command']
    service_name = args['service_name'] if 'service_name' in args else None
    env_file = os.path.abspath(str(Path('.') / args['env_file']))
    available_dir = os.path.abspath(str(Path('.') / args['available_dir']))
    enabled_dir = os.path.abspath(str(Path('.') / args['enabled_dir']))
    output_file = os.path.abspath(str(Path('.') / args['output']))
    verbose = args['verbose'] if 'verbose' in args else False

    if (command == 'enable' or command == 'disable') and service_name is None:
            ap.error('You must specify a service name.')

    pp = pprint.PrettyPrinter(indent=2)

    # Load env vars from file
    load_dotenv(dotenv_path=env_file)

    # Useful Functions
    def getFromDict(dataDict, mapList):
            return reduce(operator.getitem, mapList, dataDict)

    def setInDict(dataDict, mapList, value):
            origvalue = getFromDict(dataDict, mapList[:-1])[mapList[-1]]
            if isinstance(origvalue,list):
                    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value + origvalue
            else:
                    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

    def merge(destination, source):
            for key, value in source.items():
                    if isinstance(value, dict):
                            node = destination.setdefault(key, {})
                            merge(node, value)
                    else:
                            destination[key] = value
            return destination

    def replace_env(match):
            return os.getenv(match.group(1))

    def enable():
            service_path = os.path.join(available_dir, service_name + ".yml")
            enabled_service_path = os.path.join(enabled_dir, service_name + ".yml")
            if os.path.isfile(enabled_service_path):
                    print('Service already enabled')
                    return
            if not os.path.isfile(service_path):
                    print("Cannot find service: {}".format(service_path))
                    sys.exit()
            if not os.path.isdir(enabled_dir):
                    print("Cannot find enabled directory: {}".format(enabled_dir))
                    sys.exit()
            if os.path.islink(service_path):
                    if os.path.isfile(enabled_service_path):
                            os.unlink(enabled_service_path)
                    os.symlink(os.readlink(service_path), enabled_service_path)
            else:
                    os.symlink(service_path, enabled_service_path)
            print("Enabled {}".format(service_path))

    def disable():
            enabled_service_path = os.path.join(enabled_dir, service_name + ".yml")
            if not os.path.isfile(enabled_service_path):
                    print("Service is not enabled: {}".format(service_path))
                    sys.exit()
            if os.path.islink(enabled_service_path):
                    os.unlink(enabled_service_path)
            else:
                    os.remove(enabled_service_path)
            print("Disabled {}".format(service_name))

    def run():
            # Gather configs
            output_config = {}
            configs = []
            config_path=enabled_dir
            config_files = [f for f in os.listdir(config_path) if os.path.isfile(os.path.join(config_path, f))]
            for config_file in config_files:
                    with open(os.path.join(config_path, config_file), 'r') as stream:
                            print('Reading {}'.format(config_file))
                            config_text = re.sub(r'\${(.*)}', replace_env, stream.read())
                            name = os.path.splitext(config_file)[0]
                            try:
                                    config = yaml.load(config_text)
                            except Exception as e:
                                    print(config_text)
                                    print('Error with "{}" config file'.format(name))
                                    print(e)
                                    sys.exit(1)
                            if "composer_base" in config and config["composer_base"]:
                                    output_config = config
                            else:
                                    configs.append(config)

            # Merge configs
            for config in configs:
                    output_config = merge(output_config, config)

            # Resolve additions
            for config in configs:
                    if 'composer_compositions' in config:
                            for composition in config['composer_compositions']:
                                    if composition['type'] == 'add':
                                            setInDict(output_config, composition['to'], [ composition['value'] ])

            output_config.pop('composer_base', None)
            output_config.pop('composer_compositions', None)

            with open(output_file, 'w+') as stream:
                    yaml.dump(output_config, stream, default_flow_style=False)
            if verbose:
                    print(yaml.dump(output_config, default_flow_style=False))

            print("Done!")

    if command == 'run':
            run()
    if command == 'enable':
            enable()
    if command == 'disable':
            disable()
"""The script is used to run snmp agent for multiple device templates chosen by the user."""

# -*- coding: utf-8 -*-
import os
import argparse
import fnmatch
import itertools
import socket
from itertools import chain
import subprocess
from utils import Utils

class simulate_snmp_devices:

    "Class to simulate snmp devices"
    def __init__(self):
        "initialize"
        utils = Utils()
        self.config = utils.read_conf('device.conf')

    def available_templates(data_dir):
        try:
            print('************Available device templates to use found in data directory********')
            for (root_dir_path, _, files) in os.walk(data_dir):
                if files:
                    tag = os.path.relpath(root_dir_path, data_dir)

                    for file in files:

                        sub_folder = os.path.basename(tag)

                        print((sub_folder if sub_folder else ''), '--->', file)

            print('************End********')
        except:
            raise("Error in reading available device templates ")

    def parse_args():
        "This function is used to input the templates chosen by the user"
        # Initialize parser
        parser = argparse.ArgumentParser(description='SNMP Simulator.')

        group = parser.add_mutually_exclusive_group(required=True)

        # Adding optional argument
        group.add_argument('-d', '--devices', required=False, nargs='+',
                            help="Enter single or multiple file names using '-d' option Ex:- -d xp.snmprec ubuntu.snmprec", default=False, metavar="")
        group.add_argument('-p', '--print', required=False, action='store_true',
                            help=" use '-p' for listing down available device templates to use")
        # Read arguments from command line
        args = parser.parse_args()
        return args

    def find_dev_template(data_dir, *args):
        "To find the device template path in data directory."
        dev_templates = list(itertools.chain(*args))
        template_path = []

        for (root_dir_path , _, files) in os.walk(data_dir):

            if files:
                tag = os.path.relpath(root_dir_path, data_dir)
                for device in dev_templates:
                    for file in files:
                        tag_parent = os.path.dirname(tag)
                        sub_folder = os.path.basename(tag)
                        if fnmatch.fnmatch(file, device):
                            template_path.append(os.path.normpath(
                                os.path.join(data_dir, tag_parent, sub_folder)))

        return template_path

    def get_open_port(self,host):
        """To find open port"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

    def create_snmp(self,*args):
        """snmpwalk the chosen device templates"""
        path = list(itertools.chain(*args))
        num_devices = len(path)
        port_list = []
        path_list = []
        for i in range(num_devices):
            try:
                port = self.get_open_port(host)
                port_list.append(port)
                path_list.append(path[i])
                print(i + 1, path[i].split('/')[-1], port)
                subprocess.run(("snmpsimd.py --v3-engine-id=010203040505060880 --v3-user=qxf2 --data-dir=%s --agent-udpv4-endpoint=127.0.0.1:%s --logging-method=file:./data/snmp_logs.txt:10m --log-level=debug &" %(path[i], port)),shell=True)
            except OSError:
                raise ValueError(
                    "error in running the snmp device 'snmpsimd.py' command")

        return (port_list, path_list)

    def snmpwalk_dev_templates(self,*args):
        "snmpwalk the chosen device templates"
        port_path = list(itertools.chain(*args))
        (port_list, path_list) = map(list, zip(port_path))
        path_list = list(chain.from_iterable(path_list))
        port_list = list(chain.from_iterable(port_list))
        no_device = len(port_list)
        device_name = []
        device_port = []
        for (path_list, port_list) in zip(path_list, port_list):
            if '\\' in path_list:
                device_name.append(path_list.split('\\')[-1])
            else:
                device_name.append(path_list.split('/')[-1])
            device_port.append(port_list)

        for i in range(no_device):
            try:
                response=subprocess.call(("snmpget -v2c -c %s 127.0.0.1:%s sysDescr.0 >>%s.txt" %(device_name[i], device_port[i],device_name[i])),shell=True)
                if response==0:
                    print("The %s device is up and running in port --> %s ."%(device_name[i], device_port[i]))
                else:
                    print("The %s device is not running as expected in port --> %s."%(device_name[i], device_port[i]))
            except OSError:
                raise ValueError('error in running the snmpget.')


if __name__ == '__main__':
    devices = simulate_snmp_devices()
    args = simulate_snmp_devices.parse_args()
    data_dir = devices.config.get('data','dir')
    host = devices.config.get('data','host')

    if args.print is True:
        simulate_snmp_devices.available_templates(data_dir)
    elif args.devices is not False:
        template_path = simulate_snmp_devices.find_dev_template(data_dir, args.devices)
        if template_path is not None:
            snmp_devices = devices.create_snmp(template_path)
            if snmp_devices is not None:
                devices.snmpwalk_dev_templates(snmp_devices)

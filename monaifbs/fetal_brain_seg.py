# Copyright 2020 Marta Bianca Maria Ranzini and contributors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

##
# \file fetal_brain_seg.py
# \brief      Script to apply automated fetal brain segmentation using a pre-trained dynUNet model in MONAI
#               Integrated within the NiftyMIC package, it performs the generation of brain masks for the
#               Super-Resolution Reconstruction.
#               This script is the default call by the executable niftymic_segment_fetal_brains if no other
#               fetal brain segmentation tool is specified.
#
# \author     Marta B M Ranzini (marta.ranzini@kcl.ac.uk)
# \date       November 2020
#

import os
import argparse
import yaml
import monaifbs

from monaifbs.src.inference.monai_dynunet_inference import run_inference

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Run fetal brain segmentation using MONAI DynUNet.')
    parser.add_argument('--input_names',
                        dest='input_names',
                        metavar='input_names',
                        type=str,
                        nargs='+',
                        help='input filenames to be automatically segmented',
                        required=True)
    parser.add_argument('--segment_output_names',
                        dest='segment_output_names',
                        metavar='segment_output_names',
                        type=str,
                        nargs='+',
                        help='output filenames where to store the segmentation masks',
                        required=True)
    parser.add_argument('--config_file',
                        dest='config_file',
                        metavar='config_file',
                        type=str,
                        help='config file containing network information for inference',
                        default=None)
    args = parser.parse_args()

    # check existence of config file and read it
    config_file = args.config_file
    if config_file is None:
        config_file = os.path.join(*[os.path.dirname(monaifbs.__file__),
                                     "config", "monai_dynUnet_inference_config.yml"])
    if not os.path.isfile(config_file):
        raise FileNotFoundError('Expected config file: {} not found'.format(config_file))
    with open(config_file) as f:
        print("*** Config file")
        print(config_file)
        config = yaml.load(f, Loader=yaml.FullLoader)

    if config['inference']['model_to_load'] == "default":
        config['inference']['model_to_load'] = os.path.join(*[os.path.dirname(monaifbs.__file__),
                                                    "models", "checkpoint_dynUnet_DiceXent.pt"])

    assert len(args.input_names) == len(args.segment_output_names), "The numbers of input output filenames do not match"

    # loop over all input files and run inference for each of them
    for img, seg in zip(args.input_names, args.segment_output_names):

        # set the output folder and add to the config file
        out_folder = os.path.dirname(seg)
        if not out_folder:
            out_folder = os.getcwd()
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)
        config['output'] = {'out_postfix': 'seg', 'out_dir': out_folder}

        # run inference
        run_inference(input_data=img, config_info=config)

        # recover the filename generated by the inference code (as defined by MONAI output)
        img_filename = os.path.basename(img)
        flag_zip = 0
        if 'gz' in img_filename:
            img_filename = img_filename[:-7]
            flag_zip = 1
        else:
            img_filename = img_filename[:-4]
        out_filename = img_filename + '_' + config['output']['out_postfix'] + '.nii.gz' if flag_zip \
            else img_filename + '_' + config['output']['out_postfix'] + '.nii'
        out_filename = os.path.join(*[out_folder, img_filename, out_filename])

        # check existence of segmentation file
        if not os.path.exists(out_filename):
            raise FileNotFoundError("Network output file {} not found, "
                                    "check if the segmentation pipeline has failed".format(out_filename))

        # rename file with the indicated output name
        os.rename(out_filename, seg)
        if os.path.exists(seg):
            os.rmdir(os.path.join(out_folder, img_filename))









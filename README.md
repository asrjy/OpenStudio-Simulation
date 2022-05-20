# OpenStudio-Simulation

## Introduction

A modified version of the NREL's Synthetic Building project. 
This script generates the dataset using OpenStudio's Ruby API and OpenStudio-Standards NREL Prototype buildings


## Requirements

- [Openstudio 2.9.1](https://github.com/NREL/OpenStudio/releases/tag/v2.9.1)
- [Ruby 2.2.4](https://github.com/oneclick/rubyinstaller/releases/download/ruby-2.2.4/rubyinstaller-2.2.4-x64.exe)

It is recommended that they all be installed in the same drive as that of this script's location. 


## Instructions to Simulate Data

- Modify Parameters of create_workflow_*.rb script per requirement and run it from the terminal. 
- Create an empty folder called clean_extraction in the parent folder
- Run results_extraction_demo.py in the HelperScripts folder
- Use ResultsExtraction notebook to get a merged csv file. 

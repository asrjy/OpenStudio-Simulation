import openstudio as ost
from pathlib import Path
import os
import shutil
import time
from threading import Thread

def load_osm(path_str):
    translator = ost.osversion.VersionTranslator
    path = ost.path(path_str)
    model = translator.loadModel(path)
    if model.empty:
        print(f"Input: {path_str} is not valid. Please check")
    else:
        model = model.get
    return model

def create_single_model(building_type, vintage, climate_zone, osm_directory):
    model = ost.model.model
    epw_file = "Not Applicable"
    prototype_creator = 

def create_workflows(building_types, vintages, climate_zones, root_directory, epws_path, hash_climate_epw, measures_dir = None, n_runs = 5, efficiency_level = 2):
    Path(root_directory).mkdir(parents = True, exist_ok = True)
    hash_eff_level = {
        '1' : "Low",
        '2' : "Standard",
        '3' : "High"
    }
    out_osw_dir = os.path.join(root_directory, "3-OSWs", f"Efficiency_Level_{hash_eff_level[efficiency_level]}")
    v_osw_paths = []
    for building_type in building_types:
        for climate_zone in climate_zones:
            sub_epws_path = os.path.join(epws_path, hash_climate_epw[climate_zone])
            for vintage in vintages:
                model_name = building_type + "_" + vintage + "_" + climate_zone.split('-')[-1]
                seed_model_folder = os.path.join(root_directory, "1-Seeds", model_name)
                new_model_folder = os.path.join(root_directory, "2-Processed_Models", f"Efficiency_Level_{hash_eff_level[efficiency_level]}", model_name)
                old_osm_path = os.path.join(seed_model_folder, "SR1/in.osm")
                old_epw_path = os.path.join(seed_model_folder, "SR1/in.epw")
                new_osm_path = os.path.join(new_model_folder, f"{model_name}.osm")
                new_epw_path = os.path.join(new_model_folder, f"{model_name}.epw")
                # Creating a raw building model
                create_single_model(building_type, vintage, climate_zone, seed_model_folder)
                # Process Model
                process_model(old_osm_path, new_osm_path, efficiency_level)
                shutil.move(old_epw_path, new_epw_path)
                # Prepare OSW
                v_epw_paths =  [f for f in os.listdir(sub_epws_path) if f.endswith('.epw')]
                v_osw_paths += prepare_all_osws(new_osm_path, v_epw_paths, out_osw_dir, measures_dir, n_runs)            
    f = open(os.join(root_directory, f"job_efficiency_level_{hash_eff_level[efficiency_level]}.txt"), mode = 'w')
    f.write(v_osw_paths)
    f.close
    return v_osw_paths

def process_model(old_osm_path, new_osm_path, efficiency_level = 2):
    osm_dir = os.path.dirname(new_osm_path)
    Path(osm_dir).mkdir(parents = True, exist_ok = True)
    # Change Simulation Run Period to match Weather Data
    model = load_osm(old_osm_path)
    model.getSimulationControl.setRunSimulationforSizingPeriods(False)
    model.getSimulationControl.setRunSimulationforWeatherFileRunPeriods(True)
    # Enable CO2 Simulations
    model.getZoneAirContaminantBalance.setCarbonDioxideConcentration(True)
    # Change the VAV Control Logic to Dual Maximum
    vav_reheats = model.getAirTerminalSingleDuctVAVReheas()
    for vav_reheat in vav_reheats:
        vav_reheat.setDamperHeatingAction('ReverseWithLimits')
    # Change the Efficiency Level 
    model = adjust_efficiency_level(model, efficiency_level)
    # Save processed model
    model.save(new_osm_path, True)    

def adjust_efficiency_level(model, level = 2):
    if level == 2:
        print(f"Keep the default Efficiency Level")
        return model
    elif level == 1:
        print(f"Adjusting to Low Efficiency Level")
        factor = 1.25
    elif level == 3:
        print(f"Adjusting to High Efficiency Level")
        factor = 0.75
    
    # Adjusting Lighting
    v_light_defs = model.getLightsDefinitions()
    for light_def in v_light_defs:
        old_lpd = light_def.wattsperSpaceFloorArea.to_f
        light_def.setWattsperSpaceFloorArea(old_lpd * factor)
    
    # Adjusting MELs
    v_equip_defs = model.getElectricEquipmentDefinitions
    for equip_def in v_equip_defs:
        if equip_def.designLevelCalculationMethod() == "Watts/Area":
            equip_def.setWattsperSpaceFloorArea(float(equip_def.wattsperSpaceFloorArea) * factor)
        elif equip_def.designLevelCalculationMethod() == "EquipmentLevel":
            equip_def.setDesignLevel(float(equip_def.designLevel) * factor)
    
    # Wall Insulation
    v_opaque_materials = model.getStandardOpaqueMaterials()
    for opaque_material in v_opaque_materials:
        opaque_material.setThermalConductivity(float(opaque_material.thermalConductivity) * factor)
    
    # Windows
    v_glazing_materials = model.getGlazings()
    for glazing_material in v_glazing_materials:
        glazing_material.setThickness(float(glazing_material.thickness())/factor)
    
    # Cooling Plant
    v_cooling_coils = model.getCoilCoolingDXTwoSpeeds()
    for cooling_coil in v_cooling_coils:
        cooling_coil.setRatedLowSpeedCOP(float(cooling_coil.ratedLowSpeedCOP)/factor)
        cooling_coil.setRatedHighSpeedCOP(float(cooling_coil.ratedHighSpeedCOP)/factor)
    
    # Heating Plant
    v_heating_coils = model.getCoilHeatingGass()
    for heating_coil in v_heating_coils:
        heating_coil.setGasBurnerEfficiency(min(0.95, float(heating_coil.gasBurnerEfficiency)/factor))
    
    # Reheating Coils
    v_reheating_coils = model.getCoilHeatingElectrics()
    for reheating_coil in v_reheating_coils:
        reheating_coil.setEfficiency(min(1, float(reheating_coil.efficiency)/factor))
    
    # Water Heaters
    v_water_heaters = model.getWaterHeaterMixeds
    for water_heater in v_water_heaters:
        water_heater.setHeaterThermalEfficiency(min(0.95, float(water_heater.heaterThermalEfficiency)/factor))
    
    # Fans
    v_fans = model.getFanVariableVolumnes()
    for fan in v_fans:
        fan.setFanTotalEfficiency(min(0.8, float(fan.fanTotalEfficiency)/factor))
        fan.setMotorEfficiency(min(0.95, float(fan.motorEfficiency)/factor))
    
    # Pumps
    v_pumps = model.getPumpConstantSpeeds()
    for pump in v_pumps:
        pump.setMotorEfficiency(min(0.6, float(pump.motorEfficiency)/factor))
    return model

def prepare_single_osw(seed_osm_path, epw_path, measures_dir, osw_path):
    Path(osw_path).mkdir(parents = True, exist_ok = True)
    osw_str = {
        "weather_file": f"{epw_path}",
        "seed_file": f"{seed_osm_path}",
        "measures_path": [f"measures_dir"], 
        "steps": [
            {"arguments": {},"measure_dir_name": "Occupancy_Simulator_Office"},
            {"arguments": {},"measure_dir_name": "create_lighting_schedule_from_occupant_count"},
            {"arguments": {},"measure_dir_name": "create_mels_schedule_from_occupant_count"},
            {"arguments": {},"measure_dir_name": "update_hvac_setpoint_schedule"},
            {"arguments": {},"measure_dir_name": "add_demand_controlled_ventilation"},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Site Outdoor Air Drybulb Temperature","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Site Outdoor Air Dewpoint Temperature","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Site Outdoor Air Wetbulb Temperature","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Site Outdoor Air Relative Humidity","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Site Horizontal Infrared Radiation Rate per Area","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Site Day Type Index","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"System Node Pressure","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"System Node Temperature","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"System Node Mass Flow Rate","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"System Node Relative Humidity","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"System Node Relative Humidity","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Mean Air Temperature","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Air Relative Humidity","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Thermostat Heating Setpoint Temperature","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Thermostat Cooling Setpoint Temperature","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Air System Outdoor Air Economizer Status","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Air Terminal VAV Damper Position","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone People Occupant Count","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Electric Equipment Electric Power","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Lights Electric Power","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Fan Electric Power","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Fan Air Mass Flow Rate","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Pump Electric Power","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Pump Mass Flow Rate","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddOutputVariable","arguments":{"variable_name":"Zone Mechanical Ventilation Mass Flow Rate","key_value":"*","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"InteriorLights:Electricity","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"InteriorEquipment:Electricity","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Fans:Electricity","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"ExteriorLights:Electricity","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Heating:Electricity","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Cooling:Electricity","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Gas:HVAC","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Electricity:HVAC","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Pumps:Electricity","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Electricity:Facility","reporting_frequency":"timestep"}},
            {"measure_dir_name":"AddMeter","arguments":{"meter_name":"Gas:Facility","reporting_frequency":"timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Site Outdoor Air Drybulb Temperature","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Site Outdoor Air Dewpoint Temperature","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Site Outdoor Air Wetbulb Temperature","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Site Outdoor Air Relative Humidity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Site Horizontal Infrared Radiation Rate per Area","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Site Day Type Index","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"System Node Pressure","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"System Node Temperature","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"System Node Mass Flow Rate","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"System Node Relative Humidity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"System Node Relative Humidity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Mean Air Temperature","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Air Relative Humidity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Thermostat Heating Setpoint Temperature","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Thermostat Cooling Setpoint Temperature","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Air System Outdoor Air Economizer Status","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Air Terminal VAV Damper Position","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone People Occupant Count","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Electric Equipment Electric Power","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Lights Electric Power","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Fan Electric Power","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Fan Air Mass Flow Rate","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Pump Electric Power","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Pump Mass Flow Rate","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportVariabletoCSV","arguments":{"variable_name":"Zone Mechanical Ventilation Mass Flow Rate","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"InteriorLights:Electricity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"InteriorEquipment:Electricity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Fans:Electricity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"ExteriorLights:Electricity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Heating:Electricity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Cooling:Electricity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Gas:HVAC","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Electricity:HVAC","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Pumps:Electricity","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Electricity:Facility","reporting_frequency":"Zone Timestep"}},
            {"measure_dir_name":"ExportMetertoCSV","arguments":{"meter_name":"Gas:Facility","reporting_frequency":"Zone Timestep"}}
        ]
    }
    f = open(osw_path, mode = 'w')
    f.write(osw_str)
    f.close

def prepare_all_osws(seed_osm_path, v_epw_paths, out_osw_dir, measures_dir, n_runs);
    v_osw_paths = []
    seed_osm_name = os.path.splitext(seed_osm_path)[0]
    for epw_path in v_epw_paths:
        epw_name = os.path.splitext(epw_path)[0]
        year = epw_name[-2:-1]
        for i in range(n_runs):
            temp_osw_path = f"{out_osw_dir}/{seed_osm_name}/{epw_name}/run_{i}/{seed_osm_name}_run_{i}.osw"
            prepare_single_osw(seed_osm_path, epw_path, measures_dir, temp_osw_path)
            v_osw_paths.append(temp_osw_path)
    return v_osw_paths


# def run_osws(os_cmd, v_osw_paths, number_of_threads):
#     n = v_osw_paths.length
#     threads = []
#     for n in range(number_of_threads):
#         t = Thread(target=sum, args=(L,))
#         t.start()
#         threads.append(t)

#     # Wait all threads to finish.
#     for t in threads:
#         t.join()

def run_osws_no_multithreading(os_cmd, v_osw_paths):
    n = len(v_osw_paths)
    for index, osw_path in enumerate(v_osw_paths):
        print(f"Running {index+1}/n")
        command = f"{os_cmd} run -w {osw_path}"
        print(command)
        os.system(command)

root_directory = './Models'
measures_dir = './Openstudio-measures'
epws_path = './EPWs'

climate_zones = [
    'ASHRAE 169-2006-1A',
    # 'ASHRAE 169-2006-2A',
    # 'ASHRAE 169-2006-2B',
    # 'ASHRAE 169-2006-3A',
    # 'ASHRAE 169-2006-3B',
    # 'ASHRAE 169-2006-3C',
    # 'ASHRAE 169-2006-4A',
    # 'ASHRAE 169-2006-4B',
    # 'ASHRAE 169-2006-4C',
    # 'ASHRAE 169-2006-5A',
    # 'ASHRAE 169-2006-5B',
    # 'ASHRAE 169-2006-6A',
    # 'ASHRAE 169-2006-6B',
    # 'ASHRAE 169-2006-7A',
    # 'ASHRAE 169-2006-8A',
]

hash_climate_epw = {
    # 'climate zone option':'EPWs folder name', (example convention)
    'ASHRAE 169-2006-1A':'Miami_AMY',
    # 'ASHRAE 169-2006-2A':'Hyderabad',
    # 'ASHRAE 169-2006-3C':'SF_AMY',
    # 'ASHRAE 169-2006-5A':'Chicago_AMY',
}

vintages = [
    # '90.1-2004',
    # '90.1-2007',
    # '90.1-2010',
    '90.1-2013'
]

building_types = [
    ###############################################################
    ## building types that support stochastic occupancy simulation
    ###############################################################
    # 'SmallOffice',
    # 'MediumOffice',
    # 'LargeOffice',
    # 'SmallOfficeDetailed',
    'MediumOfficeDetailed',
    # 'LargeOfficeDetailed',
    ###############################################################
    ## building types that do not support stochastic occupancy simulation
    ###############################################################
    # 'SecondarySchool',
    # 'PrimarySchool',
    # 'SmallHotel',
    # 'LargeHotel',
    # 'Warehouse',
    # 'RetailStandalone',
    # 'RetailStripmall',
    # 'QuickServiceRestaurant',
    # 'FullServiceRestaurant',
    # 'MidriseApartment',
    # 'HighriseApartment',
    # 'Hospital',
    # 'Outpatient',
]

number_of_stochastic_occupancy_simulations = 5

efficiency_level = 2

starting = time.time()

v_osws = create_workflows(building_types = building_types, vintages = vintages, climate_zones = climate_zones, root_directory = root_directory, epws_path = epws_path, hash_climate_epw = hash_climate_epw, measures_dir = measures_dir, n_runs = number_of_stochastic_occupancy_simulations, efficiency_level = efficiency_level)

run_osws_no_multithreading(
    'openstudio', 
    v_osws, 
)

ending = time.time()
elapsed = ending-starting
print(f"Job started at: {starting}, finished at: {ending}, {elapsed} seconds elapsed")
#Filename: pcho_aphillips_a6.py
#Assignment: Business Intelligence Assignment 6
#Date: 04/02/2024
#Description: This file parses the XML Data found at: https://open.canada.ca/data/en/dataset/9ad25a13-b3b6-440f-8053-035f6c3cd9b9
#             into a CSV file that is usable for creating visualizations using Power BI

import xml.etree.ElementTree as ET
import csv
import re

def main():
    structure_file = "Structure_99-012-X2011033.xml"
    source_file = "Generic_99-012-X2011033.xml"
    geo_dict ={}
    sex_dict ={}
    age_dict={}
    noc_dict={}
    # Define the namespace mapping
    namespaces1 = {
        'structure': 'http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure'
    }
    namespaces = {
        'generic': 'http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic'
    }
   
    with open(structure_file, 'rb') as f:
        # Use iterparse to efficiently parse the XML file
        context = ET.iterparse(f, events=('start', 'end'))
        inside_code_list = False
        current_code_list_id = None
        # Iterate over the events
        for event, elem in context:
            # Check if it's the end of a structure:Code element
            if event == 'start' and elem.tag.endswith('CodeList') and elem.tag.startswith('{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}'):
                inside_code_list = True
                current_code_list_id = elem.attrib.get('id')
                
            if event == 'end' and elem.tag.endswith('CodeList') and elem.tag.startswith('{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}'):
                inside_code_list = False
            
            if inside_code_list and event == 'end' and elem.tag.endswith('Code') and elem.tag.startswith('{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}'):
                code_list_id = current_code_list_id  
            
                if code_list_id == 'CL_GEO':
                    dataToWrite = process_geo(elem, namespaces1, geo_dict)
                elif code_list_id == 'CL_SEX':
                    process_sex(elem, namespaces1, sex_dict)
                elif code_list_id == 'CL_AGEGR5':
                    process_age(elem, namespaces1, age_dict)
                elif code_list_id == 'CL_NOC2011':
                    process_noc(elem, namespaces1, noc_dict) 
                       
                elem.clear()

    with open('pcho_aphillips_parsed_data2.csv', 'w', newline='') as csvFile:
        writer = csv.writer(csvFile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
        #Open the XML file for parsing
        with open(source_file, 'rb') as f:
            context = ET.iterparse(f, events=('start', 'end'))        
            
            # Iterate over the events
            for event, elem in context:
                # Check if it's the end of a generic:Series element
                if event == 'end' and elem.tag.endswith('Series') and elem.tag.startswith('{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}'):
                    # Process the Series element
                    
                    dataToProcess = process_series(elem, namespaces)
                    if dataToProcess is not None:
                        dataToWrite = process_data(dataToProcess, geo_dict, sex_dict, age_dict, noc_dict)
                        if dataToWrite is not None:
                            #print(dataToWrite)
                            #dataToWrite = {key: f'"{value}"' for key, value in dataToWrite.items()}
                            writer.writerow(dataToWrite.values() )
                            
                        # Clear the element to free up memory
                    elem.clear()
        print("Done!")

def process_data(data, geo, sex, age, noc):
    data['GEO'] = geo.get(data['GEO'])
    data['Sex'] = sex.get(data['Sex'])
    noc_found = False
    age_found = False

   
    for key, val in noc.items():
        if key ==data['NOC2011'] :
            data['NOC2011'] = val[1]
            noc_found = True
            break

    for key, val in age.items():
        if key ==data['AGEGR5'] :
            data['AGEGR5'] = val
            age_found = True
            break
    
    if age_found is False:
        data=None
    if noc_found is False:
        data=None      
    return data
    

def process_geo(elem, namespaces1, geo_dict):
    # Find the structure:Code element
    if len(elem.attrib.get('value')) == 2:
        code_elem = elem.attrib.get('value')
        description_elem = elem.find('structure:Description', namespaces1)
        geo_dict[code_elem]= description_elem.text.strip()
    
        description_elem.clear()

def process_sex(elem, namespaces1, sex_dict):
    # Find the structure:Code element
    code_elem = elem.attrib.get('value')
    description_elem = elem.find('structure:Description', namespaces1)
    sex_dict[code_elem] = description_elem.text.strip()

    description_elem.clear()
    
def process_age(elem, namespaces1, age_dict):
    # Find the structure:Code element
    code_elem = elem.attrib.get('value')
    description_elem = elem.find('structure:Description', namespaces1)
    
    numbers = re.findall(r'\d+', description_elem.text)

    if len(numbers) > 0:
        if len(numbers) ==2:
            if int(numbers[1]) - int(numbers[0]) ==9:
                age_dict[code_elem] = description_elem.text.strip()
                description_elem.clear()
        elif len(numbers) ==1:
                age_dict[code_elem] = description_elem.text.strip()
                description_elem.clear()    

def process_noc(elem, namespaces1, noc_dict):
    # Find the structure:Code element
    description = elem.find('structure:Description', namespaces1)
    description = description.text.strip()
    noc_split = description.split(" ", 1)
    
    if len(noc_split[0]) ==4:
        code_elem = elem.attrib.get('value')
        description_elem = elem.find('structure:Description', namespaces1)     
        noc_dict[code_elem] = noc_split
    
        description_elem.clear() 
                       
           

def process_series(elem, namespaces):
    # Find the generic:SeriesKey element
    series_key_elem = elem.find('generic:SeriesKey', namespaces)
    # Find the generic:Obs element
    obs_elem = elem.find('generic:Obs', namespaces)

    if series_key_elem is not None and obs_elem is not None:
        # Process the SeriesKey element and check the criteria
        series_key_data = process_series_key(series_key_elem, namespaces)

        # Check the criteria
        if (
            len(series_key_data.get('GEO', '')) == 2 and
            series_key_data.get('Sex') == '1' and
            series_key_data.get('AGEGR5') != '1' and
            series_key_data.get('NOC2011') != '1' and
            series_key_data.get('COWD') in ['2', '3']
        ):
            # Process the Obs element
            obs_data = process_obs(obs_elem, namespaces)
            combinedData = {**series_key_data, **obs_data}
            return combinedData  

        # Clear the elements to free up memory
        series_key_elem.clear()
        obs_elem.clear()

def process_series_key(elem, namespaces):
    # Find all generic:Value elements within the SeriesKey element
    value_elements = elem.findall('generic:Value', namespaces)

    # Extract concept-value pairs and store them in a dictionary
    series_key_data = {}
    for value in value_elements:
        concept = value.get('concept')
        value_value = value.get('value')
        series_key_data[concept] = value_value

    return series_key_data

def process_obs(elem, namespaces):
        
    obs_value_elem = elem.find('generic:ObsValue', namespaces)

    obs_value = obs_value_elem.get('value') if obs_value_elem is not None else None
    
    return {'ObsValue': obs_value}

if __name__ == "__main__":
    main()
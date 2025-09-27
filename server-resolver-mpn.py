from fastapi import FastAPI
from datetime import datetime, timedelta
import subprocess
import re
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from Utils.file_manip import (
    str_to_bool,
    read_yaml_files,
    read_service_orders,
    read_yaml_multifiles,
    extract_sentences,
    read_json,
)

import time, json, re, os, sqlite3
import requests
# Configuration

GITLAB_URL = 'https://gitlab.tech.orange'  # Change if using a self-hosted GitLab
PROJECT_ID = '462351'  # Replace with your project ID
FILE_PATH = ''# Local file path
FOLDER_PATH = 'rfs_gen/Orange_team_team-project'  # Local folder path
BRANCH_NAME = 'main'  # Branch to push to
ACCESS_TOKEN = 'glpat-DWGsY3xyo74b6Z3sEZ6f'
                    #password  #gldt-dgktSozA9JRtXeAeNZRB'  # Your GitLab access token
#repo_url = 'https://gitlab.tech.orange/equipeteam/ai-resolver.git'

examples_rfs_ran_paths = {"urllc": "./intents/ran/urllc/"}

examples_so_ran_paths = {
    "urllc": "./serviceorders/ran/urllc.yaml",
    "embb": "./serviceorders/ran/embb.yaml",
    "miot": "./serviceorders/ran/miot.yaml",
    "supralive_anywhere": "./serviceorders/ran/supralive_anywhere.yaml",
    "supralive_audio_anywhere": "./serviceorders/ran/supralive_audio_anywhere.yaml",
    "supralive_audio_onsite": "./serviceorders/ran/supralive_audio_onsite.yaml",
    "supralive_onsite": "./serviceorders/ran/supralive_onsite.yaml",
    "faas": "./serviceorders/ran/faas.yaml",
    "vr": "./serviceorders/ran/vr.yaml",
    "hopital": "./serviceorders/ran/hopital.yaml",
}

examples_rfs_core_paths = {
    # "shared": "./intents/core/01-shared-cn/",
    # "mpn1": "./intents/core/02-mpn1/",
    # "mpn2": "./intents/core/03-mpn2/",
    "urllc": "./intents/core/urllc/",
}
target_rfs_core_paths = {
    # "mpn3": "./intents/core/04-mpn3/",
    "embb": "./intents/core/embb/",
}

target_rfs_core = {}
for key in target_rfs_core_paths:
    target_rfs_core[key] = read_yaml_multifiles(target_rfs_core_paths[key])

examples_so_core_paths = {
    "shared": "./serviceorders/core/Shared_network.yaml",
    "mpn1": "./serviceorders/core/MPN1.yaml",
    "mpn2": "./serviceorders/core/MPN2.yaml",
    "mpn3": "./serviceorders/core/MPN3.yaml",
    "urllc": "./serviceorders/ran/urllc.yaml",
    "embb": "./serviceorders/ran/embb.yaml",
    "miot": "./serviceorders/ran/miot.yaml",
    "supralive_anywhere": "./serviceorders/ran/supralive_anywhere.yaml",
    "supralive_audio_anywhere": "./serviceorders/ran/supralive_audio_anywhere.yaml",
    "supralive_audio_onsite": "./serviceorders/ran/supralive_audio_onsite.yaml",
    "supralive_onsite": "./serviceorders/ran/supralive_onsite.yaml",
    "faas": "./serviceorders/ran/faas.yaml",
    "vr": "./serviceorders/ran/vr.yaml",
    "hopital": "./serviceorders/ran/hopital.yaml",
}

extracted_rfs_ran = {}
extracted_so_ran = {}

extracted_rfs_core = {}
extracted_so_core = {}

for key in examples_rfs_ran_paths:
    extracted_rfs_ran[key] = read_yaml_multifiles(examples_rfs_ran_paths[key])
# print(extracted_rfs_ran)
for key in examples_so_ran_paths:
    extracted_so_ran[key] = read_service_orders(examples_so_ran_paths[key])

for key in examples_rfs_core_paths:
    extracted_rfs_core[key] = read_yaml_multifiles(examples_rfs_core_paths[key])
# print(extracted_rfs_core)

for key in examples_so_core_paths:
    extracted_so_core[key] = read_service_orders(examples_so_core_paths[key])


# Define the data models
class ServiceCharacteristic(BaseModel):
    id: str
    valueType: str
    value: Any

class Place(BaseModel):
    id: str
    role: str



# class OrderItem(BaseModel):
#     id: str
#     action: str
#     state: str
#     service: Service

# class Products(BaseModel):
#     description: str
#     orderItem: List[OrderItem]

class Service(BaseModel):
    type: str = Field(..., alias="@type")
    state: str
    serviceType: str
    serviceCharacteristic: List[ServiceCharacteristic]
    place: Place

class orderItem(BaseModel):
    id: str
    action: str
    state: str
    service: Service
class Test(BaseModel):
    description: str
    usecase: str | None = None
    customer: str | None = None
    company: str | None = None
    orderItem: List[orderItem]




services_order = {}
service_characs = {}

app = FastAPI()

@app.get("/")
async def hello():
    return {"message": "CFS for 5G RAN services"}

# Endpoint to create each service and its characteristics
# @app.get("/")
# async def index(data: Products):
#     return {"message": "CFS for 5G RAN services"}

def Gemini_response(intent,service,result):
    level = "core" # "ran" "core" "e2e", change to e2e if we want to include RAN
    api_key = "AIzaSyA7vi8e_CegPjy8506Bo-rcAzDyAM8Nn_0"  # GEMINI v1.5P
    llm = ChatGoogleGenerativeAI(
        api_key=api_key,
        model="gemini-2.5-pro",
        temperature=0.2,
        top_k=20,
        top_p=0.8,
        max_tokens=None,
        timeout=None,
        # max_retries=6,
    )
    hello_system_ran = [
        (
            "system",
            """You are a 5G RAN expert, your mission is to translate a service order to Resource-Facing Service (RFS) for Open RAN. 
                The list of 5G functions for which you need to generate for the RFS. 
                    - centralized unit - control plane (cu-cp). 
                    - centralized unit - user plane (cu-up). 
                    - decentralized unit (du). 
                    - radio unit (ru). 
                For the request order, it follows TMF641 API request. """,
        )
    ]
    twoshot_prompt_ran_examples = [
        (
            "human",
            " Translate this request order for URLLC service: {so_urllc} into Resource-Facing Service (RFS) values at OpenRAN level",
        ),
        ("ai", "Here is the RFS translated from the request order: {rfs_urllc}"),
        (
            "human",
            "How to calculate the min/max number of Resource Elements (REs) in downlink/uplink of du function with Numerology (N) = 1, which are  based on 3GPP 38.306?",
        ),
        (
            "ai",
            """Given that:
                - Throughput (T): The min/max target data throughput per user from service order: minDlTputRequirement = 1Mbps;  
                                                                                                maxDlTputRequirement = dlTputRequirement*(1+ maxTputVariation/100) = 1.1Mbps; 
                                                                                                minUlTputRequirement = 0.1Mbps; 
                                                                                                maxUlTputRequirement = ulTputRequirement*(1+ maxTputVariation/100) = 1.1Mbps.
                - Modulation and Coding Scheme (MCS = 12): To determine Modulation order (Q = 4), Target code rate (R = 434/1024) based on 3GPP 38.306.
                - Number of MIMO Layers (NL) = 1.
                - Overhead (O): Control signaling overhead: 0.14 for Downlink and 0.08 for Uplink.
                - Numerology (N) = 1
                - Then, we calculate min/max number of REs in downlink/uplink:
                        - minREDl = minDlTputRequirement*1000/(NL*Q*1*R*14*2^N*(1 - O)) = 24.49 -> 25 REs
                        - maxREDl = maxDlTputRequirement*1000/(NL*Q*1*R*14*2^N*(1 - O)) = 26.95 -> 27 REs
                        - minREUl = minUlTputRequirement*1000/(NL*Q*1*R*14*2^N*(1 - O)) = 2.29 -> 3 REs
                        - maxREUl = maxUlTputRequirement*1000/(NL*Q*1*R*14*2^N*(1 - O)) = 25.19 -> 26 REs""",
        ),
    ]

    hello_system_core = [
        (
            "system",
            """You are a 5G Core expert, your mission is to translate a service order to Resource-Facing Service (RFS). 
                The list of 5G functions for which you need to generate for the RFS: 
                    - Access and Mobility Management Function (AMF). 
                    - Authentication Server Function (AUSF). 
                    - Network Repository Function (NRF). 
                    - Network Slice Selection Function (NSSF). 
                    - Policy Control Function (PCF)
                    - Unified Data Management (UDM)
                    - Unified Data Repository (UDR)
                    - Session Management Function (SMF)
                    - User Plane Function (UPF)
                For the request order, it follows TMF641 API request. """,
        )
    ]

    twoshot_prompt_core_examples = [
        (
            "human",
            " Translate this request order for URLLC service into Resource-Facing Service (RFS) for 5G Core network: {so_urllc} ",
        ),
        (
            "ai",
            """Given that: 
            - 5qi field in the RFS correspond to the threeGpp5Qi field in the service order
            - sst (service slice type) field in the RFS correspond to the sst in the service order. 
            The mapping from sst value to sst type is based on 3GPP 23.501 as follows:
             For sst value = 1, the service type is eMBB.
             For sst value = 2, the service type is URLLC.
             For sst value = 3, the service type is mIOT.
             For sst value = 4, the service type is V2X.
             For sst value = 5, the service type is HMTC.
                """,
        ),
        ("ai", "The RFS translated for 5G Core network is given as follows: {rfs_urllc}"),
    ]
    
    prompt_mpn = [
        (
            "system",
            """you are a service resolver Agent, if a client ask you to generate a new MPN for a 5G service, you create and modify the following files included in the documentation:

            - you create a  new UPF for the client following the same content and values of this YAML:
            apiVersion: config.porch.kpt.dev/v1
            kind: Rfs
            metadata:
            name: upf(i)
            namespace: rim

            spec:
            provider:
                name: upf
                vendor: free5gc

            destination: vdr

            parameters:
                dnn:
                - name: "internet"
            - you create a  new SMF for the client based on the same content and values of this YAML:
            apiVersion: config.porch.kpt.dev/v1
            kind: Rfs
            metadata:
            name: smf(i)
            namespace: rim

            spec:
            provider:
                name: smf
                vendor: free5gc

            destination: vdr

            parameters:
                plmn:
                - plmnid:
                    mcc: ""
                    mnc: ""
                    nssai:
                    - sst: 
                        sd: ""
                        dnn:
                        - name: "internet"
                dnn:
                - name: "internet"
            - you create a new AMF for the client  based on the same content and values of this YAML: 
            apiVersion: config.porch.kpt.dev/v1
            kind: Rfs
            metadata:
            name: amf(i)
            namespace: rim

            spec:
            provider:
                name: amf
                vendor: free5gc

            destination: vdr

            parameters:
                plmn:
                - plmnid:
                    mcc: ""
                    mnc: ""
                    nssai:
                    - sst: 
                        sd: ""
                    tac:
                    - "000001"
                dnn:
                - name: "internet"

            - you create a new NSSF for the client  based on the same content and values of the file nssf1-rfs.txt  
            apiVersion: config.porch.kpt.dev/v1
            kind: Rfs
            metadata:
            name: nssf(i)
            namespace: rim

            spec:
            provider:
                name: nssf
                vendor: free5gc

            destination: vdr

            parameters:
                plmn:
                - plmnid:
                    mcc: ""
                    mnc: ""
                    nssai:
                    - sst: 
                        sd: ""
            - you modify the nssai with the new sst and sd values provided by the client



            the mcc and mnc values provided by the client  
            the sst and sd values are provided by the client 
            the (i) is changed for 1 in case of MPN1 in every function
            if the client wants an MPN2, the AMF file would be like (it contains two sst and two st) for each MPN 1 and two:
            apiVersion: config.porch.kpt.dev/v1
            kind: Rfs
            metadata:
            name: amf1
            namespace: rim

            spec:
            provider:
                name: amf
                vendor: free5gc

            destination: vdr

            parameters:
                plmn:
                - plmnid:
                    mcc: "208"
                    mnc: "91"
                    nssai:
                    - sst: 
                        sd: ""
                    - sst: 
                        sd: ""
                    tac:
                    - "000001"
                    - "000002"
                dnn:
                - name: "internet"
                - name: "orange"
            provide the output with the four yaml files of the functions in order upf,smf,amf and nssf.
            """



        )



    ]

    user_inputs = [("human", "{input}")]
    dir = f"rfs_gen/Orange_team_team-project"
    if not os.path.exists(dir):
        os.makedirs(dir)
    delay_ran = 0.0
    if level=="ran" or level=="e2e":
        messages_ran = hello_system_ran + twoshot_prompt_ran_examples + user_inputs
        prompt_ran = ChatPromptTemplate.from_messages(messages_ran)
        input_ran = {
            "rfs_urllc": extracted_rfs_ran["urllc"],
            "so_urllc": extracted_so_ran["urllc"],
            "input": f"""Provide me RFS configuration in json format for a 5G RAN service, with service order given in : {intent}. 
                            Also, provide me the calculation of maxREDl, minREDl, maxREUl and minREUl in du function with numerology N=1.
                            """,
        }
        chain_ran = prompt_ran | llm

        start_inf_ran = time.time()
        response_ran = chain_ran.invoke(input_ran)
        end_inf_ran =time.time()
        print("*******response (RAN):", response_ran)
        json_string_ran = (
                    response_ran.content.split("```")[1].split("json")[1].strip()
                )
        meta_data = response_ran.usage_metadata
        input_tokens_ran = meta_data.get("input_tokens")
        output_tokens_ran = meta_data.get("output_tokens")
        total_tokens = meta_data.get("total_tokens")
        print("Input tokens (RAN): ", input_tokens_ran)
        print("Output tokens (RAN): ", output_tokens_ran)
        print("Total tokens (RAN): ", total_tokens)
        print("*** json_string_ran", json_string_ran)
        data_ran = json_string_ran
        # formatted_json_ran = json.dumps(json_string_ran, indent=2)
        # print(formatted_json_ran)
        try:
            data_ran_json = json.loads(data_ran)
        except json.JSONDecodeError as e:
            # Use regex to identify problematic patterns
            invalid_field= re.findall(r'\[.*?\]', data_ran)  # Matches anything in square brackets
            if invalid_field:
                print("Non-conforming fields found:")
                data_ran = re.sub(r'\[.*?\]', '"calculated"', data_ran)
                data_ran_json = json.loads(data_ran)
            else:
                print("No specific invalid patterns detected.")
        try:
            now = datetime.now()
            with open(
                f"{dir}/ran_rfs_{service}_{now}.json",
                "w",
            ) as json_file:
                json.dump(data_ran_json, json_file, indent=4)
        except json.JSONDecodeError as e:
            print("Error at loading saving ran: ", e)
        delay_ran = end_inf_ran - start_inf_ran
    delay_core = 0.0
    if level=="core" or level=="e2e":
        messages_core = hello_system_core + twoshot_prompt_core_examples + user_inputs
        
        prompt_core = ChatPromptTemplate.from_messages(messages_core)
        
        
        input_core = {
                "rfs_urllc": extracted_rfs_core["urllc"],
                "so_urllc": extracted_so_core["urllc"],
                "input": f"""Provide me RFS configuration in json format for a 5G Core network, with service order given in : {intent}. 
                                """,
            }
        
        chain_core = prompt_core | llm
        start_inf_core = time.time()
        # response_ran = chain_ran.invoke(input_ran)
        response_core = chain_core.invoke(input_core)
        end_inf_core =time.time()
        json_string_core = (
                response_core.content.split("```")[1].split("json")[1].strip()
            )
        meta_data_core = response_core.usage_metadata
        input_tokens_core = meta_data_core.get("input_tokens")
        output_tokens_core = meta_data_core.get("output_tokens")
        total_tokens_core = meta_data_core.get("total_tokens")
        print("Input tokens (Core): ", input_tokens_core)
        print("Output tokens (Core): ", output_tokens_core)
        print("Total tokens (Core): ", total_tokens_core)
        print("*** json_string_core", json_string_core)
        data_core = json_string_core
        json_proc = True
        try:
            data_core_json = json.loads(data_core)
            formatted_json_core = json.dumps(json_string_core, indent=2)
            now = datetime.now()
            with open(
                f"{dir}/core_rfs_{service}_{now}.json",
                "w",
            ) as json_file:
                json.dump(data_core_json, json_file, indent=4)
            candidate_Core = data_core_json
            if "MPN3" in candidate_Core:
                candidate_Core = candidate_Core["MPN3"]
            elif "mpn3" in candidate_Core:
                candidate_Core = candidate_Core["mpn3"]
        except json.JSONDecodeError as e:
            print("Error at loading data core: ", e)
            candidate_Core = json_string_core
            json_proc = False
        delay_core = end_inf_core - start_inf_core

    if level=="core" and result['isolation']=="Isolation":
        messages_mpn = prompt_mpn
        mpn_number = 2 #the number of the deployed MPN
        prompt_mpn_core = ChatPromptTemplate.from_messages(messages_core)
        input_mpn = {
            "input": f""" I want to create an MPN{mpn_number} 5G service with sst:{result['sst_id']} , sd: "654321", mns: "91", mcc: "208" the values for MPN1 for sst and sd are: sst: 1 sd: "123456".
                            """,
        }
        chain_mpn_core = prompt_mpn_core | llm
        start_inf_core = time.time() 
        response_mpn_core = chain_mpn_core.invoke(input_mpn)
        end_inf_core =time.time()

        # Définir les noms des fichiers
        file_names = ["upf2-rfs.yaml", "smf2-rfs.yaml", "amf2-rfs.yaml", "nssf2-rfs.yaml"]

        # Expression régulière pour capturer les blocs YAML
        yaml_pattern = re.compile(r"```yaml(.*?)```", re.DOTALL)

        # Trouver tous les blocs YAML
        yaml_blocks = yaml_pattern.findall(response_mpn_core)

        # Vérifier si nous avons bien 4 blocs
        if len(yaml_blocks) != 4:
            print(f"Nombre de blocs YAML trouvés : {len(yaml_blocks)}. Vérifiez votre sortie.")
        else:
            # Enregistrer chaque bloc dans un fichier
            
            for i, block in enumerate(yaml_blocks):
                with open(f"{dir}/{file_names[i]}", 'w') as f:
                    f.write(block.strip())
                    print(f"{file_names[i]} enregistré avec succès.")
        delay_core = end_inf_core - start_inf_core


    delay = delay_ran+delay_core
    return delay

def convert_sst_name_to_id(sst_name: str):
    #convert all uppercase to lowercase
    sst_name=sst_name.lower()
    match sst_name:
        case "embb":
            return 1
        case "urllc":
            return 2
        case "miot":
            return 3
        case "v2x":
            return 4
        case "hmtc":
            return 5
        case _:
            return 1
        

def get_serviceInfo_by_Id(item_id: str, service:Service):
    for item in service.serviceCharacteristic:
        if item.id == item_id:
            return item.value
    return None

def submit_to_git():
    # Read the file content
    with open(FILE_PATH, 'r') as file:
        file_content = file.read()

    # Prepare the API request
    api_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/repository/files/{FILE_PATH}"
    headers = {
        'PRIVATE-TOKEN': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    data = {
        'branch': BRANCH_NAME,
        'content': file_content,
        'commit_message': 'Add file via API'
    }

    # Make the API request
    response = requests.post(api_url, headers=headers, json=data)
    # Check the response
    if response.status_code == 201:
        print("File pushed successfully!")
    else:
        print(f"Failed to push file: {response.status_code} - {response.text}")

def push_file_to_gitlab(file_path):
    # Read the file content
    with open(file_path, 'r') as file:
        file_content = file.read()

    # Prepare the API request
    api_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/repository/files/{file_path}"
    print(api_url) 
    headers = {
        'PRIVATE-TOKEN': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    data = {
        'branch': BRANCH_NAME,
        'content': file_content,
        'commit_message': f'Add {os.path.basename(file_path)} via API'
    }

    # Make the API request
    response = requests.post(api_url, headers=headers, json=data)

    # Check the response
    if response.status_code == 201:
        print(f"File {file_path} pushed successfully!")
    else:
        print(f"Failed to push file {file_path}: {response.status_code} - {response.text}")

#Iterate through the folder and push each file
def read_file_and_push(FOLDER_PATH=''):
  #for root, dirs, files in os.walk(FOLDER_PATH):
  #for file in files:
        #file_path = os.path.join(root, file)
        
        #relative_pat_ = os.path.relpath(file_path, FOLDER_PATH)
        # Préfixer avec "rfs_gen/"
        #gitlab_path = os.path.join("rfs_gen", relative_path)
        #push_file_to_gitlab(gitlab_path)
        #push_file_to_gitlab(relative_path)
  commit_message = f"New generated RFSs are created for your use case"
  subprocess.run(["git", "add", "."], cwd=FOLDER_PATH)
  subprocess.run(["git", "commit", "-m", commit_message], cwd=FOLDER_PATH)
  subprocess.run(["git", "push", "-u", "origin", "main"], cwd=FOLDER_PATH)


@app.post("/cfs_prods/")
async def create_cfs_prod(prod: Test):
    # print(data)
    # for item in prod.orderItem:
    # print("Customer", prod.customer)
    # print("Product: ", prod)
    result = {}
    print("activationDate: ", get_serviceInfo_by_Id(item_id="activationDate", service=prod.orderItem[0].service))
    sst_name = get_serviceInfo_by_Id(item_id="sst", service=prod.orderItem[0].service)
    print("sst name: ", sst_name )
    sst_id = convert_sst_name_to_id(sst_name)
    print("sst id: ", sst_id )
    result['sst_id'] = sst_id 
    try:
        service_characteristics = prod['orderItem'][0]['service']['serviceCharacteristic']
        
        # Search for isolation and sst values
        for characteristic in service_characteristics:
            if characteristic['id'] == 'IsolationLevel':
                result['isolation'] = characteristic['value']
        
    
    except (KeyError, IndexError) as e:
        print(f"Error accessing JSON structure: {e}")
        return None
    threegpp_5qi = get_serviceInfo_by_Id(item_id="threeGpp5Qi", service=prod.orderItem[0].service)
    print("threegpp_5qi: ", threegpp_5qi )

    # print("service Characteristics: ", prod.orderItem[0].service.serviceCharacteristic[0])
    delay=0.0
    delay = Gemini_response(prod,sst_name,result)
    read_file_and_push(FOLDER_PATH)
    return{
        "message": "CFS is succesfully handled to Service Resolver, RFS RAN and Core are translated!",
        "item_details": {
            # "name": prod.orderItem[0].id,
            "description": prod.description,
            "sst_name": sst_name,
            "sst_id": sst_id,
            "threegpp_5qi": threegpp_5qi,
            "Total inference delay (RAN + Core)": delay

        }
    }
    # return {"message": "CFS is succesfully handled to Service Resolver!"}
#     for order_item in data.orderItem:
#         # Create the service
#         service = order_item.service
#         services.append(service)

#         # Create each serviceCharacteristic
#         for characteristic in service.serviceCharacteristic:
#             service_characteristics.append(characteristic)

#     return {
#         "message": "Items created successfully",
#         "services": services,
#         "service_characteristics": service_characteristics
#     }

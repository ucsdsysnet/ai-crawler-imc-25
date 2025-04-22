import json
import pandas as pd
import pickle
import gzip
import subprocess
import os
import uuid
import argparse
import random
import string


def pickle_load(file, compress=False):
    if file.endswith(".gz") or compress:
        with gzip.open(file, "rb") as f:
            d = pickle.loads(f.read())
    else:
        d = pickle.load(open(file, "rb"))
    return d
import glob

def load_all_data(dir="results-full2/*"):
    file_paths = glob.glob("results-full2/*")
    # print(file_paths)
    d = {}
    # ['results-full2/all_meta_data-CC-MAIN-2024-26-8000.p.gz']
    for path in file_paths:
        t = pickle_load(path)
        for url in t:
            partition  = list(t[url].keys())[0]
            if url not in d:
                d[url] = {}
            d[url][partition] = t[url][partition]
    return d


def load_one_file(path):
    d = {}
    # ['results-full2/all_meta_data-CC-MAIN-2024-26-8000.p.gz']
    t = pickle_load(path)
    for url in t:
        partition  = list(t[url].keys())[0]
        if url not in d:
            d[url] = {}
        d[url][partition] = t[url][partition]
    return d


def get_robots_from_partition(partition, d):
    print('loading partion', partition)
    all_robots = {}
    no_robots = {}
    for url in d:
        if partition in d[url]:
            if 'content' in d[url][partition]:
                #TODO: record case where there is no robots.txt 
                all_robots[url] = d[url][partition]['content']
            else:
                no_robots[url] = d[url][partition]
    # print(len(d))
    return all_robots, no_robots

# enumerate all paths provided in robots.txt
def get_all_paths_from_robots(robots_content, delimiter='\n'):
    all_paths = set()

    if delimiter is not None:
        robots_content = robots_content.split(delimiter)

    for line in robots_content:
        if "disallow: " in line.lower() or "allow: " in line.lower():
            splitted = line.split()
            if len(splitted) < 2:
                # print("ERROR! Invalid Line", line, robots_content)
                continue
            all_paths.add(splitted[1])
        elif "disallow:" in line.lower() or "allow:" in line.lower():
            splitted = line.split(":")
            if len(splitted) < 2:
                # print("ERROR! Invalid Line", line, robots_content)
                continue
            all_paths.add(splitted[1])
    all_paths.add("/")  # add root path no matter what
    return list(all_paths)

def get_url2paths(all_robots):
    url2paths = {}
    for url in all_robots:
        url2paths[url] = get_all_paths_from_robots(all_robots[url])
    return url2paths


ROBOTS_PARSER_PATH = "robotstxt/c-build/robots"


def check_bot_access(robots_txt_path, botname, full_url):
    """
    Args:
    robots_txt_path (str): Path to the robots.txt file.
    botname (str): The name of the bot (e.g., 'Googlebot').
    full_url (str): The full URL that the bot wants to access.
    
    Returns:
    bool: True if the bot is allowed, False otherwise.
    """
    
    try:
        # Run the command using subprocess
        command = ['./' + ROBOTS_PARSER_PATH, robots_txt_path, botname, full_url]
        result = subprocess.run(command, capture_output=True, text=True)
        # output = result.stdout
        code = result.returncode
        # print(code, output)
        
        # check the return code for the results
        if code == 0:
            return True  # bot is allowed
        elif code == 1:
            return False  # bot is disallowed
        return None  # error parsing robots.txt

    except subprocess.CalledProcessError as e:
        print(f"Error running the command: {e}")
        return False

def get_path_permissions(all_paths, useragent, filepath, url):
    path_permissions = {}
    if url[-1] == '/': # remove trailing slash
        url = url[:-1]
    for path in all_paths:
        # check if path has the ending marker ($)
        if len(path) > 0 and path[-1] == '$':
            path = path[:-1]  # if yes, remove the ending marker.
        full_path = url + path
        # print(robots_path, useragent, full_path)
        path_permissions[path] = check_bot_access(filepath, useragent, full_path)
        # print(path)
    return path_permissions

def get_url2pathpermissions(url2robots, url2paths, useragent):    
    url2pathpermissions = {}
    for url in url2robots:
        robots_content = url2robots[url]
        with open("robots_tmp.txt", 'w') as fp:
            fp.write(robots_content)
        url2pathpermissions[url] = get_path_permissions(url2paths[url], useragent, "robots_tmp.txt", url)
    return url2pathpermissions

def get_judgements(url2pathperm):
    results = {}
    for url in url2pathperm:
        # beginning settings:
        fully_disallowed = True
        partially_disallowed = False
        no_restrictions = True

        for path in url2pathperm[url]:
            # if path not in url2paths[url]:
            #     continue # skip extraneous paths
            if url2pathperm[url][path] == False: # any of the paths is disallowed
                partially_disallowed = True
                no_restrictions = False
            elif url2pathperm[url][path] == True: # any of the paths is allowed
                fully_disallowed = False
        results[url] = {"fully_disallowed": fully_disallowed, "partially_disallowed": partially_disallowed, "no_restrictions": no_restrictions}

    return results

def get_all_partitions_from_dict(d):
    partitions = set()
    for _, partition in d.items():
        # print(partition.keys())
        partitions.add(list(partition.keys())[0])
    print(partitions)
    return partitions


def save_metadata(filename, info):
    with open("metadata.json", 'r') as fp:
        metadata = json.load(fp)

    metadata[filename] = info

    with open("metadata.json", 'w') as fp:
        json.dump(metadata, fp)


def get_judgement_amortized(url, url_paths, robots_path, user_agent):
    if url[-1] == '/': # remove trailing slash
        url = url[:-1]

    # append a dummy path for the edge case where everything is disallowed except for "/$" (because just '/' would be allowed)
    url_paths.append('/dummy-testing-path-54321')

    # initialize everything to false
    fully_disallowed = False
    partially_disallowed = False
    no_restrictions = False

    # first, check the / path 
    slash_results = check_bot_access(robots_path, user_agent, url+'/')
    if slash_results == True: # the / is allowed
        # print("slash is allowed")
        for path in url_paths:
            # check if path has the ending marker ($)
            if path == '/':
                continue # skip over the / as we have already checked it
            if len(path) > 0 and path[-1] == '$':
                path = path[:-1]  # if yes, remove the ending marker.
            # print("testing path", path)
            # res = check_bot_access(robots_path, user_agent, url+path)
            # print(url+path, res)
            if check_bot_access(robots_path, user_agent, url+path) == False:  # found a disallowed path
                partially_disallowed = True
                return {
                    "fully_disallowed": False,
                    "partially_disallowed": True,
                    "no_restrictions": False
                }
        # finished checking all the paths, and none are disallowed
        return {
            "fully_disallowed": False,
            "partially_disallowed": False,
            "no_restrictions": True
        }
    elif slash_results == False: # the / is disallowed
        # print("slash is disallowed")
        for path in url_paths:
            # print("testing path", path)
            if path == '/':
                continue # skip over the / as we have already checked it
            if len(path) > 0 and path[-1] == '$':
                path = path[:-1]  # if yes, remove the ending marker.
            # print("testing path", path)
            # res = check_bot_access(robots_path, user_agent, url+path)
            # print(url+path, res)
            if check_bot_access(robots_path, user_agent, url+path) == True: # found an allowed path
                partially_disallowed = True
                return {
                    "fully_disallowed": False,
                    "partially_disallowed": True,
                    "no_restrictions": False
                }
        # finished checking all the paths, and all are disallowed
        return {
            "fully_disallowed": True,
            "partially_disallowed": False,
            "no_restrictions": False
        }
    

def get_judgements_dummy():
    return "hi!"



def load_one_partition(snapshot):
    with open("final_cc_data/"+snapshot+".json") as fp:
        d = json.load(fp)
    return d

def process_one_file_amortized(filename, useragent, snapshot, robots_file='testrobots-1.txt'):
    # d = load_one_file(filename)
    d = load_one_partition(snapshot)
    robots_file = 'robots_'+snapshot+'.txt'
    print("length of data in file:", len(d))
    # partitions = get_all_partitions_from_dict(d)
    # print("number of partitions in data:", len(partitions))

    # for partition in partitions:
    #     all_robots, no_robots  = get_robots_from_partition(partition, d)
    #     print("lenth of all robots.txt from partition:", partition, len(all_robots))
    #     print("length of sites with no robots.txt", len(no_robots))

    all_robots = {}
    for url in d:
        if not isinstance(d[url], dict):
            all_robots[url] = d[url]
    
    UA = useragent
    url2paths = get_url2paths(all_robots)

    robots_judgements = {}
    for url in all_robots:
        with open(robots_file, "w") as f:
            f.write(all_robots[url])
        robots_judgements[url] = get_judgement_amortized(url, url2paths[url], robots_file, useragent)
        # robots_judgements[url] = get_judgements_dummy()

    file_name = "robots_results/final_judgements/" + useragent + "_" + snapshot + ".json"
    print("saving results to", file_name)
    with open(file_name, 'w') as f:
        json.dump(robots_judgements, f)

    # save_metadata(filename, info)

def save_metadata(filename, info):
    try:
        with open("metadata-final.json", 'r') as fp:
            metadata = json.load(fp)
    except:
        with open("metadata-final.json", 'w') as fp:
            json.dump({})  # init json file if not exist.

    metadata[filename] = info

    with open("metadata-final.json", 'w') as fp:
        json.dump(metadata, fp)



def generate_random_string(length=5):
    # Define the characters to choose from (uppercase, lowercase, digits)
    characters = string.ascii_letters + string.digits
    # Generate a random string of the specified length
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def divide_list(input_list, num_segments=6):
    # Calculate the length of each segment
    avg_length = len(input_list) / float(num_segments)
    print(len(input_list), num_segments)
    segments = []
    last = 0.0

    while last < len(input_list):
        segments.append(input_list[int(last):int(last + avg_length)])
        last += avg_length

    return segments


if __name__== '__main__':
    parser = argparse.ArgumentParser(description="analyze robots.txt files")
    parser.add_argument("useragent")
    parser.add_argument("snapshot")
    args = parser.parse_args()


    process_one_file_amortized("test", args.useragent, args.snapshot)

    # file_paths = glob.glob("robots_analysis/results-full2/*")
    # segments = divide_list(list(file_paths))

    # # Set up argument parsing
    # parser = argparse.ArgumentParser(description="analyze robots.txt files")
    # parser.add_argument("useragent")
    # parser.add_argument("robots_temp_file")
    # parser.add_argument("segment")

    # # Parse arguments
    # args = parser.parse_args()

    # for fp in segments[int(args.segment) - 1]:
    #     process_one_file_amortized(fp, args.useragent, args.robots_temp_file)
    

import re
import ipaddress
from collections import defaultdict
import tldextract
from imc25_defs import OPENAI_IP_RANGES, APPLEBOT_IP_RANGES, META_IP_RANGES

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) - - \[(?P<timestamp>[^\]]+)] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) \S+ "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]+)"'
)


def load_agents_from_file(file_path):
    with open(file_path, 'r') as f:
        # ignore lines that start with #
        agents_in_string = [line.strip() for line in f.readlines() if not line.startswith("#") if len(line.strip()) > 0]
        agents_and_their_type = [line.split(",") for line in agents_in_string]
        # get agents per group
        ai_data_crawler = []
        ai_search_crawler = []
        ai_assistant_crawler = []
        ai_undocumented_crawler = []
        all_ai_cralwers = []
        for agent in agents_and_their_type:
            if len(agent) == 2:
                all_ai_cralwers.append(agent[0])
                if agent[1].lower() == "ai-data-crawler":
                    ai_data_crawler.append(agent[0])
                elif agent[1].lower() == "ai-search-crawler":
                    ai_search_crawler.append(agent[0])
                elif agent[1].lower() == "ai-assistant-crawler":
                    ai_assistant_crawler.append(agent[0])
                elif agent[1].lower() == "undocumented-crawler":
                    ai_undocumented_crawler.append(agent[0])
            else:
                raise ValueError(f"Invalid agent format: {agent}")
        return all_ai_cralwers, ai_data_crawler, ai_search_crawler, ai_assistant_crawler, ai_undocumented_crawler

def read_log_with_path(log_path):
    with open(log_path, 'r') as f:
        logs = f.readlines()
        return logs

def read_conversation_data_given_app_infos(app_infos, conversation_data_path):
    # pass

    pass

def parse_log(log, print_error = False):
    global LOG_PATTERN
    parsed = {}
    match = LOG_PATTERN.match(log)
    if match:
        log_data = match.groupdict()  # Extract all matched groups as a dictionary
        ip = log_data['ip']
        timestamp = log_data['timestamp']
        method = log_data['method']
        path = log_data['path']
        protocol = log_data['protocol']
        status = log_data['status']
        user_agent = log_data['user_agent']
        parsed = {
            'ip': ip,
            'timestamp': timestamp,
            'method': method,
            'path': path,
            'protocol': protocol,
            'status': status,
            'user_agent': user_agent
        }
    else:
        # Seems fine
        if print_error:
            print(f"Parsing Error: Log line does not match pattern: {log}")
        return None
        # raise ValueError(f"Log line does not match pattern: {log}")
    return parsed


def is_ip_in_openai(ip):
    return is_ip_official(ip, "oai")

def is_ip_official(ip, company_or_user_agent):
    # if ip is string, convert to ipaddress object
    if isinstance(ip, str):
        try:
            ip = ipaddress.ip_address(ip)
        except ValueError:
            # Invalid IP address format
            raise ValueError(f"Invalid IP address format: {ip}")
    elif not isinstance(ip, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        # Invalid type
        raise TypeError(f"IP address must be a string or an ipaddress object: {ip}")
    # Check if the IP address is in any of the OpenAI IP ranges
    ip_obj = ipaddress.ip_address(ip)
    if company_or_user_agent.lower() in ["openai", "oai", "gptbot", "chatgpt-user", "oai-searchbot"]:
        return any(ip_obj in ip_range for ip_range in OPENAI_IP_RANGES)
    elif company_or_user_agent.lower() in ["applebot","apple"]:
        return any(ip_obj in ip_range for ip_range in APPLEBOT_IP_RANGES)
    elif company_or_user_agent.lower() in ["meta", "metabot", "meta-externalagent", "meta-externalfetcher"]:
        return any(ip_obj in ip_range for ip_range in META_IP_RANGES)
    elif company_or_user_agent.lower() in ["bytedance", "tiktok", "bytespider"]:
        return True
    else:
        raise ValueError(f"Unknown company: {company_or_user_agent}. Supported companies are: OpenAI, Apple, Meta.")

def is_ua_from_openai(parsed_log):
    user_agent = parsed_log['user_agent']
    ip = parsed_log['ip']
    if is_ip_in_openai(ip):
        if 'ChatGPT-User'.lower() in user_agent.lower():
            return True
    return False

def get_registered_domain(domain):
    ext = tldextract.extract(domain)
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else domain
    

def generate_ip_to_group_and_domain_to_group(group_to_ips):
    ip_to_provider_domains, domain_to_provider_domains = defaultdict(set), defaultdict(set)
    # convert group_to_ips to ip_to_group
    ip_to_provider_domains = {}
    for group, ips in group_to_ips.items():
        for ip in ips:
            if ip not in ip_to_provider_domains:
                ip_to_provider_domains[ip] = group
            else:
                if ip_to_provider_domains[ip] != group:
                    raise ValueError(f"IP {ip} is associated with multiple groups: {ip_to_provider_domains[ip]} and {group}")
    # print('ip_to_provider_domains', ip_to_provider_domains)

    # convert group_to_ips to domain_to_provider_domains
    domain_to_provider_domains = {}
    for group, ips in group_to_ips.items():
        for domain in group:
            if domain not in domain_to_provider_domains:
                domain_to_provider_domains[domain] = ips
            else:
                if domain_to_provider_domains[domain] != ips:
                    raise ValueError(f"Domain {domain} is associated with multiple groups: {domain_to_provider_domains[domain]} and {ips}")
    # print('domain_to_provider_domains', domain_to_provider_domains)
    return ip_to_provider_domains, domain_to_provider_domains

"""
Input:
domain_to_ips = {
    'example.com': ['1.1.1.1', '2.2.2.2'],
    'test.com': ['2.2.2.2', '3.3.3.3'],
    'hello.com': ['4.4.4.4'],
    'world.com': ['4.4.4.4'],
    'isolated.com': ['5.5.5.5']
}
Output:
('example.com', 'test.com') -> {'1.1.1.1', '2.2.2.2', '3.3.3.3'}
('hello.com', 'world.com') -> {'4.4.4.4'}
('isolated.com',) -> {'5.5.5.5'}
"""
def domain_grouping_given_domain_to_ip_dict(domain_to_ips):
    ip_to_domain_assciated = defaultdict(set)
    # Invert the mapping: map IP to list of domains
    ip_to_domains = defaultdict(set)
    for domain, ips in domain_to_ips.items():
        for ip in ips:
            ip_to_domains[ip].add(domain)

    # Build a graph where each node is a domain, edge if they share an IP
    domain_graph = defaultdict(set)
    for domains in ip_to_domains.values():
        domain_list = list(domains)
        for i in range(len(domain_list)):
            for j in range(i + 1, len(domain_list)):
                domain_graph[domain_list[i]].add(domain_list[j])
                domain_graph[domain_list[j]].add(domain_list[i])

    # Find connected components (domains that are transitively connected)
    def dfs(domain, visited, group):
        visited.add(domain)
        group.add(domain)
        for neighbor in domain_graph[domain]:
            if neighbor not in visited:
                dfs(neighbor, visited, group)

    visited = set()
    group_to_ips = {}
    for domain in domain_to_ips:
        if domain not in visited:
            group = set()
            dfs(domain, visited, group)
            group_key = tuple(sorted(group))
            group_ips = set()
            for d in group:
                group_ips.update(domain_to_ips[d])
            group_to_ips[group_key] = group_ips

    

    return group_to_ips


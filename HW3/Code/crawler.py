from urllib.parse import urlparse, urljoin
import urllib.robotparser
from bs4 import BeautifulSoup, UnicodeDammit
import time
import urllib.robotparser
import json
import pickle
import re
import collections
import ssl
import socket
import json

common_seeds = ['http://en.wikipedia.org/wiki/Climate_change', 'https://climate.nasa.gov/']

my_seeds = [
    'https://en.wikipedia.org/wiki/Weather',
    'https://education.nationalgeographic.org/resource/weather-or-climate-whats-difference',
    'https://www.ncei.noaa.gov/news/weather-vs-climate',
    'https://www.weather.gov/climateservices/CvW',
    'https://oceanservice.noaa.gov/facts/weather_climate.html',
    'https://www.epa.gov/climate-indicators/weather-climate',
    'https://en.wikipedia.org/wiki/Climate',
    'https://www.climatecentral.org',
    'https://climate.nasa.gov/effects',
    'https://www.noaa.gov/climate',
    'https://www.noaa.gov/weather',
    'https://www.federalregister.gov/agencies/national-oceanic-and-atmospheric-administration',
    'https://www.weather.gov',
    'https://education.nationalgeographic.org/resource/global-warming',
    'https://www.britannica.com/science/global-warming',
    'http://en.wikipedia.org/wiki/Weather_and_climate'
    ]

title_map = {}
links_map = {}
requests_map = {}
data_content_map = {}
link_score_map = {}
canonicalize_url_map = {}

def canonicalize_url(url, base_url=None):
    if url in canonicalize_url_map:
        return canonicalize_url_map[url]
    url = url.lower()
    parts = url.split("://", 1)
    if len(parts) == 2:
        protocol, rest = parts
    else:
        protocol, rest = "", parts[0]

    parts = rest.split("/", 1)
    host = parts[0]
    path = "/"
    if len(parts) == 2:
        if parts[1] == "": 
            host = parts[0].split("#")[0]
        path = "/" + parts[1]

    host_parts = host.split(":")
    hostname = host_parts[0]
    if len(host_parts) == 2 and host_parts[1].isdigit():
        port = int(host_parts[1])
    else:
        port = None

    if (protocol == "http" and port == 80) or (protocol == "https" and port == 443):
        host = hostname
    else:
        if port:
            host = ":".join([hostname, str(port)])
        else: 
            host = hostname

    if base_url and not protocol:
        base_parts = base_url.split("://", 1)
        base_protocol = base_parts[0]
        base_rest = base_parts[1] if len(base_parts) == 2 else ""
        base_host = base_rest.split("/", 1)[0]
        url = urljoin(base_protocol + "://" + base_host, url)
        return canonicalize_url(url)

    path = path.split("#")[0]    
    path = "/"+"/".join([part for part in path.split("/") if part])
    canonicalized_url = protocol + "://" + host + path
    if not canonicalized_url.startswith('http') or 'javascript' in canonicalized_url or 'pdf' in canonicalized_url or 'svg' in canonicalized_url or 'jpg' in canonicalized_url or 'png' in canonicalized_url or 'gif' in canonicalized_url or 'jpeg' in canonicalized_url:
        canonicalize_url_map[url] = None    
        return None
    canonicalize_url_map[url] = canonicalized_url
    return canonicalized_url



def process_html_content(soup):
    title = soup.title.string
    links = set()
    for link in soup.find_all('a', href=True):
        canonicalized_url = canonicalize_url(link['href'])
        if canonicalized_url:
            links.add(canonicalized_url)
    content = [paragraph.get_text() for paragraph in soup.findAll('p')]
    content = ' '.join(content)
    content = content.replace('\n', ' ')
    content = content.strip()
    content = re.sub(r'[^\w\s]', '', content)
    content = re.sub(r'\s+', ' ', content)
    return title, links, content
    
def is_english(soup):
    html_tag = soup.html
    if html_tag and 'lang' in html_tag.attrs:
        return html_tag['lang'].lower().startswith('en')
    return False

def check_content_type(response):
    content_type = response.headers.get_content_type()
    if content_type:
        return 'text/html' in content_type    
    return False

    
blocked_domains = {
    'https://web.archive.org', 'https://www.nanseninitiative.org', 'https://www.addthis.com', 'http://h.bkzx.cn',
    'https://d-nb.info', 'http://www.omegawiki.org', 'https://dic.nicovideo.jp', 'https://leanlogic.online',
    'https://dic.nicovideo.jp', 'https://leanlogic.online', 'https://d-nb.info', 'http://h.bkzx.cn',
    'https://www.europarl.europa.eu', 'http://www.duraspace.org', 'http://www.dspace.org', 'http://coolice.legis.iowa.gov',
    'http://wol.jw.org', 'https://archive.today'
    }

robots_map = {}
def robots_file_allowed(url):
    try:
        parsed_url = urlparse(url)
        netloc_host = parsed_url.netloc
        domain_name = parsed_url.scheme + '://' + netloc_host
        if domain_name in blocked_domains:
            return None, False
        socket.setdefaulttimeout(5)
        robots_url = domain_name + '/robots.txt'
        if netloc_host not in robots_map:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            robots_map[netloc_host] = rp
        else: 
            rp = robots_map[netloc_host]
    except Exception as e:
        print("Exception in robots_file_allowed.", url, e)
        return None, True
    return rp.crawl_delay("*"), rp.can_fetch('*', url.encode('utf-8'))

def check_delay(url, delay=None):
    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc
    current_time = time.time()
    if not delay:
        delay = 1
    if domain_name in requests_map:
        if current_time - requests_map[domain_name] < delay:
            time.sleep(delay - (current_time - requests_map[domain_name]))
    requests_map[url] = current_time

def save_response(url, pageCounter):
    
    if url in title_map:
        return True
    try:
        with urllib.request.urlopen(url, timeout=5, context=ssl._create_unverified_context()) as response:
            if response.getcode() != 200:
                return False
            if not check_content_type(response):
                return False
            content = response.read()
            dammit = UnicodeDammit(content, ["utf-8", "iso-8859-1", "windows-1251"])
            soup = BeautifulSoup(dammit.unicode_markup, 'html.parser')
            if not is_english(soup):
                return False
            title, links, content = process_html_content(soup)
            title_map[url] = title.lower()
            try:
                save_path = '../Results/webpages-links'
                filename = f'{save_path}/page-{pageCounter}.txt'
                with open(filename, "w") as f:
                    f.write(" ".join(links))
                links_map[url] = filename
            except Exception as e:
                print("Error saving links", e)

            save_path = '../Results/webpages-text'
            filename = f'{save_path}/page-{pageCounter}.txt'
            with open(filename, "w") as f:
                f.write(content)
            data_content_map[url] = filename
            return True
    except Exception as e:
        return False
    
        
def calculate_score(url, wave_number, keywords):
    if url in link_score_map: 
        return link_score_map[url]
    score = 0
    url_set = set(url.split())
    title_set = set(title_map[url].split())
    title_text_score = 10 * len(title_set.intersection(keywords))
    url_score = 15 * len(url_set.intersection(keywords))
    score+=title_text_score
    score+=url_score
    score += (20-wave_number+1)*5
    link_score_map[url] = score
    return score


num_of_docs_in_each_file = 100
def writeContentsToFile(fileCounter, files):
    save_path = '../Results/webpages-content'
    with open(f'{save_path}/content{fileCounter}.txt', "w") as f:
       for url in files:
            title = title_map[url]
            text = ''
            readText = open(data_content_map[url], "r")
            text = readText.read()
            readText.close()
            data = f'<DOC>\n<DOCNO>{url}</DOCNO>\n<TITLE>{title}</TITLE>\n<TEXT>{text}</TEXT>\n</DOC>\n'
            f.write(data)
    print(f'Wrote to file {fileCounter*num_of_docs_in_each_file-num_of_docs_in_each_file}:{fileCounter*num_of_docs_in_each_file}')


def writeOutlinks(link_map):
    save_path = '/Users/karthik/Documents/NEU/4th Sem/IR/Assignments/hw3-karthikcd7/Results/'
    outlinks = {}
    inlinks = {}  
    for key, path in link_map.items():
        values = []
        with open(path, "r") as readText:
            values = readText.read().split()
        outlinks[key] = values
        for value in values:
            if value not in inlinks:
                inlinks[value] = []
            inlinks[value].append(key)
    
    with open(f'{save_path}/outlinks.json', "w") as f:
        json.dump(outlinks, f)
    print(f'Wrote outlink values to file outlinks.json')
    
    with open(f'{save_path}/inlinks.json', "w") as f:
        json.dump(inlinks, f)
    print(f'Wrote inlink values to file inlinks.json')

def writeSeedsToFile(seeds):
    save_path = '../Results/seeds'
    with open(f'{save_path}/seeds.txt', 'w') as f:
            f.write(" ".join(seeds) + '\n')
    print(f'Wrote seeds to file seeds.txt')


keywords={'weather', 'climate', 'temperature', 'change' 'atmosphere', 'humidity', 'cloud', 'air', 'rain', 'global_warming', 'greenhouse_effect', 'carbon_dioxide', 'methane', 'nitrous_oxide', 'ozone', 'water_vapor', 'aerosols', 'solar_radiation', 'fossil_fuels', 'deforestation', 'land_use', 'urbanization', 'climate_models', 'climate_forecasting'}
save_path = '/Users/karthik/Documents/NEU/4th Sem/IR/Assignments/hw3-karthikcd7/Results'
def crawler(seeds, frontier, links_map, title_map, data_content_map, link_score_map, requests_map, file_counter):
    
    start = time.time()
    files_to_save = set()
    save_to_file_counter = 0
    past_wave_seeds = []
    for seed in seeds:
        connonalized_link = canonicalize_url(seed)
        print(connonalized_link)
        delay, allowed = robots_file_allowed(connonalized_link)
        if not allowed:
            continue
        check_delay(connonalized_link, delay)
        if save_response(connonalized_link, file_counter):
            frontier.append(connonalized_link)
            file_counter += 1
            files_to_save.add(connonalized_link)
            save_to_file_counter += 1
            past_wave_seeds.append(connonalized_link)
        else: 
            print("Could not save response for seed", connonalized_link)
    print("initial seeds done", time.time() - start)
    total_file_limit = 41000
    while file_counter < total_file_limit: 
        try:
            while frontier and file_counter < total_file_limit:
                for wave_number in range(len(frontier)):
                    node = frontier.popleft()
                    if node not in links_map:
                        continue
                    readText = open(links_map[node], "r")
                    text = readText.read()
                    readText.close()
                    links = text.split()
                    for connonalized_link in links:
                        if connonalized_link in data_content_map:
                            continue
                        delay, allowed = robots_file_allowed(connonalized_link)
                        if not allowed:
                            continue
                        check_delay(connonalized_link, delay)
                        if save_response(connonalized_link, file_counter):
                            score = calculate_score(connonalized_link, wave_number, keywords)
                            print(connonalized_link, score, file_counter)
                            file_counter += 1
                            save_to_file_counter += 1
                            frontier.append(connonalized_link)
                            if file_counter % num_of_docs_in_each_file == 0:
                                frontier = sorted(frontier, key=lambda link: link_score_map.get(link, 0), reverse=True)
                                frontier = collections.deque(frontier)
                                print("Frontier sorted")
                            files_to_save.add(connonalized_link)
                            past_wave_seeds.append(connonalized_link)
                        if save_to_file_counter >= num_of_docs_in_each_file:
                            writeContentsToFile(file_counter//num_of_docs_in_each_file, files_to_save)
                            writeSeedsToFile(past_wave_seeds)
                            past_wave_seeds.clear()
                            files_to_save.clear()
                            file_counter += 1
                            save_to_file_counter = 0

                        if file_counter % num_of_docs_in_each_file == 0:
                            state = (frontier, links_map, title_map, data_content_map, link_score_map, requests_map)
                            with open(f'{save_path}/crawler_state.pkl', 'wb') as f:
                                pickle.dump(state, f)
                        if file_counter >= total_file_limit+4:
                            return
        except Exception as e:
            print("Exception occurred:", e)
            with open(f'{save_path}/crawler_state.pkl', 'rb') as f:
                state = pickle.load(f)
            frontier, links_map, title_map, data_content_map, link_score_map, requests_map = state
            frontier = collections.deque(frontier)

    writeOutlinks(links_map)
    print("End of Crawler", time.time() - start)

# Load saved state variables
# with open(f'{save_path}/crawler_state.pkl', 'rb') as f:
#     state = pickle.load(f)
# frontier, links_map, title_map, data_content_map, link_score_map, requests_map = state
# frontier = collections.deque(frontier)
# writeOutlinks(links_map)

# Load saved seeds
# with open(f'{save_path}/seeds/seeds.txt', 'r') as f:
#     seeds = f.read().split()

# Call the crawler function
# file_counter = 39900
# crawler([], frontier, links_map, title_map, data_content_map, link_score_map, requests_map, file_counter)

# frontier = collections.deque()
# crawler(common_seeds + my_seeds, frontier, links_map, title_map, data_content_map, link_score_map, requests_map, 0)
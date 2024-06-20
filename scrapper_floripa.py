# -*- coding: utf-8 -*-

import requests
import json
import re
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def get_sublinks(main_url, link_selector, link_regex):
    try:
        response = requests.get(main_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the main page: {main_url}. Error: {e}")
        return []
    print("Getting sublinks....")
    site = BeautifulSoup(response.content, 'html.parser')
    if(link_regex == ''):
        links = site.select(link_selector)
    else:
        search = main_url + link_regex
        links = site.find_all(link_selector, href=re.compile(fr'{search}\S+'))
    sublinks = [requests.compat.urljoin(main_url, link.get('href')) for link in links if (link.get('href'))]

    return sublinks

def try_parse_prias(data, description):
    print("parsing praias")
    texto_split = description.split(" ")
    info = ""
    dado = ""
    fim_info = False
    for palavra in texto_split:
        if(not(fim_info) and (":" in palavra)):
            if('Região' in palavra):
                info = 'Região'
            elif('Bairro' in palavra):
                dado += ' ' + palavra.replace('Bairro:', '')
                data[info] = dado
                info = 'Bairro'
            elif('próximas' in palavra):
                dado = dado.replace('Praias', '')
                dado += ' ' + palavra.replace('próximas:', '')
                data[info] = dado
                info = 'Praias próximas'
            elif('Distâncias' in palavra):
                dado += ' ' + palavra.replace('Distâncias:', '')
                data[info] = dado
                info = 'Distâncias'
            elif('Praia' in palavra):
                dado = dado.replace('Tipo de', '')
                dado += ' ' + palavra.replace('Praia:', '')
                data[info] = dado
                info = 'Tipo de Praia'
            elif('Ondulação' in palavra):
                dado += ' ' + palavra.replace('Ondulação:', '')
                data[info] = dado
                info = 'Tipo de Onda'
            elif('areia' in palavra):
                dado = dado.replace('Faixa de', '')
                dado += ' ' + palavra.replace('areia:', '')
                data[info] = dado
                info = 'Tipo de areia'
            elif('praia' in palavra):
                dado = dado.replace('Comprimento da', '')
                dado += ' ' + palavra.replace('praia:', '')
                data[info] = dado
                info = 'Comprimento da praia'
            elif('água' in palavra):
                dado = dado.replace('Temperatura da', '')
                dado += ' ' + palavra.replace('água:', '')
                data[info] = dado
                info = 'Temperatura da água'
            else:
                dado = dado.replace('Encontre', '')
                data[info] = dado
                info = 'descrição'
                fim_info = True
            dado = ''
        elif(info != ''):
            dado += ' ' + palavra
    data[info] = dado
    return data

def try_parse_trilha(data, description, image_titles):
    ignore_infos = ["Onde dormir", "Guia de Praias"]
    serch_str = r'\b(?:' + '|'.join(ignore_infos) + r')\b'
    texto_split = description.split("Informações")
    infos = texto_split[1].split('.')
    print(len(infos))
    if(len(infos) >= 9):
        for palavra in infos:
            for imagem in image_titles:
                if(imagem.text in palavra):
                    palavra = palavra.replace(imagem.text, '')
            parseado = palavra.split(':')
            if(len(parseado) == 2):
                [info, dado] = parseado
                if(not re.match(serch_str, info)):
                    print(info)
                    data[info] = dado

    data['descrição'] = texto_split[0]
    return data

def try_parse_parques(name, description, image_titles, data):
    curr_info = ''
    print(name)
    if(name == 'Funcionamento do Parque de Coqueiros'):
        print(description)
    for palavra in description.split(':'):
        if('Endereço' in palavra):
            info = 'Endereço'
            dado = palavra.replace(info, '')
        elif('Horários' in palavra):
            info = 'Horários'
            dado = palavra.replace(info, '')
        elif('Telefone' in palavra):
            info = 'Telefone'
            dado = palavra.replace(info, '')
        elif('Agendamento' in palavra):
            info = 'Agendamento'
            dado = palavra.replace(info, '')
        elif('Ingressos' in palavra):
            info = 'Ingressos'
            dado = palavra.replace(info, '')
        elif('Leia também' in palavra):
            dado = palavra.replace('+ Leia também', '')
            data[curr_info] = dado
            break
        elif('Estacionamento' in palavra):
            dado = palavra.replace('Estacionamento', '')
            data[curr_info] = dado
            break
        else:
            dado = palavra
        if(curr_info != ''):
            data[curr_info] = dado
        curr_info = info
    return data
    
def try_parse_fortes(name, name_elem, name_selector, description_selector):
    next_sibling = name_elem.find_next_sibling()
    paragraphs = []
    data = {'nome': name,
            'tipo': 'forte'}
    while next_sibling and next_sibling.name != name_selector:
        if(next_sibling.name == description_selector):
            paragraphs.append(next_sibling.text.strip())
        next_sibling = next_sibling.find_next_sibling()
    description = ''
    for paragraph in paragraphs:
        if(':' in paragraph):
            [info, dado] = paragraph.split(':')
            data[info] = dado
        else:
            description += paragraph + '\n'
    data['descrição'] = description
    return data

def try_parse_historia(data, description):
    dados = description.split('📍')
    if(len(dados) < 2):
        return {}
    for dado in dados[1].split('.'):
        if('✔' in dado):
            data['recomendado'] = dado.replace('✔', '')
        elif(dado != ''):
            data['localização'] = dado
    data['descrição'] = dados[0]
    return data


def generic_scraper(url, name_selector, description_selector, source, filter_titles=False, filter = None):
    try:
        response = requests.get(url, headers=headers, verify=(url != 'https://www.passagenspromo.com.br/blog/passeios-em-florianopolis/'))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the webpage: {url}. Error: {e}")
        return []

    tipo = "nenhum"
    if(source == "passagenspromo"):
        tipo = "local"

    elif('/praia' in url):
        tipo = "praia"
    
    elif('/trilha' in url):
        tipo = "trilha"
    elif('/parques' in url):
        tipo = "parques"
    elif('/fort' in url):
        tipo = "forte"
    elif('/pontos-turistico' in url):
        tipo = 'historia'

    site = BeautifulSoup(response.content, 'html.parser')
    name_elements = site.select(name_selector)
    image_titles = site.find_all('figcaption')
    if filter_titles:
        data = []
        for name_elem in name_elements:
            if re.match(filter, name_elem.text.strip()):
                name = name_elem.text.strip()
                paragraphs = []
                next_sibling = name_elem.find_next_sibling()
                if(tipo == "forte"):
                    data.append(try_parse_fortes(name, name_elem, name_selector, description_selector))
                    continue
                
                while next_sibling and next_sibling.name == description_selector:
                    paragraphs.append(next_sibling.text.strip())
                    next_sibling = next_sibling.find_next_sibling()
                
                description = ' '.join(paragraphs) if paragraphs else 'No description available'
                
                if(tipo == "parques"):
                    dado = {'name' : name.replace('Funcionamento do ', ''),
                            'tipo' : tipo}
                    data.append(try_parse_parques(name, description, image_titles, dado))
                elif(tipo == "historia"):
                    dado = {'name' : name,
                            'tipo' : tipo}
                    ponto_historico = try_parse_historia(dado,description)
                    if(len(ponto_historico) > 0):
                        data.append(ponto_historico)
                else:
                    print(name)
                    data.append({
                    'name': name,
                    'tipo' : tipo,
                    'description': description,
                    'source': source
                    })
        return data
    else:
        description_elements = site.select(description_selector)
        if not name_elements:
            print(f"No items found for the name selector on {url}")
            return []

        data = []
        for i, name_elem in enumerate(name_elements):
            name = name_elem.text.strip()
            description = description_elements[i].text if i < len(description_elements) else 'No description available'
            dado = {'name' : name.replace(': ', ''),
                    'tipo' : tipo}
            if(tipo == "praia"):
                data.append(try_parse_prias(dado ,description))
            elif (tipo == "trilha"):
                data.append(try_parse_trilha(dado, description, image_titles))
            else:
                data.append({
                    'name': name,
                    'tipo' : tipo,
                    'description': description,
                    'source': source
                })
        return data

sites_info = [
    {
        'url': 'https://guiafloripa.com.br/turismo/praias',
        'name_selector': 'h1',
        'description_selector': 'div.info-filmes p',
        'source': 'guiafloripa',
        'follow_links': True,
        'link_selector': 'ol li a',
        'link_regex': ''
    },
    {
        'url': 'https://guiafloripa.com.br/turismo/trilhas-florianopolis',
        'name_selector': 'h1',
        'description_selector': 'div.info-filmes p',
        'source': 'guiafloripa',
        'follow_links': True,
        'link_selector': 'a',
        'link_regex': '/trilha'
    },
    
    {
        'url': 'https://piramides.com.br/blog/florianopolis/pontos-turisticos-de-florianopolis/',
        'name_selector': 'h3',
        'description_selector': 'p',
        'source': 'piramides',
        'filter_titles': True,
        'filter': r'^\d+'
    },
    
    {
        'url': 'https://www.quintoandar.com.br/guias/parques-em-florianopolis/',
        'name_selector': 'h5',
        'description_selector': 'p',
        'source': 'quintoandar',
        'filter_titles': True,
        'filter': r'Funcionamento do\s+'
    },

    {
        'url': 'https://visitefloripa.com.br/fortalezas-de-florianopolis-conheca-historias-incriveis-no-feriado-de-7-de-setembro/#',
        'name_selector': 'h2',
        'description_selector': 'p',
        'source': 'visitefloripa',
        'filter_titles': True,
        'filter': r'\b(?:Fort\S+|Bateria\s+)\b'
    },
    
    {
        'url': 'https://www.passagenspromo.com.br/blog/passeios-em-florianopolis/',
        'name_selector': 'h2',
        'description_selector': 'p',
        'source': 'passagenspromo',
        'filter_titles': True,
        'filter': r'^\d+'
    }
]

all_data = []
for site in sites_info:
    print("Analisando: ", site['source'])
    if site.get('follow_links'):
        links = get_sublinks(site['url'], site['link_selector'], site['link_regex'])
        for link in links:
            data = generic_scraper(
                link,
                site['name_selector'],
                site['description_selector'],
                site['source']
            )
            all_data.extend(data)
    else:
        data = generic_scraper(
            site['url'],
            site['name_selector'],
            site['description_selector'],
            site['source'],
            site.get('filter_titles', False),
            site['filter']
        )
        all_data.extend(data)
print("Gerou ", len(all_data), " entradas")
with open('pontos_turisticos_florianopolis.json', 'w', encoding='utf-8') as file:
    json.dump(all_data, file, ensure_ascii=False, indent=4)
print("Created pontos_turisticos_florianopolis.json file")



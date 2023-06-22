from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

app = Flask(__name__)

@app.route('/anime-data', methods=['POST'])
def post_anime_data():
    data = request.json
    urls_listas = data.get('urlsListas', [])

    animes = obtener_animes(urls_listas)

    response = {
        'status': 200,
        'body': {
            'animes': animes
        }
    }
    return jsonify(response)

def limpiar_texto(texto):
    texto_limpio = re.sub(r'[^\w\s]', '', texto)
    return texto_limpio.strip()

def obtener_capitulos(url, capitulos_existentes=[]):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        chapters = soup.select('li.row')[:4]
        capitulos = []

        for element in chapters:
            nombre_cap = limpiar_texto(element.select_one('h4').text)
            link = urljoin(url, element.select_one('a')['href'])

            capitulo_existente = next((cap for cap in capitulos_existentes if cap['capitulo'] == nombre_cap), None)
            leido = capitulo_existente['leido'] if capitulo_existente else False

            capitulos.append({'capitulo': nombre_cap, 'url': link, 'leido': leido})

        return capitulos
    except requests.HTTPError as e:
        print(f"Error al realizar la solicitud HTTP a la URL: {url}")
        print(f"Error: {e}")
        return []

def add_new_chapters(existing_chapters, new_chapters):
    for new_chapter in new_chapters:
        if not any(chapter['url'] == new_chapter['url'] for chapter in existing_chapters):
            existing_chapters.insert(0, new_chapter)
    if len(existing_chapters) > 4:
        existing_chapters.pop()
    return existing_chapters

def obtener_animes(urls_listas):
    animes = []
    if len(urls_listas) == 1:
        # Solo hay una URL
        urls = urls_listas[0]
        for url in urls:
            try:
                new_chapters = obtener_capitulos(url)
                if new_chapters:
                    response = requests.get(url)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')
                    titulo = soup.select_one('h1')
                    imagen = soup.select_one('div.media-left.cover-detail')

                    nombre = limpiar_texto(titulo.text)
                    imagen_url = "https://www.leercapitulo.com/" + urljoin(response.url, imagen.select_one('img')['src'])
                    url = "https://www.leercapitulo.com/" + url

                    anime = {
                        'nombre': nombre,
                        'imagenUrl': imagen_url,
                        'link': new_chapters
                    }

                    animes.append(anime)

            except requests.HTTPError as e:
                print(f"Error al obtener animes de la URL: {url}")
                print(f"Error: {e}")
    else:
        # Hay múltiples URLs
        for urls in urls_listas:
            anime = {
                'nombre': '',
                'imagenUrl': '',
                'link': []
            }

            for url in urls:
                try:
                    new_chapters = obtener_capitulos(url)
                    if new_chapters:
                        response = requests.get(url)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, 'html.parser')
                        titulo = soup.select_one('h1')
                        imagen = soup.select_one('div.media-left.cover-detail')

                        nombre = limpiar_texto(titulo.text)
                        imagen_url = "https://www.leercapitulo.com/" + urljoin(response.url, imagen.select_one('img')['src'])
                        url = "https://www.leercapitulo.com/" + url

                        anime['nombre'] = nombre
                        anime['imagenUrl'] = imagen_url
                        anime['link'] = new_chapters

                except requests.HTTPError as e:
                    print(f"Error al obtener animes de la URL: {url}")
                    print(f"Error: {e}")

            animes.append(anime)

    return animes

if __name__ == "__main__":
    app.run(debug=False)

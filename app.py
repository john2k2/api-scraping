from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
import re

app = Flask(__name__)

def limpiar_texto(texto):
    return re.sub(r'[^\w\s]', '', texto).strip()

def obtener_capitulos(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        capitulos = []
        for row in soup.find_all('li', class_='row')[:4]:
            nombre_cap = limpiar_texto(row.find('h4').get_text())
            link = row.find('a').get('href')
            capitulos.append({'capitulo': nombre_cap, 'url': link, 'leido': False})
        return capitulos
    else:
        print(f'Error al realizar la solicitud HTTP a la URL: {url}')
        return []

@app.route('/api', methods=['POST'])
def post():
    data = request.get_json() or {}
    urls = data.get('urls') or []

    animes = {}
    for url in urls:
        try:
            capitulos = obtener_capitulos(url)
            if len(capitulos) > 0:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    titulo = soup.find('h1')
                    imagen = soup.find('div', class_='media-left cover-detail')

                    nombre = limpiar_texto(titulo.get_text())
                    imagen_url = imagen.find('img').get('src')

                    anime = {
                        'nombre': nombre,
                        'imagenUrl': imagen_url,
                        'link': capitulos,
                    }
                    animes[nombre] = anime
        except Exception as e:
            print(f'Error al obtener animes de la URL: {url}')
            print(f'Error: {str(e)}')

    return jsonify(list(animes.values())), 200

if __name__ == '__main__':
    app.run(debug=False)

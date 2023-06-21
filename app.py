from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from flask import Flask, request, jsonify

def limpiar_texto(texto):
    texto_limpio = ''.join(e for e in texto if e.isalnum() or e.isspace())
    return texto_limpio.strip()

def obtener_capitulos(url, capitulos_existentes=None):
    if capitulos_existentes is None:
        capitulos_existentes = []
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            chapters = soup.find_all('li', class_='row')[:4]
            capitulos = []

            for chapter in chapters:
                nombre_cap = limpiar_texto(chapter.find('h4').get_text())
                link = urljoin(url, chapter.find('a')['href'])
                
                capitulo_existente = next((cap for cap in capitulos_existentes if cap['capitulo'] == nombre_cap), None)
                leido = capitulo_existente['leido'] if capitulo_existente else False

                capitulos.append({'capitulo': nombre_cap, 'url': link, 'leido': leido})

            return capitulos
        else:
            print(f'Error al realizar la solicitud HTTP a la URL: {url}')
            return []
    except Exception as e:
        print(f'Error al realizar la solicitud HTTP a la URL: {url}')
        print(f'Error: {e}')
        return []

app = Flask(__name__)

@app.route('/')
def inicio():
    return "¡La aplicación está funcionando correctamente!"

@app.route('/capitulos', methods=['POST'])
def capitulos():
    data = request.get_json()
    url = data.get('url')
    capitulos_existentes = data.get('capitulos_existentes', [])
    if not url:
        return jsonify({'error': 'URL no proporcionada'}), 400
    try:
        capitulos = obtener_capitulos(url, capitulos_existentes)
        return jsonify({'capitulos': capitulos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=false)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import re
from flask_cors import CORS

# Ruta al archivo de cuenta de servicio de Firebase
firebase_credentials_path = './ytvideo.json'

# Inicialización de Firebase Admin
cred = credentials.Certificate(firebase_credentials_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
CORS(app)  # Habilitar CORS en la aplicación

def limpiarTexto(texto):
    textoLimpio = re.sub(r'[^\w\s]', '', texto)
    return textoLimpio.strip()

def obtenerCapitulos(url, capitulosExistentes=[]):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            chapters = soup.select('li.row')[:4]
            capitulos = []
            for chapter in chapters:
                nombreCap = limpiarTexto(chapter.find('h4').get_text())
                link = urljoin(url, chapter.find('a')['href'])

                capituloExistente = next((cap for cap in capitulosExistentes if cap['capitulo'] == nombreCap), None)
                leido = capituloExistente['leido'] if capituloExistente else False

                capitulos.append({
                    'capitulo': nombreCap,
                    'url': link,
                    'leido': leido
                })
            return capitulos
        else:
            print(f'Error al realizar la solicitud HTTP a la URL: {url}')
            return []
    except Exception as e:
        print(f'Error al realizar la solicitud HTTP a la URL: {url}')
        print(f'Error: {str(e)}')
        return []

def addNewChapters(existingChapters, newChapters):
    for newChapter in newChapters:
        existingChapterIndex = next((i for i, chapter in enumerate(existingChapters) if chapter['url'] == newChapter['url']), -1)
        if existingChapterIndex == -1:
            existingChapters.insert(0, newChapter)
    if len(existingChapters) > 4:
        existingChapters.pop()
    return existingChapters

def obtenerMangas(urls, uid, nombreLista):
    mangas = {}

    for url in urls:
        try:
            docId = f'{uid}-{limpiarTexto(url)}'
            docRef = db.collection('mangas').document(docId)
            docSnap = docRef.get()

            newChapters = obtenerCapitulos(url)
            if newChapters:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    titulo = soup.select_one('h1').get_text()
                    imagen = soup.select_one('div.media-left.cover-detail img')['src']

                    baseUrl = response.url
                    nombre = limpiarTexto(titulo)
                    imagenUrl = urljoin(baseUrl, imagen)

                    if docSnap.exists:
                        existingChapters = docSnap.get('link', [])
                        updatedChapters = addNewChapters(existingChapters, newChapters)

                        manga = {
                            'nombre': nombre,
                            'imagenUrl': docSnap.get('imagenUrl'),
                            'uid': uid,
                            'nombreLista': nombreLista,
                            'link': {}
                        }
                        for i, chapter in enumerate(updatedChapters):
                            manga['link'][str(i)] = {
                                'capitulo': chapter['capitulo'],
                                'url': chapter['url'],
                                'leido': chapter['leido']
                            }
                    else:
                        manga = {
                            'nombre': nombre,
                            'imagenUrl': imagenUrl,
                            'uid': uid,
                            'link': {}
                        }
                        for i, chapter in enumerate(newChapters):
                            manga['link'][str(i)] = {
                                'capitulo': chapter['capitulo'],
                                'url': chapter['url'],
                                'leido': chapter['leido']
                            }

                    mangas[nombre] = manga
        except Exception as e:
            print(f'Error al obtener mangas de la URL: {url}')
            print(f'Error: {str(e)}')

    return list(mangas.values())

def actualizarResultadosFirebase(mangas, uid, nombreLista):
    try:
        for manga in mangas:
            docId = f'{uid}-{manga["nombre"]}'
            docRef = db.collection('mangas').document(docId)

            docData = {
                'nombre': manga['nombre'],
                'imagenUrl': manga['imagenUrl'],
                'uid': uid,
                'listaNombre': nombreLista,  # Campo modificado
                'link': manga['link']
            }

            docRef.set(docData)

        print(f'Resultados guardados en Firebase para el usuario {uid}')
    except Exception as e:
        print(f'Error al guardar los resultados en Firebase para el usuario {uid}')
        print(f'Error: {str(e)}')


@app.route('/api/mangas', methods=['POST'])
def obtenerMangasHandler():
    try:
        data = request.get_json()
        uid = data.get('uid')
        urls = data.get('urls', [])
        nombreLista = data.get('listaNombre')

        print(f'Obteniendo mangas para el usuario {uid}')
        print(f'URLs: {urls}')

        if not uid or not urls or not nombreLista:
            return jsonify({'error': 'Falta el UID, las URLs o el nombre de la lista'}), 400

        mangas = obtenerMangas(urls, uid, nombreLista)
        actualizarResultadosFirebase(mangas, uid, nombreLista)

        return jsonify({'message': 'Mangas actualizados correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

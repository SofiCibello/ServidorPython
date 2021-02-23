import firebase_admin
from firebase_admin import credentials, firestore, messaging


def inicializarApp():
    cred = credentials.Certificate("serviceAccountKey.json")
    app = firebase_admin.initialize_app(cred)


def enviarMensaje(mensaje):
    message = messaging.Message(
        notification=messaging.Notification(
            title='Alerta!',
            body=mensaje
        ),
        topic='todos'
    )
    respuesta = messaging.send(message)
    print('Enviado: ' + respuesta)

inicializarApp()
if __name__ == '__main__':
    enviarMensaje('Hola')
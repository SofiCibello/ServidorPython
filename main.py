import datetime
import socket
import threading
import sys
import pickle

import pause

import historialDB
import time
import requests
import json
import firebase


class Servidor():
    estado = 3  # 0 = En espera ; 1 = En curso ; 2 = Finalizado ; 3 = Sin conexion
    tiempoRecorrido = 15  # en segundos, cuanto tiempo durara cada recorrido

    # Creacion de la clase servidor y se define su constructor pasándole
    # por parámetro el host y el puerto para la creación de socket
    def __init__(self, host="0.0.0.0", puerto=11000):
        self.puerto = puerto

        # Arreglo para guardar los clientes conectados
        self.clientes = []

        # Arreglo para guardar los clientes conectados que son arduinos
        self.arduinos = []

        # Creacion de la variable que almacenara el socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Aca en el servidor, al socket lo enlazamos
        self.sock.bind((str(host), int(puerto)))
        # Numero maximo de conexiones en la cola
        self.sock.listen(5)

        # Hilos para aceptar y procesar las conexiones
        aceptar = threading.Thread(target=self.aceptarConexion)
        procesar = threading.Thread(target=self.procesarConexion)

        aceptar.daemon = True
        aceptar.start()

        procesar.daemon = True
        procesar.start()

        # Creacion del while que mantendrá vivo el hilo principal
        while True:
            # mensaje = input('>>> ')
            # if mensaje == 'salir':
            #     self.sock.close()
            #     sys.exit()
            # else:
            #     pass
            pass

    # Funcion que aceptara las conexiones y las almacenara
    # en el arreglo de clientes
    def aceptarConexion(self):
        print(">>> Servidor iniciado en el puerto: " + str(self.puerto))
        print(">>> ---------------------------------------")
        while True:
            try:
                conexion, direccion = self.sock.accept()
                print('>>> Cliente conectado')
                conexion.setblocking(False)
                self.clientes.append(conexion)
            except:
                pass

    # Funcion para procesar las conexiones, esta contendrá
    # un while infinito que estará recorriendo la lista de clientes
    # para saber cuando recibe un mensaje.
    def procesarConexion(self):
        usuarios = ['Sofi,79906', 'Lara Parrucci,77749', 'Mario Groppo,1234']
        while True:
            if len(self.clientes) > 0:
                clientesRemover = []
                for cliente in self.clientes:
                    try:
                        data = cliente.recv(1024)
                        print(data.decode())
                        if data.decode() == '':
                            clientesRemover.append(cliente)
                        # El formato de los comentarios es "[TipoDispositivoEmisor (Arduino/Movil)] Descripcion"
                        # [AppMovil] Inicio de sesion
                        if data.decode() in usuarios:
                            print('-- Sesion aceptada --')
                            cliente.send('OK'.encode())
                        # [AppMovil] Solicitud de historial
                        if 'historial' in data.decode().lower():
                            print('>>> Historial enviado')
                            cliente.send(historialDB.historialTexto().encode())
                        # [AppMovil] Iniciar Arduino
                        if 'iniciar' in data.decode().lower():
                            print('>>> Arduino iniciado')
                            Servidor.estado = 1
                            for clienteArduino in self.arduinos:
                                if clienteArduino != cliente:
                                    clienteArduino.send('iniciar'.encode())

                            # Hacemos que el recorrido se finalice cuando sea necesario
                            finRecorr = threading.Thread(target=self.finalizarRecorridoAutomatico)
                            finRecorr.daemon = True
                            finRecorr.start()

                        # [AppMovil] Detener Arduino
                        if 'detener' in data.decode().lower():
                            print('>>> Arduino detenido')
                            historialDB.agregarEstado('Recorrido finalizado')
                            Servidor.estado = 2
                            for clienteArduino in self.arduinos:
                                if clienteArduino != cliente:
                                    clienteArduino.send('detener'.encode())
                        # [AppMovil] Obtencion del estado
                        if 'estado' in data.decode().lower():
                            print('>> Enviando estado al movil: ' + str(self.estado))
                            cliente.send(str(Servidor.estado).encode())
                        # [AppMovil] Configuracion de alarma
                        if '2021' in data.decode().lower():
                            print('>> Alarma establecida')
                            # Hacemos que el recorrido se finalice cuando sea necesario
                            alarma = threading.Thread(target=self.establecerAlarma, args=[data.decode()])
                            alarma.daemon = True
                            alarma.start()

                        # [Arduino] conectado
                        if 'conectado' in data.decode().lower():
                            print('Arduino conectado')
                            self.arduinos.append(cliente)
                            Servidor.estado = 0

                        # [Arduino] Humo detectado
                        if 'humo' in data.decode().lower():
                            print('Humo detectado')
                            firebase.enviarMensaje('Se ha detectado humo')
                            historialDB.agregarEstado('Humo detectado')

                        # [Arduino] Movimiento detectado
                        if 'movimiento' in data.decode().lower():
                            print('Movimiento detectado')
                            firebase.enviarMensaje('Se ha detectado movimiento')
                            historialDB.agregarEstado('Movimiento detectado')

                    except:
                        pass
                for cliente in clientesRemover:
                    print('>>> Cliente desconectado')
                    self.clientes.remove(cliente)

    # Función que nos permitirá enviar los mensajes a
    # todos los clientes conectados
    def mensaje_para_todos(self, mensaje, cliente):
        for cli in self.clientes:
            try:
                if cli != cliente:
                    cli.send(mensaje)
            except:
                self.clientes.remove(cli)

    # Detener arduinos
    def finalizarRecorridoAutomatico(self):
        time.sleep(Servidor.tiempoRecorrido)
        print('>>> Arduino detenido')
        historialDB.agregarEstado('Recorrido exitoso')
        firebase.enviarMensaje('El recorrido ha finalizado con exito')
        Servidor.estado = 2
        for arduino in self.arduinos:
            arduino.send('detener'.encode())

    def establecerAlarma(self, alarma):
        date_time_obj = datetime.datetime.strptime(alarma, '%Y-%m-%d %H:%M:%S.%f')
        pause.until(date_time_obj)
        firebase.enviarMensaje('Recorrido iniciado')
        print('>>> Arduino iniciado')
        Servidor.estado = 1
        for clienteArduino in self.arduinos:
            clienteArduino.send('iniciar'.encode())

        # Hacemos que el recorrido se finalice cuando sea necesario
        finRecorr = threading.Thread(target=self.finalizarRecorridoAutomatico)
        finRecorr.daemon = True
        finRecorr.start()






# Iniciamos el Servidor
servidor = Servidor()

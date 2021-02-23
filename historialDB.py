import datetime
import sqlite3

def historialTexto():
    # A continuación se crea un objeto conexión y un archivo llamado “historialDB.db”
    # donde se almacenará la base de datos.
    conexion = sqlite3.connect('historialDB.db')

    # A continuación se establece una conexión
    # y luego se crea un objeto cursor utilizando el objeto de conexión
    cursorObj = conexion.cursor()

    cursorObj.execute('SELECT * FROM  Historial')

    rows = cursorObj.fetchall()

    texto = ''
    for row in rows:
        for cell in row:
            texto += cell + '%'
        texto = texto[:-1] + '&'

    return texto

def agregarEstado(descripcion):
    conexion = sqlite3.connect('historialDB.db')
    cursorObj = conexion.cursor()
    fecha = str(datetime.datetime.now().date().strftime("%d/%m/%y"))
    hora = str(datetime.datetime.now().time().strftime("%H:%M"))
    cursorObj.execute('INSERT INTO Historial (Fecha, Hora, Descripcion) VALUES ("' + fecha + '", "' + hora + '", "' + descripcion + '")')
    conexion.commit()
    conexion.close()

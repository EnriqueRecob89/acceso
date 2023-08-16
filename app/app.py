import os
import pdfkit
import mysql.connector
import serial
import time
import sqlite3
# Espera un momento para que Arduino se inicialice
time.sleep(2)

from PIL import Image
from PIL import ImageTk
from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, Blueprint, make_response
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_paginate import Pagination, get_page_parameter
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from Models.ModelUser import ModuleUser
from Models.entities.user import User
#importamos Blueprint para crear una etiqueta

#Creamos una tag con la ayuda de Blueprint y la iniciamos en nuestro proyecti (al crear nuestra applicación)
custom_tags = Blueprint('custom_tags', __name__)

app = Flask(__name__)
csrf=CSRFProtect()

# Conexión MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'recoba'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'tiard'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ruta=app.config['UPLOAD_FOLDER']='./app/static/img/uploads/profesores'

db = MySQL(app)

Login_manager_app=LoginManager(app)

@Login_manager_app.user_loader
def load_user(idusuarios):
    return ModuleUser.get_by_id(db,idusuarios)
@login_required
@app.route('/logout')
def logout():
    logout_user()
    return render_template('login.html')


app.secret_key='mysecretkey'

#Usamos el nuevo tag que creamos y le asignamos una función
@custom_tags.app_template_global()
def listar_materias():
    cur=db.connection.cursor()
    sql="SELECT * FROM materias order by nombre asc"
    cur.execute(sql)
    materias=cur.fetchall()
    cur.close()
    return materias

@login_required
def listar_profesores():
    cur=db.connection.cursor()
    sql="SELECT * FROM profesores order by nombre asc"
    cur.execute(sql)
    profesores=cur.fetchall()
    cur.close()
    return profesores

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Ruta al Inicio
@app.route('/')
def index():
    index = listar_materias()
    data = {
        'titulo': 'Inicio',
        'bienvenida': 'Bienvenido ',
        'materias': materias,
        'numero_materias': len(materias)
    }
    print(materias)
    
    return render_template('index.html', data=data)
#_---------------------------------------ARDUINO------------------------------------------------------------------#

@app.route('/rfid', methods=['POST'])
def recibir_rfid():
    NumTar = request.data.decode('utf-8')
    # Procesa el número de tarjeta y consulta la base de datos
    # Devuelve el nombre como respuesta
    

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="JOSERo180303**",
    database="tiard"
)
def obtener_nombre_por_tarjeta(NumTar):
    cursor = db.cursor()
    cursor.execute("SELECT nombre FROM alumnos WHERE rfid_id = %s", (NumTar,))
    resultado = cursor.fetchone()
    cursor.close()
    
    if resultado:
        return resultado[0]
    else:
        return "Tarjeta no registrada"










# ---------------------------------------------- Apartado CRUD de Alumnos ---------------------------------------------
#Read (Leer)

PER_PAGE = 25
def alumnos_Paginar(page):
    cur=db.connection.cursor()

    # Ejemplo de consulta paginada (ajusta esto según la estructura de tu tabla)
    offset = (page - 1) * PER_PAGE
    sql = "SELECT * FROM alumnos LIMIT %s OFFSET %s"
    cur.execute(sql, (PER_PAGE, offset))

    # Obtenemos los resultados y los almacenamos en una lista
    resultados_pagina_actual = cur.fetchall()

    # Consulta para obtener el total de resultados (sin paginación)
    sql_total = "SELECT COUNT(*) FROM alumnos"
    cur.execute(sql_total)
    total_results = cur.fetchone()[0]

    cur.close()

    return resultados_pagina_actual, total_results

@app.route('/alumnos')
@login_required
def alumnos_Ver():
    # Obtener la página actual del paginador
    page = request.args.get(get_page_parameter(), type=int, default=1)

    # Obtener los resultados de la página actual y el total de resultados
    resultados_pagina_actual, total_results = alumnos_Paginar(page)

    # Generar el objeto de paginación
    pagination = Pagination(page=page, per_page=PER_PAGE, total=total_results, outer_window=20, inner_window=20)

    return render_template('alumnos.html', pagination=pagination, alumnos=resultados_pagina_actual)


"""@app.route('/alumnos')
@login_required
def alumnos_Ver():
    cur=db.connection.cursor()
    sql="SELECT * FROM alumnos order by matricula asc"
    cur.execute(sql)
    alumnos=cur.fetchall()
    print(alumnos) 
    cur.close()

    return render_template('alumnos.html', alumnos=alumnos)
"""

@app.route('/alumno/<string:id>')
@login_required
def ver_alumno(id):
    print(id)
    cur=db.connection.cursor()
    sql="SELECT * FROM alumnos WHERE idalumnos={0}".format(id)
    cur.execute(sql)
    alumno=cur.fetchall()
    print(alumno[0])
    cur.close()
    
    return render_template('alumnoVer.html', alumno=alumno[0])


@app.route('/alumnos', methods=['GET'])
def buscar():
    buscar = request.args.get('buscar')
    cur = mysql.connection.cursor()
    
    if buscar:
        sql = "SELECT * FROM alumnos WHERE nombre LIKE %s OR matricula LIKE %s"
        valores = (f"%{buscar}%", f"%{buscar}%")
        cur.execute(sql, valores)
        alumnos = cur.fetchall()
    else: 
        cur.execute("SELECT * FROM alumnos")
        alumnos = cur.fetchall()
        
    cur.close()
    
    #paginador actual
    page = request.args.get(get_page_parameter(), type=int, default=1)
    
    def libros_paginar (page, per_page=PER_PAGE):
        start_alumnos = (page - 1)* per_page
        end_alumnos = start_alumnos + per_page
        return alumnos[start_alumnos:end_alumnos], len(alumnos)
    
    resultados_pagina_actual, total_results = alumnos_Paginar (page)
    
    pagination=pagination(
        page=page,
        PER_PAGE=PER_PAGE,
        total=total_results,
        outer_window=2,
        inner_window=2,
    ) 
    return render_template(
        "alumnos.html", pagination=pagination, alumnos=resultados_pagina_actual
    )
    

def buscar_alumnos(query):
    conn = sqlite3.connect('tiard.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alumnos WHERE nombre LIKE ? OR matricula LIKE ?", ('%' + query + '%', '%' + query + '%'))
    resultados = cursor.fetchall()
    conn.close()
    return resultados

#Create (Crear)
@app.route('/alumno/nuevo')
@login_required
def alumno_Crear():
    return render_template('alumnoCrear.html',)

@app.route('/alumno/agregar', methods=['POST'])

def alumno_Agregar():
    if request.method == 'POST':
        Nombre=request.form['Nombre']
        Apellido=request.form['Apellido']
        Matricula=request.form['Matricula']
        Carrera=request.form['Carrera']
        NumTar=request.form['NumTar']
        
        Creado=datetime.now()
        Activo=1
        

            
        cur=db.connection.cursor()
        sql="INSERT INTO alumnos (nombre, apellido, matricula, carrera, numtar) VALUES (%s, %s, %s, %s, %s)"
        valores=(Nombre, Apellido, Matricula, Carrera, NumTar.upper())
        cur.execute(sql,valores)
        db.connection.commit()
        cur.close()

        #flash('¡Alumno "{}" agregado exitosamente!'.format(Nombre))
        flash('¡Alumno agregado exitosamente!')

        return redirect(url_for('alumno_Crear'))

#Update (Actualizar)
@app.route('/alumno/editar/<string:id>')
@login_required
def editar_alumno(id):
    print(id)
    cur=db.connection.cursor()
    sql="SELECT * FROM alumnos WHERE idalumnos={0}".format(id)
    cur.execute(sql)
    alumno=cur.fetchall()
    print(alumno[0])
    cur.close()
    return render_template('alumnoEditar.html', alumno=alumno[0])

@app.route('/alumno/actualizar/<string:id>', methods=['POST'])
@login_required
def alumno_actualizar(id):
    if request.method == 'POST':
        Nombre=request.form['Nombre']
        Apellido=request.form['Apellido']
        Matricula=request.form['Matricula']
        Carrera=request.form['Carrera']
        NumTar=request.form['NumTar']

        cur=db.connection.cursor()
        sql="UPDATE alumnos SET nombre=%s, apellido=%s, matricula=%s, carrera=%s, numtar=%s WHERE idalumnos=%s"        
        valores=(Nombre, Apellido, Matricula, Carrera, NumTar.upper(), id)
        cur.execute(sql,valores)
        db.connection.commit()
        cur.close()

        flash('¡Alumno modificado exitosamente!')
    return redirect(url_for('alumnos_Ver'))

#Delete (Borrar)
@app.route('/alumno/eliminar/<string:id>')
@login_required
def eliminar_alumno(id):
    print(id)
    cur=db.connection.cursor()
    sql="DELETE FROM alumnos WHERE idalumnos={0}".format(id)
    cur.execute(sql)
    db.connection.commit()
    cur.close()
    flash('¡Alumno  eliminado correctamente!')
    return redirect(url_for('alumnos_Ver'))


# ---------------------------------------------- Apartado CRUD de Profesores ----------------------------------------------
#Read (Leer)
@app.route('/profesores')
@login_required
def profesores_Ver():
    cur=db.connection.cursor()
    sql="SELECT * FROM profesores ORDER BY idprofesores desc"
    cur.execute(sql)
    profesores=cur.fetchall()
    print(profesores) 
    cur.close()
    return render_template('profesores.html', profesores=profesores)

@app.route('/profesor/<string:id>')
@login_required
def ver_profesor(id):
    print(id)
    cur=db.connection.cursor()
    sql="SELECT * FROM profesores WHERE idprofesores={0}".format(id)
    cur.execute(sql)
    profesor=cur.fetchall()
    print(profesor[0])
    cur.close()
    return render_template('profesorVer.html', profesor=profesor[0])

#Create (Crear)
@app.route('/profesor/nuevo')
@login_required
def profesor_Crear():
    return render_template('profesorCrear.html',)

@app.route('/profesor/agregar', methods=['POST'])
@login_required
def profesor_Agregar():
    if request.method == 'POST':
        Nombre=request.form['Nombre']
        Apellido=request.form['Apellido']
        Puesto=request.form['Puesto']
        Area=request.form['Area']
        NumTar=request.form['NumTar']
       
        Creado=datetime.now()
        Activo=1
        cur=db.connection.cursor()
        sql="INSERT INTO profesores (nombre, apellido, puesto, area, numtar) VALUES ( %s, %s, %s, %s, %s)"
        valores=(Nombre, Apellido, Puesto, Area, NumTar.upper())
        cur.execute(sql,valores)
        db.connection.commit()
        cur.close()

        flash('¡Profesor agregado exitosamente!')

        return redirect(url_for('profesores_Ver'))

#Update (Actualizar)
@app.route('/profesor/editar/<string:id>')
@login_required
def editar_profesor(id):
    print(id)
    cur=db.connection.cursor()
    sql="SELECT * FROM profesores WHERE idprofesores={0}".format(id)
    cur.execute(sql)
    profesor=cur.fetchall()
    print(profesor[0])
    cur.close()
    return render_template('profesorEditar.html', profesor=profesor[0])

@app.route('/profesor/actualizar/<string:id>', methods=['POST'])
@login_required
def profesor_actualizar(id):
    if request.method == 'POST':
        Nombre=request.form['Nombre']
        Apellido=request.form['Apellido']
        Puesto=request.form['Puesto']
        Area=request.form['Area']
        NumTar=request.form['NumTar']

        cur=db.connection.cursor()
        sql="UPDATE profesores SET nombre=%s, apellido=%s, puesto=%s, area=%s, numtar=%s WHERE idprofesores=%s"        
        valores=(Nombre, Apellido, Puesto, Area, NumTar.upper(), id)
        cur.execute(sql,valores)
        db.connection.commit()
        cur.close()
        flash('¡Profesores modificado exitosamente!')
    return redirect(url_for('profesores_Ver'))

#Delete (Borrar)
@app.route('/profesor/eliminar/<string:id>')
@login_required
def eliminar_profesor(id):
    print(id)
    cur=db.connection.cursor()
    sql="DELETE FROM profesores WHERE idprofesores={0}".format(id)
    cur.execute(sql)
    db.connection.commit()
    cur.close()
    flash('¡Profesores eliminado correctamente!')
    return redirect(url_for('profesores_Ver'))

# ---------------------------------------------- Apartado CRUD de Materias ----------------------------------------------

# ---------------------------------------------- Apartado CRUD de Usuarios ----------------------------------------------
#Read (Leer)
@app.route('/usuarios')
@login_required
def usuarios_Ver():
    cur=db.connection.cursor()
    sql="SELECT * FROM usuarios ORDER BY idusuarios desc"
    cur.execute(sql)
    usuarios=cur.fetchall()
    print(usuarios) 
    cur.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuario/<string:id>')
@login_required
def ver_usuario(id):
    print(id)
    cur=db.connection.cursor()
    sql="SELECT * FROM usuarios WHERE idusuarios={0}".format(id)
    cur.execute(sql)
    usuario=cur.fetchall()
    print(usuario[0])
    cur.close()
    return render_template('usuarioVer.html', usuario=usuario[0])

#Create (Crear)
@app.route('/usuario/nuevo')
@login_required
def usuario_Crear():
    return render_template('usuarioCrear.html',)

@app.route('/usuario/agregar', methods=['POST'])
@login_required
def usuario_Agregar():
    if request.method == 'POST':
        Username=request.form['Username']
        Password=request.form['Password']
        Pass=generate_password_hash(Password)
        TipoUsuario=request.form['TipoUsuario']
        Creado=datetime.now()
        Activo=1

        cur=db.connection.cursor()
        sql="INSERT INTO usuarios (username, password, tipo, creado, activo) VALUES (%s, %s, %s, %s, %s)"
        valores=(Username, Pass, TipoUsuario, Creado, Activo)
        cur.execute(sql,valores)
        db.connection.commit()
        cur.close()

        flash('¡Usuario agregado exitosamente!')

        return redirect(url_for('usuarios_Ver'))

#Update (Actualizar)
@app.route('/usuario/editar/<string:id>')
@login_required
def editar_usuario(id):
    print(id)
    cur=db.connection.cursor()
    sql="SELECT * FROM usuarios WHERE idusuarios={0}".format(id)
    cur.execute(sql)
    usuario=cur.fetchall()
    print(usuario[0])
    cur.close()
    return render_template('usuarioEditar.html', usuario=usuario[0])

@app.route('/usuario/actualizar/<string:id>', methods=['POST'])
@login_required
def usuario_actualizar(id):
    if request.method == 'POST':
        Username=request.form['Username']
        Password=request.form['Password']
        Pass=generate_password_hash(Password)
        TipoUsuario=request.form['TipoUsuario']
        Activo=1

        cur=db.connection.cursor()
        sql="UPDATE usuarios SET username=%s, password=%s, tipo=%s, activo=%s WHERE idusuarios=%s"        
        valores=(Username, Pass, TipoUsuario, Activo, id)
        cur.execute(sql,valores)
        db.connection.commit()
        cur.close()

        flash('¡Usuario modificado exitosamente!')
    return redirect(url_for('usuarios_Ver'))

#Delete (Borrar)
@app.route('/usuario/eliminar/<string:id>')
@login_required
def eliminar_usuario(id):
    print(id)
    cur=db.connection.cursor()
    sql="DELETE FROM usuarios WHERE idusuarios={0}".format(id)
    cur.execute(sql)
    db.connection.commit()
    cur.close()
    flash('¡Usuario eliminado correctamente!')
    return redirect(url_for('usuarios_Ver'))

### Apartado SingUp

@app.route('/signup')
def signup():
    return render_template('signup.html')

### Apartado Login

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/loguear', methods=['POST'])
def loguear():
    if request.method == 'POST':
        Username=request.form['Username']
        Password=request.form['Password']
        user=User(0,Username,Password,None)
        loged_user=ModuleUser.login(db,user)

        if loged_user!= None:
            if loged_user.password:
                login_user(loged_user)
                return redirect(url_for('usuarios_Ver'))
            else:
                flash('Nombre de usuario y/o Contraseña incorrecta.')
                return render_template('login.html')
        else:
            flash('Nombre de usuario y/o Contraseña incorrecta.')
            return render_template('login.html')
    else:
            flash('Nombre de usuario y/o Contraseña incorrecta.')
            return render_template('login.html')


def pagina_no_encontrada(error):
    #return render_template('404.html'), 404
    return redirect(url_for('index'))
def acceso_no_autorizado(error):
    return redirect(url_for('login'))

if __name__ == '__main__':
    csrf.init_app(app)
    app.register_blueprint(custom_tags)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(debug=True, port=5000)
    
    

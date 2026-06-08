import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt

app = Flask(__name__)
app.secret_key = "1234"

MONGO_URI = "mongodb://localhost:27017/"
NOMBRE_BASE_DATOS = "consultorio"

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database(NOMBRE_BASE_DATOS)
    usuarios_col = db["usuarios"]
    pacientes_col = db["pacientes"]
    print("✅ Conectado a MongoDB correctamente")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")


@app.route('/')
def index():
    if 'doctor_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip()
        password = request.form.get('password', '')
        if not nombre or not correo or not password:
            flash("Todos los campos son obligatorios", "danger")
            return redirect(url_for('register'))
        if usuarios_col.find_one({"correo": correo}):
            flash("El correo ya está registrado.", "danger")
            return redirect(url_for('register'))
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        usuarios_col.insert_one({
            "nombre": nombre,
            "correo": correo,
            "password": hashed_pw
        })
        flash("Cuenta creada con éxito. Ya puedes iniciar sesión.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        password = request.form.get('password', '')
        user = usuarios_col.find_one({"correo": correo})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['doctor_id'] = str(user['_id'])
            session['doctor_name'] = user['nombre']
            flash(f"Bienvenido {user['nombre']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Credenciales incorrectas.", "danger")
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        user = usuarios_col.find_one({"correo": correo})
        if user:
            flash("Se ha enviado un enlace de recuperación a tu correo (Simulado).", "info")
        else:
            flash("El correo no está registrado.", "danger")
        return redirect(url_for('login'))
    return render_template('login.html', forgot_mode=True)

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', doctor_name=session['doctor_name'])

@app.route('/pacientes', methods=['GET', 'POST'])
def pacientes():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        edad_str = request.form.get('edad', '')
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        if not nombre:
            flash("El nombre del paciente es obligatorio", "danger")
            return redirect(url_for('pacientes'))
        try:
            edad = int(edad_str) if edad_str else 0
            if edad < 0 or edad > 150:
                raise ValueError
        except ValueError:
            flash("La edad debe ser un número válido entre 0 y 150", "danger")
            return redirect(url_for('pacientes'))
        nuevo_paciente = {
            "doctor_id": session['doctor_id'],
            "nombre": nombre,
            "edad": edad,
            "correo": correo,
            "telefono": telefono,
            "fecha_registro": str(__import__('datetime').datetime.now())
        }
        try:
            pacientes_col.insert_one(nuevo_paciente)
            flash(f"Paciente {nombre} agregado correctamente.", "success")
        except Exception as e:
            flash(f"Error al agregar paciente: {str(e)}", "danger")
            
        return redirect(url_for('pacientes'))
    mis_pacientes = list(pacientes_col.find({"doctor_id": session['doctor_id']}))
    total_pacientes = len(mis_pacientes)
    return render_template('pacientes.html', pacientes=mis_pacientes, total=total_pacientes)

if __name__ == '__main__':
    print("zapato blanco")
    app.run(debug=True)
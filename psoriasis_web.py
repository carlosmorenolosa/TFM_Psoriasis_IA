from flask import (
    Flask,
    request,
    render_template_string,
    send_from_directory,
    jsonify,
)
import fitz
import re
import openai
import pinecone
from pinecone.core.client.configuration import Configuration as OpenApiConfiguration
import markdown
from flask import make_response
from flask import session
from io import BytesIO
from weasyprint import HTML
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask import jsonify
from flask_cors import CORS
from flask_session import Session
import base64
from PIL import Image
import os
from werkzeug.utils import secure_filename
from langchain.text_splitter import RecursiveCharacterTextSplitter


app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = "papas-popas789M1"

# Configuración de la sesión basada en el sistema de archivos
app.config["SESSION_TYPE"] = "filesystem"
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)

"""# Configura el uso de Redis para las sesiones
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')"""

"""Inicializa la extensión Flask-Session
Session(app)"""

# Configura tus claves API aquí
openai.api_key = os.getenv("OPENAI_API_KEY")

openapi_config = OpenApiConfiguration.get_default_copy()
openapi_config.proxy = "http://proxy.server:3128"

pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment="gcp-starter",
    openapi_config=openapi_config,
)
index = pinecone.Index("embedding-psoriasis-large")

data_store = {}


HTML_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>APM Dermatología | Consulta de Dermatología con IA</title>
  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css" rel="stylesheet">
  <!-- Google Fonts: Open Sans -->
  <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
  <link rel="icon" type="image/png" href="{{ url_for('static', filename='d_psoriaris.png') }}">
  <style>


    /* Cargar Helvetica Neue Light (300) */
    @font-face {
      font-family: 'Helvetica Neue';
      src: url('fonts/ HelveticaNeueCyr-Light.woff2') format('woff2'),
           url('fonts/ HelveticaNeueCyr-Light.woff') format('woff');
      font-weight: 300;
      font-style: normal;
    }

    /* Cargar Helvetica Neue Bold (700) */
    @font-face {
      font-family: 'Helvetica Neue';
      src: url('fonts/HelveticaNeueCyr-Bold.woff2') format('woff2'),
           url('fonts/HelveticaNeueCyr-Bold.woff') format('woff');
      font-weight: 700;
      font-style: normal;
    }

    body {
      font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
      background: linear-gradient(180deg, #B9BAFD, #FCEEFB);/*background-color: #f9f9f9;*/
      color: #333;
    }
    .container {
      padding-top: 3rem;
      padding-bottom: 3rem;
    }
    .header-container {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 10px;
      margin: 0 auto; /* Centrar el contenedor */
      padding: 0 20px; /* Añadir algo de espacio en los lados */
      max-width: 1000px; /* Limitar el ancho máximo del contenedor */
      position: relative; /* Cambiar a relative en lugar de absolute */
      top: 20px; /* Ajustar la distancia desde la parte superior */
      width: 100%; /* Mantener el ancho completo del contenedor */

    }

    .header-container img {
      max-height: 50px;
      object-fit: contain;
    }

    /* Añadir un nuevo contenedor para el logo grande */
    .logo-grande {
      text-align: center;
      margin-top: 20px; /* Espacio entre los logos pequeños y el logo grande */
      margin-bottom: 40px; /* Añadir más espacio entre el logo grande y el texto */

    }

    .logo-grande img {
      max-height: 70px; /* Tamaño del logo grande */
      object-fit: contain;
    }

    h3.nuestros-colaboradores {
       margin-top: 40px; /* Aumenta este valor según el espacio que quieras */
       margin-bottom: 20px; /* Añade este espacio inferior */

    }

    /* Estilo para los enlaces que contienen los logos */
    .enlaces-recomendados.nuestros-colaboradores-logos a {
        margin: 0 50px;
        margin-bottom: 40px;/* Espacio horizontal entre los logos (puedes ajustar el valor) */
    }

    .nuestros-colaboradores-logos img {
        max-width: none !important;
        max-height: none !important;
        width: 70px !important; /* Ajusta este tamaño según tus preferencias */
        height: auto !important; /* Mantiene la proporción del logo */
        margin: 0 30px; /* Ajusta el espacio entre logos */
    }



    h2, h3 {
      text-align: center;
      margin-bottom: 1.5rem;
      color:#2B2A90;
      font-weight:300;

    }

    h2 span {
        font-weight:700;
        color: #2B2A90;

    }

    .btn {
        border-radius: 10px;
        background-color: #2B2A90; /* Color azul oscuro */
        color: #FFFFFF;
        border: 1px solid #2B2A90;
    }
    .btn:hover {
        background-color: #2B2A90; /* Color más oscuro al pasar el cursor */
    }

    #upload-generating-message {
      color: #2B2A90; /* Cambia este color por el que desees */
    }




    .form-section {
      background-color: rgba(255, 255, 255, 0.2); /* Fondo blanco semitransparente */
      padding: 2rem;
      border-radius: 20px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* Sombra más suave */
      margin-bottom: 2rem;
    }

    .form-control, .form-select {
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.3); /* Color lila más oscuro para el fondo */
        border: 1px solid rgba(255, 255, 255, 0.3); /* Mismo color lila para el borde */
        color: #2B2A90; /* Color del texto */

    }

    .form-control:focus, .form-select:focus {
        background-color: rgba(255, 255, 255, 0.3); /* Mantiene el lila suave al hacer clic */
        border-color: rgba(255, 255, 255, 0.3); /* Mantiene el borde lila suave */
        outline: none; /* Elimina el borde de enfoque predeterminado */
        box-shadow: none; /* Elimina cualquier sombra que algunos navegadores aplican */
    }

    .alert-success {
        background-color: rgba(255, 255, 255, 0.4); /* Lila suave en lugar de verde */
        border-color: #d6b3e6 !important; /* Bordes de un tono similar */
        color: #2B2A90 !important; /* Color del texto oscuro para que sea legible */
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* Sombra más suave */
    }


    .form-label {
      color: #2B2A90; /* Cambia este color por el que desees */
    }

    textarea {
      color: #2B2A90; /* Cambia este color por el que desees */
    }

    textarea::placeholder {
      color: #2B2A90; /* Cambia este color por el que desees */
    }

    #advancedInstructions::placeholder {
      color: #2B2A90; /* Cambia este color */
      font-style: italic; /* Esto es opcional, puedes agregar otros estilos */

    }

    #advancedInstructions {
      color: #2B2A90; /* Cambia este color */
    }

    /* Cambiar el color del placeholder */
    #voiceTextOutput::placeholder {
        color: #2B2A90; /* Cambia este color por el que desees */
        font-style: italic; /* Esto es opcional, puedes agregar otros estilos */
    }

    #voiceTextOutput {
        color: #2B2A90; /* Cambia este color por el que desees */
    }






    .enlaces-recomendados a {
      text-align: center;
      color: #333;
      margin: 1rem;
      text-decoration: none;
      transition: transform 0.3s;
    }
    .enlaces-recomendados a:hover {
      transform: translateY(-5px);
    }
    .enlaces-recomendados img {
      width: 60px;
      height: 60px;
      object-fit: contain;
      margin-bottom: 1.5rem;
    }
    .banner-img {
      width: 100%;
      max-width: 600px;
      height: auto;
      display: block;
      margin: 2rem auto;
      border-radius: 8px;
    }
    .copyright {
      text-align: center;
      padding: 1rem 0;
      background-color: transparent !important;
      width: 100%;
      border-top: 1px solid #eaeaea;
    }

    #como-funciona-text {
      text-align: justify !important;
      color: #2B2A90;
    }

    @media (max-width: 768px) {
      .header-container {
        margin-top: 0;
        padding-top: 0;
        flex-direction: row;
        justify-content: space-between;
      }

      .header-container img {
         max-height: 40px;
         object-fit: contain;
      }

      .logo-grande img{
        max-height: 50px;
      }

      .enlaces-recomendados {
        flex-direction: column;
        align-items: center;
        margin-bottom: 50px;
      }

      .enlaces-recomendados a {
        width: 80%;
      }

      .nuestros-colaboradores-logos img {
        max-width: none !important;
        max-height: none !important;
        width: 70px !important; /* Ajusta este tamaño según tus preferencias */
        height: auto !important; /* Mantiene la proporción del logo */
        margin: 0 30px 50px !important; /* Ajusta el espacio entre logos */
      }

      /* Ajuste de tamaño para todos los botones */
      .btn-primary, .btn-secondary {
        font-size: 0.75rem !important;
        padding: 0.375rem 0.75rem !important;
      }

      /* Ajuste específico para los botones dentro de los formularios */
      form#uploadForm .btn,
      form#dataForm .btn {
        font-size: 0.75rem !important;
        padding: 0.375rem 0.75rem !important;
      }

        /* Selector más específico para los botones "Anterior" */
      form#dataForm .btn-anterior {
        font-size: 0.75rem !important;
        padding: 0.375rem 0.75rem !important;
        margin-right: 0.5rem !important;
      }

      /* Separar más los botones dentro de .d-flex */
      .d-flex .btn {
        margin-bottom: 0.5rem !important;
      }
    }

  </style>
</head>
<body>
  <div class="container">
    <!-- Header Logos -->
    <div class="logo-grande">
        <img src="static/d_psoriaris.png" alt="Nuevo Logo Grande">
    </div>


    <!-- Main Title -->
    <h2>Consulta de Tratamiento para <span>Dermatología</span> mediante IA</h2>


    <!-- Forms Section -->
    <div class="form-section">

      <!-- Selección de Patología -->
      <div class="mb-3">
            <label for="pathologySelect" class="form-label">Seleccione una patología:</label>
            <select class="form-select" id="pathologySelect" name="pathology">
                <option value="psoriasis" selected>Psoriasis</option>
                <option value="dermatitis_atopica">Dermatitis Atópica</option>
                <option value="hidradenitis_supurativa">Hidradenitis Supurativa</option>
                <option value="acne">Acne</option>
            </select>
      </div>
      <!-- Selección de Documento -->
      <div class="mb-3">
          <label for="documentSelect" class="form-label">
            Seleccione el documento para alimentar el modelo de IA:
            <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Nuestro modelo utiliza por defecto un protocolo de Dermatología para determinar el mejor tratamiento. No obstante, puedes subir el documento que desees para que el modelo aprenda de él y determine el tratamiento siguiendo sus criterios."></i>
          </label>
          <select class="form-select" id="documentSelect">
            <option value="default" selected>Por defecto</option>
            <option value="upload_document">Seleccione un documento</option>
          </select>
      </div>
      <div class="mb-3">
            <label for="advancedInstructions" class="form-label">
                Instrucciones avanzadas para el modelo:
                <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Puede ingresar instrucciones específicas o consideraciones avanzadas para personalizar la consulta y que el modelo aprenda a diagnosticar como usted."></i>
            </label>
            <textarea class="form-control" id="advancedInstructions" name="advanced_instructions" rows="4" placeholder="Escriba aquí las instrucciones avanzadas..."></textarea>
      </div>



      <!-- Input de Documento Personalizado -->
      <div id="documentInputContainer" class="mb-3" style="display: none;">
        <label for="customDocumentFile" class="form-label">Elija el documento (PDF):</label>
        <input type="file" name="custom_document" class="form-control" id="customDocumentFile" accept=".pdf">
      </div>

      <!-- Selección de Modo de Trabajo -->
      <div class="mb-3">
        <label for="modeSelect" class="form-label">Seleccione Modo de Trabajo:</label>
        <select class="form-select" id="modeSelect">
          <option value="upload" selected>Cargar Informe Médico del Paciente</option>
          <option value="form">Completar Datos del Paciente en la Web</option>
          <option value="upload_scanned">Cargar Informe Médico del Paciente Escaneado (PDF)</option> <!-- Nueva opción -->
          <option value="take_photo">Tomar Foto del Informe Médico del Paciente</option> <!-- Nueva opción -->
          <option value="input_voice">Entrada por Voz</option> <!-- Nueva opción -->
        </select>
      </div>

      <!-- Formulario de Carga de Archivo -->
      <form id="uploadForm" enctype="multipart/form-data" class="mb-3" style="display: block;">
        <!-- Campo oculto para el user_id -->
        <input type="hidden" name="user_id" value="{{ user_id }}">

        <div class="mb-4">
          <label for="customFile" class="form-label">
            Elegir archivo
            <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Debe cargar un archivo de texto con los datos del paciente en formato PDF o DOCX. Puede incluir consideraciones o consejos para que el algoritmo las tenga en cuenta."></i>
          </label>
          <input type="file" name="patient_file" class="form-control" id="customFile">
        </div>
        <div class="mb-3">
          <label for="imageSelect" class="form-label">
            ¿Desea cargar una imagen de la patología del paciente?
            <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Puede cargar una imagen existente o tomar una foto con su dispositivo. El modelo la analizará y la tendrá en cuenta a la hora de determinar el tratamiento."></i>
          </label>
          <select class="form-select" id="imageSelect">
            <option value="no_image" selected>Sin Imagen</option>
            <option value="upload_image">Elegir imagen</option>
            <option value="take_image">Tomar imagen con el dispositivo</option>
          </select>
        </div>
        <div id="imageInputContainer" class="mb-3"></div>
        <div class="mb-3">
          <label for="language" class="form-label">Seleccione el idioma de la respuesta:</label>
          <select class="form-select" id="language" name="language">
            <option value="ES">Español</option>
            <option value="EN">Inglés</option>
            <option value="FR">Francés</option>
          </select>
        </div>
        <div class="d-flex justify-content-between">
          <button type="submit" class="btn btn-primary">Generar Respuesta</button>
          <a href="https://iaenpsoriasis.pythonanywhere.com/download-form" class="btn btn-secondary" download>Descargar Formulario Tipo</a>
        </div>
        <p id="upload-generating-message" class="mt-3 text-center fw-bold" style="display: none;">Su respuesta se está generando. Por favor, espere...</p>
      </form>
      <!-- Formulario para cargar un archivo escaneado (PDF) -->
      <div id="scannedFormContainer" style="display:none;" class="mb-4">
        <label for="scannedFile" class="form-label">Seleccione el informe médico escaneado (PDF)</label>
        <input type="file" name="scanned_file" class="form-control" id="scannedFile" accept=".pdf" required>

        <!-- Añadimos las opciones de imagen y idioma -->
        <div class="mb-3 mt-4">
            <label for="imageSelect" class="form-label">
                ¿Desea cargar una imagen de la patología del paciente?
                <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Puede cargar una imagen existente o tomar una foto con su dispositivo. El modelo la analizará y la tendrá en cuenta a la hora de determinar el tratamiento."></i>
            </label>
            <select class="form-select" id="imageSelectScanned">
                <option value="no_image" selected>Sin Imagen</option>
                <option value="upload_image">Elegir imagen</option>
                <option value="take_image">Tomar imagen con el dispositivo</option>
            </select>
        </div>
        <div id="imageInputContainerScanned" class="mb-3"></div>

        <div class="mb-3">
            <label for="languageScanned" class="form-label">Seleccione el idioma de la respuesta:</label>
            <select class="form-select" id="languageScanned" name="language">
                <option value="ES">Español</option>
                <option value="EN">Inglés</option>
                <option value="FR">Francés</option>
            </select>
        </div>
    <!-- Añadimos los botones de "Generar Respuesta" y "Descargar Formulario Tipo" -->
        <div class="d-flex justify-content-between mt-3">
            <button type="button" class="btn btn-primary" id="generateScannedResponse">Generar Respuesta</button>
            <a href="https://iaenpsoriasis.pythonanywhere.com/download-form" class="btn btn-secondary" download>Descargar Formulario Tipo</a>
        </div>
        <p id="scanned-generating-message" class="mt-3 text-center fw-bold" style="display: none;">Su respuesta se está generando. Por favor, espere...</p>
      </div>

        <!-- Formulario para tomar una foto de los datos del paciente -->
      <div id="photoInputContainer" style="display:none;" class="mb-4">
        <label for="photoFile" class="form-label">
          Tome o seleccione la foto del informe del paciente
          <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Asegúrese de que la imagen sea clara y legible para obtener mejores resultados."></i>
        </label>
        <input type="file" name="patient_photo" class="form-control" id="photoFile" accept="image/*" capture="camera" required>

        <!-- Añadimos las opciones de imagen y idioma -->
        <div class="mb-3 mt-4">
            <label for="imageSelect" class="form-label">
                ¿Desea cargar una imagen de la patología del paciente?
                <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Puede cargar una imagen existente o tomar una foto con su dispositivo. El modelo la analizará y la tendrá en cuenta a la hora de determinar el tratamiento."></i>
            </label>
            <select class="form-select" id="imageSelectPhoto">
                <option value="no_image" selected>Sin Imagen</option>
                <option value="upload_image">Elegir imagen</option>
                <option value="take_image">Tomar imagen con el dispositivo</option>
            </select>
        </div>
        <div id="imageInputContainerPhoto" class="mb-3"></div>

        <div class="mb-3">
            <label for="languagePhoto" class="form-label">Seleccione el idioma de la respuesta:</label>
            <select class="form-select" id="languagePhoto" name="language">
                <option value="ES">Español</option>
                <option value="EN">Inglés</option>
                <option value="FR">Francés</option>
            </select>
        </div>
    <!-- Añadimos los botones de "Generar Respuesta" y "Descargar Formulario Tipo" -->
        <div class="d-flex justify-content-between mt-3">
            <button type="button" class="btn btn-primary" id="generatePhotoResponse">Generar Respuesta</button>
            <a href="https://iaenpsoriasis.pythonanywhere.com/download-form" class="btn btn-secondary" download>Descargar Formulario Tipo</a>
        </div>
        <p id="photo-generating-message" class="mt-3 text-center fw-bold" style="display: none;">Su respuesta se está generando. Por favor, espere...</p>
      </div>

      <!-- Formulario de Datos -->
      <form id="dataForm" style="display:none;" class="mb-3">
        <!-- Campo oculto para el user_id -->
        <input type="hidden" name="user_id" value="{{ user_id }}">
        <!-- Página 1: Datos Demográficos -->
        <div id="page1" class="form-page">
          <h5>
              Datos Demográficos
              <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="A continuación, puede completar los datos del paciente en la web. Si no dispone o no desea completar algún campo, puede dejarlo en blanco."></i>
          </h5>

          <div class="mb-3">
            <label for="patientAge" class="form-label">Edad del Paciente</label>
            <input type="number" class="form-control" id="patientAge" name="patient_age">
          </div>
          <div class="mb-3">
            <label for="patientSex" class="form-label">Sexo del Paciente</label>
            <select class="form-select" id="patientSex" name="patient_sex">
              <option value="" disabled selected>Seleccione una opción</option>
              <option value="hombre">Hombre</option>
              <option value="mujer">Mujer</option>
            </select>
          </div>
          <div class="mb-3">
            <label for="patientHeight" class="form-label">Altura del Paciente (cm)</label>
            <input type="number" class="form-control" id="patientHeight" name="patient_height">
          </div>
          <div class="mb-3">
            <label for="patientWeight" class="form-label">Peso del Paciente (Kg)</label>
            <input type="number" class="form-control" id="patientWeight" name="patient_weight">
          </div>
          <div class="d-flex justify-content-end">
            <button type="button" class="btn btn-secondary" id="nextPage1">Siguiente</button>
          </div>
        </div>

        <!-- Página 2: Antecedentes Médicos -->
        <div id="page2" class="form-page" style="display:none;">
          <h5>Antecedentes Médicos</h5>
          <div class="mb-3">
            <label for="medicationAllergies" class="form-label">Alergias a medicamentos</label>
            <input type="text" class="form-control" id="medicationAllergies" name="medication_allergies">
          </div>
          <div class="mb-3">
            <label for="cvRiskFactors" class="form-label">Factores de riesgo cardiovascular</label>
            <input type="text" class="form-control" id="cvRiskFactors" name="cv_risk_factors">
          </div>
          <!-- ... (Otros campos de la página 2) ... -->
          <div class="d-flex justify-content-between">
            <button type="button" class="btn btn-secondary" id="prevPage2">Anterior</button>
            <button type="button" class="btn btn-secondary" id="nextPage2">Siguiente</button>
          </div>
        </div>

        <!-- Página 3: Características Clínicas Psoriasis -->
        <div id="page3" class="form-page" style="display:none;">
          <h5>Características Clínicas Patología</h5>
          <div class="mb-3">
            <label for="psoriasisType" class="form-label">Tipo de patología</label>
            <input type="text" class="form-control" id="psoriasisType" name="psoriasis_type">
          </div>
          <div class="mb-3">
            <label for="lesionLocation" class="form-label">Localización de las lesiones</label>
            <input type="text" class="form-control" id="lesionLocation" name="lesion_location">
          </div>
          <!-- ... (Otros campos de la página 3) ... -->
          <div class="d-flex justify-content-between">
            <button type="button" class="btn btn-secondary" id="prevPage3">Anterior</button>
            <button type="button" class="btn btn-secondary" id="nextPage3">Siguiente</button>
          </div>
        </div>

        <!-- Página 4: Resultados de Pruebas -->
        <div id="page4" class="form-page" style="display:none;">
          <h5>Resultados de Pruebas</h5>
          <div class="mb-3">
            <label for="biomarkerLevels" class="form-label">Niveles de biomarcadores relevantes</label>
            <input type="text" class="form-control" id="biomarkerLevels" name="biomarker_levels">
          </div>
          <div class="mb-3">
            <label for="imagingResults" class="form-label">Resultados de pruebas de imagen (si corresponde)</label>
            <input type="text" class="form-control" id="imagingResults" name="imaging_results">
          </div>
          <div class="d-flex justify-content-between">
            <button type="button" class="btn btn-secondary" id="prevPage4">Anterior</button>
            <button type="button" class="btn btn-secondary" id="nextPage4">Siguiente</button>
          </div>
        </div>

        <!-- Página 5: Configuración del Algoritmo -->
        <div id="page5" class="form-page" style="display:none;">
          <h5>Configuración del Algoritmo</h5>
          <div class="mb-3">
            <label for="algorithmConsiderations" class="form-label">
                Conclusiones o consideraciones al algoritmo
                <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Ingrese cualquier consideración o conclusión específica sobre el tratamiento o análisis que el algoritmo debe tener en cuenta. De esta manera, el algoritmo podrá pensar como usted y determinar el tratamiento en función de sus criterios."></i>
            </label>
            <input type="text" class="form-control" id="algorithmConsiderations" name="algorithm_considerations" required>
          </div>
          <div class="mb-3">
            <label for="imageSelect" class="form-label">
                ¿Desea cargar una imagen de la patología del paciente?
                <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Puede cargar una imagen existente o tomar una foto con su dispositivo. El modelo la analizará y la tendrá en cuenta a la hora de determinar el tratamiento."></i>
            </label>
            <select class="form-select" id="imageSelectData" name="image_select">
              <option value="no_image" selected>Sin Imagen</option>
              <option value="upload_image">Elegir imagen</option>
              <option value="take_image">Tomar imagen con el dispositivo</option>
            </select>
          </div>
          <div id="imageInputContainerData" class="mb-3"></div>
          <div class="mb-3">
            <label for="languageData" class="form-label">Seleccione el idioma de la respuesta:</label>
            <select class="form-select" id="languageData" name="language">
              <option value="ES">Español</option>
              <option value="EN">Inglés</option>
              <option value="FR">Francés</option>
            </select>
          </div>
          <div class="d-flex justify-content-between">
            <button type="button" class="btn btn-secondary btn-anterior" id="prevPage5">Anterior</button>
            <div>
              <button type="submit" class="btn btn-primary">Generar Respuesta</button>
              <a href="https://iaenpsoriasis.pythonanywhere.com/download-form" class="btn btn-secondary" download>Descargar Formulario Tipo</a>
            </div>
          </div>
          <p id="data-generating-message" class="mt-3 text-center fw-bold" style="display: none;">Su respuesta se está generando. Por favor, espere...</p>
        </div>
      </form>
    </div>
    <!-- Formulario para entrada por voz -->
    <div id="voiceInputContainer" style="display:none;" class="mb-4">
      <label for="voiceInput" class="form-label">
        Presione el botón y hable para introducir los datos del paciente
        <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Use su voz para proporcionar información relevante sobre el paciente."></i>
      </label>
      <div class="d-flex align-items-center mb-2">
        <button type="button" id="startVoiceInput" class="btn btn-primary me-2">Iniciar Grabación</button>
        <button type="button" id="stopVoiceInput" class="btn btn-danger" disabled>Parar Grabación</button>
      </div>
      <p id="voiceStatus" class="mt-2"></p>
      <textarea id="voiceTextOutput" class="form-control mt-2" rows="6" placeholder="El texto reconocido aparecerá aquí..."></textarea>

      <!-- Opciones de imagen y idioma -->
      <div class="mb-3 mt-4">
          <label for="imageSelectVoice" class="form-label">
              ¿Desea cargar una imagen de la patología del paciente?
              <i class="bi bi-info-circle" data-bs-toggle="tooltip" data-bs-placement="right" title="Puede cargar una imagen existente o tomar una foto con su dispositivo. El modelo la analizará y la tendrá en cuenta a la hora de determinar el tratamiento."></i>
          </label>
          <select class="form-select" id="imageSelectVoice">
              <option value="no_image" selected>Sin Imagen</option>
              <option value="upload_image">Elegir imagen</option>
              <option value="take_image">Tomar imagen con el dispositivo</option>
          </select>
      </div>
      <div id="imageInputContainerVoice" class="mb-3"></div>
      <div class="mb-3">
          <label for="languageVoice" class="form-label">Seleccione el idioma de la respuesta:</label>
          <select class="form-select" id="languageVoice" name="language">
              <option value="ES">Español</option>
              <option value="EN">Inglés</option>
              <option value="FR">Francés</option>
          </select>
      </div>
      <div class="d-flex justify-content-between mt-3">
          <button type="button" class="btn btn-primary" id="generateVoiceResponse">Generar Respuesta</button>
          <a href="https://iaenpsoriasis.pythonanywhere.com/download-form" class="btn btn-secondary" download>Descargar Formulario Tipo</a>
      </div>
      <p id="voice-generating-message" class="mt-3 text-center fw-bold" style="display: none;">Su respuesta se está generando. Por favor, espere...</p>
    </div>


    <!-- Respuesta del Servidor -->
    <div id="response-container" class="alert alert-success d-none" role="alert">
      <h4 class="alert-heading">Respuesta Generada</h4>
      <p id="response-text" class="mb-0"></p>
      <form id="emailForm" class="mt-3">
        <div class="mb-3">
          <label for="email" class="form-label fw-bold">Correo electrónico:</label>
          <input type="email" class="form-control" id="email" name="email" required>
        </div>
        <input type="hidden" id="response-content" name="response-content"> <!-- Campo oculto para la respuesta -->
        <button type="submit" class="btn btn-primary">Enviar por correo</button>
      </form>
      <div class="form-section mt-5">
          <h3>Chatbot del Tratamiento</h3>
          <iframe src="https://chatbot-psoriasis-gemini.streamlit.app/?embed=true&txt_formulario_url={{ txt_formulario_url }}&txt_tratamiento_url={{ txt_tratamiento_url }}"
                  width="100%" height="600" style="border:none;"></iframe>
      </div>
    </div>


    <!-- Cuadro de texto para reseñas -->
    <div class="form-section mt-5">
      <h3>¿Qué te parecen los tratamientos generados? ¿Alguna sugerencia?</h3>
      <form id="reviewForm">
        <div class="mb-3">
          <textarea class="form-control" id="reviewText" rows="3" required></textarea>
        </div>
        <button type="submit" class="btn btn-primary">Enviar reseña</button>
      </form>
      <p id="review-message" class="mt-3 text-center fw-bold" style="display: none;">Gracias por tu reseña.</p>
    </div>

    <!-- ¿Cómo funciona? -->
    <h3>¿Cómo funciona?</h3>
    <p class="form-section" id="como-funciona-text">
      Este proyecto nace con el objetivo de realizar una aproximación hacia el mejor tratamiento disponible para los pacientes con Psoriasis según el Protocolo de Consenso de Psoriasis en Castilla la Mancha. Para ello, se ha desarrollado un modelo de IA que analiza y aprende sobre la Psoriasis y sus diversos tratamientos, siendo capaz de determinar el tratamiento ideal para el paciente. Únicamente se ha de cargar un formulario tipo el cual pueden descargar en el botón superior con los datos del paciente y pulsar en el botón "Generar Respuesta". A continuación, el modelo generará un informe individualizado sobre el paciente con la justificación del tratamiento elegido así como consideraciones a tener en cuenta sobre el mismo.
    </p>

    <!-- Título para entidades colaboradas -->
    <h3>Nuestros Colaboradores</h3>
    <div class="enlaces-recomendados nuestros-colaboradores-logos d-flex flex-wrap justify-content-center">
       <a href="#">
          <img src="static/junt.png" alt="Nuevo Logo">
       </a>
       <a href="#">
          <img src="static/ses.png" alt="Logo del Medio">
       </a>
       <a href="#">
          <img src="static/hosp.png" alt="Logo">
       </a>
    </div>

    <!-- Enlaces Recomendados -->
    <h3>Enlaces Recomendados</h3>
    <div class="enlaces-recomendados d-flex flex-wrap justify-content-center">
      <a href="https://www.uptodate.com/login" target="_blank">
        <img src="static/unnamed.png" alt="UpToDate">
        <span>UpToDate</span>
      </a>
      <a href="https://www.actasdermo.org" target="_blank">
        <img src="static/actas_4_1.png" alt="ACTAS">
        <span>ACTAS</span>
      </a>
      <a href="https://aedv.es" target="_blank">
        <img src="static/cambio_2.png" alt="AEDV">
        <span>AEDV</span>
      </a>
      <a href="https://www.jaad.org" target="_blank">
        <img src="static/cambio_8.png" alt="JAAD">
        <span>JAAD</span>
      </a>
      <a href="https://eadv.org" target="_blank">
        <img src="static/cambio_10.png" alt="EADV">
        <span>EADV</span>
      </a>
      <a href="https://www.comtoledo.org/" target="_blank">
        <img src="static/imagen6.png" alt="ICOMT">
        <span>ICOMT</span>
      </a>
      <a href="https://www.fisterra.com/" target="_blank">
        <img src="static/imagen7.png" alt="Fisterra">
        <span>Fisterra</span>
      </a>
      <a href="https://www.nejm.org/" target="_blank">
        <img src="static/imagen8.png" alt="NEJM">
        <span>NEJM</span>
      </a>
      <a href="https://aedv.es/grupos-de-trabajo/psoriasis/" target="_blank">
        <img src="static/cambio_5.png" alt="GPs">
        <span>GPs</span>
      </a>
      <a href="https://www.buymeacoffee.com/psoriasisiaclm" target="_blank">
        <img src="static/imagen11.png" alt="Un café?">
        <span>Un café?</span>
      </a>
    </div>


    <!-- Banner de Coffee -->
    <a href="https://www.buymeacoffee.com/psoriasisiaclm" target="_blank" class="d-block mt-4">
      <img src="static/banner_coffee_3.png" alt="Banner" class="banner-img">
    </a>
  </div>

  <!-- Copyright -->
  <div class="copyright bg-white">
    <p>© 2024, IA en Psoriasis. Todos los derechos reservados.</p>
  </div>

  <!-- Bootstrap 5 JS y Dependencias -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            let recognition = null;
            // Actualización del nombre del archivo seleccionado
            const customFileInput = document.getElementById('customFile');
            customFileInput.addEventListener('change', function(event) {
                // Puedes agregar lógica adicional si lo deseas
            });

            // Manejadores de eventos para los formularios
            document.getElementById('uploadForm').addEventListener('submit', handleFormSubmit);
            document.getElementById('dataForm').addEventListener('submit', handleDataFormSubmit);

            // Manejador para el desplegable de modo de trabajo
            document.getElementById('modeSelect').addEventListener('change', function(event) {
                const selectedMode = event.target.value;
                const uploadForm = document.getElementById('uploadForm');
                const dataForm = document.getElementById('dataForm');
                const scannedFormContainer = document.getElementById('scannedFormContainer'); // Para cargar archivos escaneados
                const photoInputContainer = document.getElementById('photoInputContainer');   // Para tomar fotos de datos
                const voiceInputContainer = document.getElementById('voiceInputContainer');

                if (selectedMode === 'upload') {
                    uploadForm.style.display = 'block';
                    dataForm.style.display = 'none';
                    scannedFormContainer.style.display = 'none';
                    photoInputContainer.style.display = 'none';
                    voiceInputContainer.style.display = 'none';
                } else if (selectedMode === 'form') {
                    uploadForm.style.display = 'none';
                    dataForm.style.display = 'block';
                    scannedFormContainer.style.display = 'none';
                    photoInputContainer.style.display = 'none';
                    voiceInputContainer.style.display = 'none';
                    showPage(0);
                } else if (selectedMode === 'upload_scanned') {  // Nueva opción: Cargar archivo escaneado
                    uploadForm.style.display = 'none';
                    dataForm.style.display = 'none';
                    scannedFormContainer.style.display = 'block';
                    photoInputContainer.style.display = 'none';
                    voiceInputContainer.style.display = 'none';
                } else if (selectedMode === 'take_photo') {  // Nueva opción: Tomar foto de los datos del paciente
                    uploadForm.style.display = 'none';
                    dataForm.style.display = 'none';
                    scannedFormContainer.style.display = 'none';
                    photoInputContainer.style.display = 'block';
                    voiceInputContainer.style.display = 'none';
                } else if (selectedMode === 'input_voice') {
                    uploadForm.style.display = 'none';
                    dataForm.style.display = 'none';
                    scannedFormContainer.style.display = 'none';
                    photoInputContainer.style.display = 'none';
                    voiceInputContainer.style.display = 'block';
                } else {
                    uploadForm.style.display = 'none';
                    dataForm.style.display = 'none';
                    scannedFormContainer.style.display = 'none';
                    photoInputContainer.style.display = 'none';
                    voiceInputContainer.style.display = 'none';
                }

                document.getElementById('response-container').classList.add('d-none');
            });

            // Manejador para el desplegable de selección de documento
            document.getElementById('documentSelect').addEventListener('change', function(event) {
                const selectedOption = event.target.value;
                const documentInputContainer = document.getElementById('documentInputContainer');

                if (selectedOption === 'upload_document') {
                    documentInputContainer.style.display = 'block';
                } else {
                    documentInputContainer.style.display = 'none';
                }
            });

            // Inicializar la selección predeterminada
            document.getElementById('documentSelect').dispatchEvent(new Event('change'));
            document.getElementById('modeSelect').dispatchEvent(new Event('change'));

            // Función para mostrar la página actual del formulario
            function showPage(pageNumber) {
                const pages = document.querySelectorAll('.form-page');
                pages.forEach((page, index) => {
                    if (index === pageNumber) {
                        page.style.display = 'block';
                    } else {
                        page.style.display = 'none';
                    }
                });
            }

            // Manejadores para la navegación entre páginas del formulario
            const totalPages = 5; // Ajusta según el número total de páginas
            let currentPage = 0;

            document.getElementById('nextPage1').addEventListener('click', function() {
                currentPage = 1;
                showPage(currentPage);
            });

            document.getElementById('prevPage2').addEventListener('click', function() {
                currentPage = 0;
                showPage(currentPage);
            });

            document.getElementById('nextPage2').addEventListener('click', function() {
                currentPage = 2;
                showPage(currentPage);
            });

            document.getElementById('prevPage3').addEventListener('click', function() {
                currentPage = 1;
                showPage(currentPage);
            });

            document.getElementById('nextPage3').addEventListener('click', function() {
                currentPage = 3;
                showPage(currentPage);
            });

            document.getElementById('prevPage4').addEventListener('click', function() {
                currentPage = 2;
                showPage(currentPage);
            });

            document.getElementById('nextPage4').addEventListener('click', function() {
                currentPage = 4;
                showPage(currentPage);
            });

            document.getElementById('prevPage5').addEventListener('click', function() {
                currentPage = 3;
                showPage(currentPage);
            });

            // Manejador para el selector de imágenes en el formulario de datos
            document.getElementById('imageSelectData').addEventListener('change', function(event) {
                const imageInputContainer = document.getElementById('imageInputContainerData');
                const selectedOption = event.target.value;

                imageInputContainer.innerHTML = '';

                if (selectedOption === 'upload_image') {
                    const imageInput = document.createElement('input');
                    imageInput.type = 'file';
                    imageInput.accept = 'image/*';
                    imageInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(imageInput);
                } else if (selectedOption === 'take_image') {
                    const cameraInput = document.createElement('input');
                    cameraInput.type = 'file';
                    cameraInput.accept = 'image/*';
                    cameraInput.capture = 'environment';
                    cameraInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(cameraInput);
                }
            });

            // Manejador para el selector de imágenes en el formulario de carga
            document.getElementById('imageSelect').addEventListener('change', function(event) {
                const imageInputContainer = document.getElementById('imageInputContainer');
                const selectedOption = event.target.value;

                imageInputContainer.innerHTML = '';

                if (selectedOption === 'upload_image') {
                    const imageInput = document.createElement('input');
                    imageInput.type = 'file';
                    imageInput.accept = 'image/*';
                    imageInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(imageInput);
                } else if (selectedOption === 'take_image') {
                    const cameraInput = document.createElement('input');
                    cameraInput.type = 'file';
                    cameraInput.accept = 'image/*';
                    cameraInput.capture = 'environment';
                    cameraInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(cameraInput);
                }
            });

            // Manejador para el selector de imágenes en el formulario de archivo escaneado
            document.getElementById('imageSelectScanned').addEventListener('change', function(event) {
                const imageInputContainer = document.getElementById('imageInputContainerScanned');
                const selectedOption = event.target.value;

                imageInputContainer.innerHTML = ''; // Limpiar el contenedor antes de añadir un nuevo input

                if (selectedOption === 'upload_image') {
                    const imageInput = document.createElement('input');
                    imageInput.type = 'file';
                    imageInput.accept = 'image/*';
                    imageInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(imageInput);
                } else if (selectedOption === 'take_image') {
                    const cameraInput = document.createElement('input');
                    cameraInput.type = 'file';
                    cameraInput.accept = 'image/*';
                    cameraInput.capture = 'environment';
                    cameraInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(cameraInput);
                }
            });

            // Manejador para el selector de imágenes en el formulario de toma de fotos
            document.getElementById('imageSelectPhoto').addEventListener('change', function(event) {
                const imageInputContainer = document.getElementById('imageInputContainerPhoto');
                const selectedOption = event.target.value;

                imageInputContainer.innerHTML = ''; // Limpiar el contenedor antes de añadir un nuevo input

                if (selectedOption === 'upload_image') {
                    const imageInput = document.createElement('input');
                    imageInput.type = 'file';
                    imageInput.accept = 'image/*';
                    imageInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(imageInput);
                } else if (selectedOption === 'take_image') {
                    const cameraInput = document.createElement('input');
                    cameraInput.type = 'file';
                    cameraInput.accept = 'image/*';
                    cameraInput.capture = 'environment';
                    cameraInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(cameraInput);
                }
            });
            // Manejador para el botón de inicio de grabación de voz
            document.getElementById('startVoiceInput').addEventListener('click', function() {
                // Verificar si el navegador soporta la API de reconocimiento de voz
                if ('webkitSpeechRecognition' in window) {
                    recognition = new webkitSpeechRecognition();
                    recognition.lang = 'es-ES'; // Establecer el idioma a español
                    recognition.continuous = true; // Habilitar reconocimiento continuo
                    recognition.interimResults = false; // Solo resultados finales
                    recognition.maxAlternatives = 1;

                    recognition.onstart = function() {
                        document.getElementById('voiceStatus').textContent = 'Escuchando...';
                        document.getElementById('startVoiceInput').disabled = true;
                        document.getElementById('stopVoiceInput').disabled = false;
                    };

                    recognition.onerror = function(event) {
                        document.getElementById('voiceStatus').textContent = 'Error en el reconocimiento de voz: ' + event.error;
                    };

                    recognition.onend = function() {
                        document.getElementById('voiceStatus').textContent = 'Grabación finalizada.';
                        document.getElementById('startVoiceInput').disabled = false;
                        document.getElementById('stopVoiceInput').disabled = true;
                    };

                    recognition.onresult = function(event) {
                        let finalTranscript = '';

                        for (let i = event.resultIndex; i < event.results.length; i++) {
                            let transcript = event.results[i][0].transcript;
                            if (event.results[i].isFinal) {
                                finalTranscript += transcript + ' ';
                            }
                        }

                        // Añadir al texto existente
                        let currentText = document.getElementById('voiceTextOutput').value;
                        document.getElementById('voiceTextOutput').value = currentText + finalTranscript;
                    };

                    recognition.start();
                } else {
                    alert('Su navegador no soporta reconocimiento de voz. Por favor, use Chrome o Edge.');
                }
            });

            // Manejador para el botón de parar grabación de voz
            document.getElementById('stopVoiceInput').addEventListener('click', function() {
                if (recognition) {
                    recognition.stop();
                    recognition = null; // Reiniciar la variable recognition
                }
            });

            document.getElementById('imageSelectVoice').addEventListener('change', function(event) {
                const imageInputContainer = document.getElementById('imageInputContainerVoice');
                const selectedOption = event.target.value;

                imageInputContainer.innerHTML = '';

                if (selectedOption === 'upload_image') {
                    const imageInput = document.createElement('input');
                    imageInput.type = 'file';
                    imageInput.accept = 'image/*';
                    imageInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(imageInput);
                } else if (selectedOption === 'take_image') {
                    const cameraInput = document.createElement('input');
                    cameraInput.type = 'file';
                    cameraInput.accept = 'image/*';
                    cameraInput.capture = 'environment';
                    cameraInput.classList.add('form-control', 'mt-2');
                    imageInputContainer.appendChild(cameraInput);
                }
            });

            document.getElementById('generateVoiceResponse').addEventListener('click', handleVoiceInput);




            // Manejador para el envío del formulario de correo electrónico
            document.getElementById('emailForm').addEventListener('submit', function(event) {
                event.preventDefault();
                const emailInput = document.getElementById('email');
                const responseContent = document.getElementById('response-content').value;

                if (emailInput.value === '') {
                    alert("Debe introducir un correo");
                    return false;
                }

                const formData = {
                    email: emailInput.value,
                    'response-content': responseContent
                };

                fetch('https://iaenpsoriasis.pythonanywhere.com/send_email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                })
                .catch((error) => {
                    alert('Error al enviar el correo: ' + error.message);
                });

                return false;
            });

            // Asignar event listeners a los botones "Generar Respuesta"
            document.getElementById('generateScannedResponse').addEventListener('click', handleScannedFileUpload);
            document.getElementById('generatePhotoResponse').addEventListener('click', handlePhotoUpload);

            // Inicializar los tooltips de Bootstrap
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });

            // Manejador para el envío de reseñas
            document.getElementById('reviewForm').addEventListener('submit', async function(event) {
                event.preventDefault(); // Prevenir que se recargue la página
                const reviewText = document.getElementById('reviewText').value;
                const userId = "{{ user_id }}";  // Captura el user_id desde el contexto

                if (!reviewText.trim()) {
                  alert("Por favor, escribe tu reseña.");
                  return;
                }

                // Enviar la reseña al backend
                try {
                  const response = await fetch('/submit_review', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ review: reviewText, user_id: userId })
                  });

                  const data = await response.json();
                  if (response.ok) {
                    document.getElementById('review-message').style.display = 'block';
                    document.getElementById('reviewForm').reset();
                  } else {
                    alert("Error: " + data.message);
                  }
                } catch (error) {
                  alert("Error al enviar la reseña: " + error.message);
                }
            });

            });

        // Definir las funciones en el ámbito global
        async function handleScannedFileUpload() {
            const scannedFileInput = document.getElementById('scannedFile');
            const imageInputContainer = document.getElementById('imageInputContainerScanned');
            const imageInput = imageInputContainer.querySelector('input[type="file"]'); // Para la imagen opcional
            const languageSelect = document.getElementById('languageScanned').value; // Para el idioma seleccionado
            const formData = new FormData();

            // Verificar si se ha seleccionado un archivo escaneado
            if (scannedFileInput.files.length === 0) {
                alert("Debe seleccionar un archivo escaneado.");
                return;
            }

            // Añadir el archivo escaneado al FormData
            formData.append('scanned_file', scannedFileInput.files[0]);

            // Añadir imagen si se ha seleccionado
            if (imageInput && imageInput.files.length > 0) {
                formData.append('image', imageInput.files[0]);
            }

            // Obtener el valor de advancedInstructions y agregarlo a formData
            const advancedInstructions = document.getElementById('advancedInstructions').value;
            formData.append('advanced_instructions', advancedInstructions);

            const pathology = document.getElementById('pathologySelect').value;
            formData.append('pathology', pathology);


            // Añadir el idioma seleccionado
            formData.append('user_id', '{{ user_id }}'); // Asegúrate de que esto se renderiza correctamente
            formData.append('language', languageSelect);

            // Mostrar mensaje de carga mientras se genera la respuesta
            document.getElementById('scanned-generating-message').style.display = 'block';

            try {
                // Enviar solicitud al servidor
                const response = await fetch('https://iaenpsoriasis.pythonanywhere.com/upload_scanned_file', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (response.ok) {
                    // Mostrar la respuesta generada en el contenedor
                    document.getElementById('response-text').innerHTML = data.message;
                    document.getElementById('response-container').classList.remove('d-none');
                } else {
                    alert("Error: " + data.error);
                }

            } catch (error) {
                console.error("Error al cargar el archivo escaneado:", error);
                alert("Error al cargar el archivo escaneado.");
            }

            // Ocultar mensaje de carga
            document.getElementById('scanned-generating-message').style.display = 'none';
        }

        async function handlePhotoUpload() {
            const photoFileInput = document.getElementById('photoFile');
            const imageInput = document.getElementById('imageInputContainerPhoto').querySelector('input[type="file"]'); // Para la imagen opcional
            const languageSelect = document.getElementById('languagePhoto').value; // Para el idioma seleccionado
            const formData = new FormData();

            // Verificar si se ha tomado o seleccionado una foto
            if (photoFileInput.files.length === 0) {
                alert("Debe tomar o seleccionar una foto.");
                return;
            }

            // Añadir la foto del informe del paciente al FormData
            formData.append('patient_photo', photoFileInput.files[0]);

            // Añadir imagen si se ha seleccionado
            if (imageInput && imageInput.files.length > 0) {
                formData.append('image', imageInput.files[0]);
            }

            // Obtener el valor de advancedInstructions y agregarlo a formData
            const advancedInstructions = document.getElementById('advancedInstructions').value;
            formData.append('advanced_instructions', advancedInstructions);

            const pathology = document.getElementById('pathologySelect').value;
            formData.append('pathology', pathology);


            // Añadir el idioma seleccionado
            formData.append('user_id', '{{ user_id }}'); // Asegúrate de que esto se renderiza correctamente
            formData.append('language', languageSelect);

            // Mostrar mensaje de carga mientras se genera la respuesta
            document.getElementById('photo-generating-message').style.display = 'block';

            try {
                // Enviar solicitud al servidor
                const response = await fetch('https://iaenpsoriasis.pythonanywhere.com/upload_photo', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (response.ok) {
                    // Mostrar la respuesta generada en el contenedor
                    document.getElementById('response-text').innerHTML = data.message;
                    document.getElementById('response-container').classList.remove('d-none');
                } else {
                    alert("Error: " + data.error);
                }

            } catch (error) {
                console.error("Error al cargar la foto:", error);
                alert("Error al cargar la foto.");
            }

            // Ocultar mensaje de carga
            document.getElementById('photo-generating-message').style.display = 'none';
        }

        async function handleVoiceInput() {
            const voiceText = document.getElementById('voiceTextOutput').value.trim();
            const imageInputContainer = document.getElementById('imageInputContainerVoice');
            const imageInput = imageInputContainer.querySelector('input[type="file"]');
            const languageSelect = document.getElementById('languageVoice').value;
            const formData = new FormData();

            if (!voiceText) {
                alert("Debe proporcionar entrada de voz.");
                return;
            }

            // Añadir el texto de voz al FormData
            formData.append('voice_text', voiceText);

            // Añadir imagen si se ha seleccionado
            if (imageInput && imageInput.files.length > 0) {
                formData.append('image', imageInput.files[0]);
            }

            // Obtener las instrucciones avanzadas
            const advancedInstructions = document.getElementById('advancedInstructions').value;
            formData.append('advanced_instructions', advancedInstructions);

            const pathology = document.getElementById('pathologySelect').value;
            formData.append('pathology', pathology);


            // Añadir el idioma seleccionado y el ID de usuario
            formData.append('user_id', '{{ user_id }}');
            formData.append('language', languageSelect);

            // Mostrar mensaje de carga
            document.getElementById('voice-generating-message').style.display = 'block';

            try {
                // Enviar solicitud al servidor
                const response = await fetch('https://iaenpsoriasis.pythonanywhere.com/voice_input', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (response.ok) {
                    document.getElementById('response-text').innerHTML = data.message;
                    document.getElementById('response-container').classList.remove('d-none');
                } else {
                    alert("Error: " + data.error);
                }

            } catch (error) {
                console.error("Error al procesar la entrada de voz:", error);
                alert("Error al procesar la entrada de voz.");
            }

            // Ocultar mensaje de carga
            document.getElementById('voice-generating-message').style.display = 'none';
        }


        // Función para manejar el envío del formulario de carga de archivo
        async function handleFormSubmit(event) {
            event.preventDefault();

            const fileInput = document.getElementById('customFile');
            if (fileInput.files.length === 0) {
                alert("Debe seleccionar un archivo");
                return;
            }

            const form = event.target;
            const formData = new FormData(form);
            formData.append('ajax', 'true');

            // Obtener el valor de advancedInstructions y agregarlo a formData
            const advancedInstructions = document.getElementById('advancedInstructions').value;
            formData.append('advanced_instructions', advancedInstructions);

            const pathology = document.getElementById('pathologySelect').value;
            formData.append('pathology', pathology);


            // Agregar la imagen si se ha seleccionado o tomado
            const imageInputContainer = document.getElementById('imageInputContainer');
            const imageInput = imageInputContainer.querySelector('input[type="file"]');
            if (imageInput && imageInput.files.length > 0) {
                formData.append('image', imageInput.files[0]);
            }

            // Verificar si se seleccionó un documento personalizado
            const documentSelect = document.getElementById('documentSelect').value;
            if (documentSelect === 'upload_document') {
                const customDocumentInput = document.getElementById('customDocumentFile');
                if (customDocumentInput.files.length === 0) {
                    alert("Debe seleccionar un documento para nutrir a la IA.");
                    return;
                }
                formData.append('custom_document', customDocumentInput.files[0]);
            }

            // Mostrar mensaje de carga
            document.getElementById('upload-generating-message').style.display = 'block';

            try {
                const response = await fetch('https://iaenpsoriasis.pythonanywhere.com/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const responseData = await response.json();  // Cambiamos a JSON
                    // Manejar error específico de límite de consultas
                    if (response.status === 403 && responseData.error === "Has alcanzado el límite de consultas gratuitas") {
                        alert(responseData.error);  // Muestra el error de límite de consultas
                        document.getElementById('upload-generating-message').style.display = 'none';
                        return;
                    }

                    throw new Error(`Error: ${response.statusText}`);
                }

                const data = await response.text();
                if (data) {
                    document.getElementById('response-text').innerHTML = data;
                    document.getElementById('response-container').classList.remove('d-none');
                    document.getElementById('upload-generating-message').style.display = 'none';
                    document.getElementById('response-content').value = data

                    // Limpiar el formulario y restaurar el campo user_id
                    form.reset();  // Limpia el formulario

                    const userIdField = document.createElement('input');
                    userIdField.setAttribute('type', 'hidden');
                    userIdField.setAttribute('name', 'user_id');
                    userIdField.setAttribute('value', "{{ user_id }}");  // Asegúrate de que el user_id esté aquí
                    form.appendChild(userIdField);

                } else {
                    alert("No se ha podido generar la respuesta.");
                    document.getElementById('upload-generating-message').style.display = 'none';
                }
            } catch (error) {
                alert(`Error al enviar la solicitud: ${error.message}`);
                document.getElementById('upload-generating-message').style.display = 'none';
            }
        }

        // Función para manejar el envío del formulario de datos
        async function handleDataFormSubmit(event) {
            event.preventDefault();

            console.log("handleDataFormSubmit fue llamado."); // Mensaje de depuración

            if (!validateCurrentPage()) {
                return;
            }

            const languageSelect = document.getElementById('languageData').value
            const form = event.target;
            const formData = new FormData(form);
            formData.append('ajax', 'true');

            formData.append('user_id', '{{ user_id }}'); // Asegúrate de que este valor se renderiza correctamente
            formData.append('language', languageSelect);

            // Obtener el valor de advancedInstructions y agregarlo a formData
            const advancedInstructions = document.getElementById('advancedInstructions').value;
            formData.append('advanced_instructions', advancedInstructions);

            const pathology = document.getElementById('pathologySelect').value;
            formData.append('pathology', pathology);



            // Agregar la imagen si se ha seleccionado o tomado
            const imageInput = document.getElementById('imageInputContainerData').querySelector('input[type="file"]');
            if (imageInput && imageInput.files.length > 0) {
                formData.append('image', imageInput.files[0]);
            }

            // Verificar si se seleccionó un documento personalizado
            const documentSelect = document.getElementById('documentSelect').value;
            if (documentSelect === 'upload_document') {
                const customDocumentInput = document.getElementById('customDocumentFile');
                if (customDocumentInput.files.length === 0) {
                    alert("Debe seleccionar un documento para nutrir a la IA.");
                    return;
                }
                formData.append('custom_document', customDocumentInput.files[0]);
            }

            // Mostrar mensaje de carga
            document.getElementById('data-generating-message').style.display = 'block';

            try {
                const response = await fetch('https://iaenpsoriasis.pythonanywhere.com/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Error: ${response.statusText}`);
                }

                const data = await response.text();
                if (data) {
                    document.getElementById('response-text').innerHTML = data;
                    document.getElementById('response-container').classList.remove('d-none');
                    document.getElementById('data-generating-message').style.display = 'none';
                    document.getElementById('response-content').value = data;
                } else {
                    alert("No se ha podido generar la respuesta.");
                    document.getElementById('data-generating-message').style.display = 'none';
                }
            } catch (error) {
                alert(`Error al enviar la solicitud: ${error.message}`);
                document.getElementById('data-generating-message').style.display = 'none';
            }
        }

        // Función para validar todos los campos requeridos en todas las páginas del formulario
        function validateAllPages() {
            const pages = document.querySelectorAll('.form-page');
            for (const page of pages) {
                const inputs = page.querySelectorAll('input:required, select:required');
                for (const input of inputs) {
                    if (!input.checkValidity()) {
                        alert("Por favor, complete todos los campos requeridos.");
                        return false;
                    }
                }
            }
            return true;
        }
        function validateCurrentPage() {
            // Seleccionar la página que está actualmente visible
            const visiblePage = document.querySelector('.form-page:not([style*="display: none"])');

            if (!visiblePage) {
                alert("No se encontró la página visible del formulario.");
                return false;
            }

            // Seleccionar todos los campos requeridos dentro de la página visible
            const requiredFields = visiblePage.querySelectorAll('input:required, select:required, textarea:required');

            for (const field of requiredFields) {
                if (!field.value || field.value.trim() === "") {
                    alert("Por favor, complete todos los campos requeridos.");
                    field.focus();
                    return false;
                }
            }

            return true;
        }

    </script>

</body>
</html>

"""

# Diccionario que contiene los IDs de los dermatólogos y su límite de consultas
dermatologos = {
    "abc123": 7,  # ID: abc123 tiene un límite de 10 consultas
    "def456": 12,  # ID: def456 tiene un límite de 5 consultas
    "gerardo": 11,
    "alvaro.gomez": 11,
    "carolina": 11,
    "isabel": 11,
    "a_elisabet": 11,  # ID: ghi789 tiene un límite de 8 consultas
    "juanjo_amoros": 10,
}


def extraer_imagen_de_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    images = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(image)
    return images  # Lista de imágenes extraídas del PDF


def convert_image_to_bytes(image):
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="PNG")  # Convierte la imagen a bytes
    return img_byte_arr.getvalue()


# Leer cuántas consultas ha realizado un dermatólogo
def leer_consultas(user_id):
    try:
        with open("consultas.txt", "r") as f:
            for line in f:
                id_registrado, consultas = line.strip().split(",")
                if id_registrado == user_id:
                    return int(consultas)
    except FileNotFoundError:
        # Si no existe el archivo aún, es la primera consulta
        return 0
    return 0


# Actualizar el número de consultas en el archivo
def actualizar_consultas(user_id, consultas_actuales):
    lines = []
    encontrado = False

    try:
        with open("consultas.txt", "r") as f:
            lines = f.readlines()

        # Actualizar o agregar el número de consultas del dermatólogo
        with open("consultas.txt", "w") as f:
            for line in lines:
                id_registrado, consultas = line.strip().split(",")
                if id_registrado == user_id:
                    f.write(f"{user_id},{consultas_actuales}\n")
                    encontrado = True
                else:
                    f.write(line)
            # Si el ID no estaba en el archivo, agregarlo
            if not encontrado:
                f.write(f"{user_id},{consultas_actuales}\n")
    except FileNotFoundError:
        # Si no existe el archivo, crear el archivo por primera vez
        with open("consultas.txt", "w") as f:
            f.write(f"{user_id},{consultas_actuales}\n")


def extraer_texto_de_docx(ruta_archivo):
    doc = Document(ruta_archivo)
    texto_completo = []
    for para in doc.paragraphs:
        texto_completo.append(para.text)
    return "\n".join(texto_completo)


def extraer_texto_de_pdf(ruta_archivo):
    doc = fitz.open(ruta_archivo)
    texto_completo = []
    for pagina in doc:
        texto_completo.append(pagina.get_text())
    return "\n".join(texto_completo)


def dividir_en_segmentos(texto, chunk_size=1000, chunk_overlap=100):
    # Inicializamos el splitter recursivo
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,  # Tamaño máximo de cada fragmento
        chunk_overlap=chunk_overlap,  # Superposición entre fragmentos
        separators=["\n\n", "\n", " ", ""],
    )

    # Dividimos el texto
    segmentos = splitter.split_text(texto)

    return segmentos


def generar_embeddings(segmentos):
    embeddings = []
    for segmento in segmentos:
        response = openai.Embedding.create(
            input=[segmento],
            model="text-embedding-3-large",  # Ajusta el modelo según tus necesidades
        )
        embedding_vector = response["data"][0]["embedding"]
        embeddings.append(embedding_vector)
    return embeddings


def consultar_modelo_multimodal(image_bytes, prompt):
    # Convertir la imagen en una cadena de base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Construir el contexto como lo haces en las otras partes del código
    system_prompt = {
        "role": "system",
        "content": """
        Por favor, analiza la imagen de un informe escaneado o foto y extrae los datos relevantes del paciente, como su edad, sexo, altura, peso, condiciones médicas, etc.
        """,
    }

    # Contenido del usuario con la imagen en base64 y el prompt
    user_content = {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            },
        ],
    }

    # Realizar la llamada a GPT-4 con capacidad multimodal
    response = openai.ChatCompletion.create(
        model="chatgpt-4o-latest",  # Asegúrate de usar el modelo multimodal correcto
        messages=[system_prompt, user_content],
    )

    # Devolver la respuesta generada
    return response["choices"][0]["message"]["content"]


@app.route("/submit_review", methods=["POST"])
def submit_review():
    try:
        # Obtener los datos enviados
        data = request.get_json()
        review_text = data.get("review")
        user_id = data.get("user_id")

        # Verificar que el texto y el user_id existan
        if not review_text or not user_id:
            return jsonify({"message": "Faltan datos para enviar la reseña"}), 400

        # Guardar la reseña en un archivo de texto
        with open("reseñas.txt", "a") as file:
            file.write(f"ID de usuario: {user_id}, Reseña: {review_text}\n")

        return jsonify({"message": "Reseña guardada con éxito"}), 200

    except Exception as e:
        return jsonify({"message": f"Error al guardar la reseña: {e}"}), 500


@app.route("/voice_input", methods=["POST"])
def voice_input():
    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"error": "ID de usuario no proporcionado"}), 400

    # Verificar si el ID es válido
    if user_id not in dermatologos:
        return jsonify({"error": "ID no válido"}), 403

    # Obtener el límite de consultas y las consultas realizadas
    limite_consultas = dermatologos[user_id]
    consultas_realizadas = leer_consultas(user_id)

    # Verificar si ha alcanzado el límite de consultas
    if consultas_realizadas >= limite_consultas:
        return jsonify({"error": "Has alcanzado el límite de consultas gratuitas"}), 403

    # Obtener el texto de voz
    voice_text = request.form.get("voice_text")
    if not voice_text:
        return jsonify({"error": "No se ha proporcionado texto de voz"}), 400

    language = request.form.get("language", "ES")
    advanced_instructions = request.form.get("advanced_instructions", "")

    pathology = request.form.get("pathology", "psoriasis")

    # Verificar si se ha subido una imagen de la psoriasis
    imagen_base64 = None
    if "image" in request.files:
        image_file = request.files["image"]
        if image_file.filename != "":
            try:
                image_bytes_psoriasis = image_file.read()
                imagen_base64 = base64.b64encode(image_bytes_psoriasis).decode("utf-8")
            except Exception as e:
                return jsonify({"error": f"Error al procesar la imagen: {e}"}), 500

    try:
        # Usar el texto de voz como texto normalizado
        texto_normalizado = voice_text

        # Pasar el texto normalizado a consultar_modelo
        respuesta_md = consultar_modelo(
            texto_normalizado,
            language,
            imagen_base64,
            advanced_instructions=advanced_instructions,
            pathology=pathology,
        )

        # Incrementar el contador de consultas realizadas
        consultas_realizadas += 1
        actualizar_consultas(user_id, consultas_realizadas)

        # Convertir la respuesta a HTML y retornarla
        respuesta_html = markdown.markdown(respuesta_md)
        return jsonify({"message": respuesta_html}), 200

    except Exception as e:
        return jsonify({"error": f"Error al procesar la entrada de voz: {e}"}), 500


@app.route("/upload_scanned_file", methods=["POST"])
def upload_scanned_file():
    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"error": "ID de usuario no proporcionado"}), 400

    # Verificar si el ID es válido
    if user_id not in dermatologos:
        return jsonify({"error": "ID no válido"}), 403

    # Obtener el límite de consultas y las consultas realizadas
    limite_consultas = dermatologos[user_id]
    consultas_realizadas = leer_consultas(user_id)

    # Verificar si ha alcanzado el límite de consultas
    if consultas_realizadas >= limite_consultas:
        return jsonify({"error": "Has alcanzado el límite de consultas gratuitas"}), 403

    if "scanned_file" not in request.files:
        return jsonify({"error": "No se ha proporcionado un archivo"}), 400

    scanned_file = request.files["scanned_file"]

    if scanned_file.filename == "":
        return jsonify({"error": "Ningún archivo seleccionado"}), 400

    language = request.form.get("language", "ES")

    advanced_instructions = request.form.get("advanced_instructions", "")

    pathology = request.form.get("pathology", "psoriasis")

    # Verificar si se ha subido una imagen de la psoriasis
    imagen_base64 = None
    if "image" in request.files:
        image_file = request.files["image"]
        if image_file.filename != "":
            try:
                image_bytes_psoriasis = image_file.read()
                imagen_base64 = base64.b64encode(image_bytes_psoriasis).decode("utf-8")
            except Exception as e:
                return jsonify({"error": f"Error al procesar la imagen: {e}"}), 500

    try:
        # Convertir el PDF escaneado en imágenes
        images = extraer_imagen_de_pdf(scanned_file)
        # Tomar la primera imagen (o puedes iterar si lo prefieres)
        image_bytes = convert_image_to_bytes(images[0])

        # Extraer el texto utilizando consultar_modelo_multimodal
        texto_extraido = consultar_modelo_multimodal(
            image_bytes,
            prompt="Extrae los datos del paciente de este informe escaneado.",
        )

        # Normalizar el texto extraído
        texto_query = texto_extraido

        # Pasar el texto normalizado a consultar_modelo
        respuesta_md = consultar_modelo(
            texto_query,
            language,
            imagen_base64,
            advanced_instructions=advanced_instructions,
            pathology=pathology,
        )

        # Incrementar el contador de consultas realizadas
        consultas_realizadas += 1
        actualizar_consultas(user_id, consultas_realizadas)

        # Convertir la respuesta a HTML y retornarla
        respuesta_html = markdown.markdown(respuesta_md)
        return jsonify({"message": respuesta_html}), 200

    except Exception as e:
        return jsonify({"error": f"Error al procesar el archivo escaneado: {e}"}), 500


@app.route("/upload_photo", methods=["POST"])
def upload_photo():

    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"error": "ID de usuario no proporcionado"}), 400

    # Verificar si el ID es válido
    if user_id not in dermatologos:
        return jsonify({"error": "ID no válido"}), 403

    # Obtener el límite de consultas y las consultas realizadas
    limite_consultas = dermatologos[user_id]
    consultas_realizadas = leer_consultas(user_id)

    # Verificar si ha alcanzado el límite de consultas
    if consultas_realizadas >= limite_consultas:
        return jsonify({"error": "Has alcanzado el límite de consultas gratuitas"}), 403

    if "patient_photo" not in request.files:
        return jsonify({"error": "No se ha proporcionado una imagen"}), 400

    patient_photo = request.files["patient_photo"]

    if patient_photo.filename == "":
        return jsonify({"error": "Ninguna imagen seleccionada"}), 400

    language = request.form.get("language", "ES")

    advanced_instructions = request.form.get("advanced_instructions", "")

    pathology = request.form.get("pathology", "psoriasis")

    # Verificar si se ha subido una imagen de la psoriasis
    imagen_base64 = None
    if "image" in request.files:
        image_file = request.files["image"]
        if image_file.filename != "":
            try:
                image_bytes_psoriasis = image_file.read()
                imagen_base64 = base64.b64encode(image_bytes_psoriasis).decode("utf-8")
            except Exception as e:
                return jsonify({"error": f"Error al procesar la imagen: {e}"}), 500

    try:
        # Leer los bytes de la imagen
        image_bytes = patient_photo.read()

        # Extraer el texto utilizando consultar_modelo_multimodal
        texto_extraido = consultar_modelo_multimodal(
            image_bytes, prompt="Extrae los datos del paciente de esta imagen."
        )

        # Normalizar el texto extraído
        texto_query = texto_extraido

        # Pasar el texto normalizado a consultar_modelo
        respuesta_md = consultar_modelo(
            texto_query,
            language,
            imagen_base64,
            advanced_instructions=advanced_instructions,
            pathology=pathology,
        )

        # Incrementar el contador de consultas realizadas
        consultas_realizadas += 1
        actualizar_consultas(user_id, consultas_realizadas)

        # Convertir la respuesta a HTML y retornarla
        respuesta_html = markdown.markdown(respuesta_md)
        return jsonify({"message": respuesta_html}), 200

    except Exception as e:
        return jsonify({"error": f"Error al procesar la foto: {e}"}), 500


@app.route("/", methods=["GET"])
def form():
    user_id = request.args.get("id")  # Capturar el parámetro 'id'

    if not user_id:
        return "ID no proporcionado", 400  # Si no hay 'id', denegar acceso

    # Verificar si el ID está en el diccionario
    if user_id not in dermatologos:
        return "ID no válido", 403

    # Obtener el límite de consultas del diccionario
    limite_consultas = dermatologos[user_id]

    # Leer el número de consultas ya realizadas del archivo de texto
    consultas_realizadas = leer_consultas(user_id)

    # Comprobar si ha llegado al límite de consultas
    if consultas_realizadas >= limite_consultas:
        return "Has alcanzado el límite de consultas gratuitas", 403

    # Al cargar por primera vez, se pasa una 'respuesta' vacía.
    return render_template_string(HTML_TEMPLATE, respuesta=None, user_id=user_id)


@app.route("/upload", methods=["POST"])
def upload_file():

    try:

        user_id = request.form.get("user_id")
        if not user_id:
            return jsonify({"error": "ID de usuario no proporcionado"}), 400

        # Verificar si el ID es válido
        if user_id not in dermatologos:
            return jsonify({"error": "ID no válido"}), 403

        # Obtener el límite de consultas del diccionario
        limite_consultas = dermatologos[user_id]

        # Leer el número de consultas ya realizadas
        consultas_realizadas = leer_consultas(user_id)

        # Verificar si ha alcanzado el límite de consultas
        if consultas_realizadas >= limite_consultas:
            return (
                jsonify({"error": "Has alcanzado el límite de consultas gratuitas"}),
                403,
            )

        # session.permanent = True
        if "patient_file" not in request.files and "patient_age" not in request.form:
            return "Archivo o datos no encontrados", 400

        language = request.form["language"]
        # Capturar las instrucciones avanzadas del formulario
        advanced_instructions = request.form.get("advanced_instructions", "")
        pathology = request.form.get("pathology", "psoriasis")
        is_ajax = request.form.get("ajax", "false") == "true"

        # Verificar si se seleccionó un documento personalizado
        custom_document = None
        custom_filename = None
        if "custom_document" in request.files:
            custom_document = request.files["custom_document"]
            filename = secure_filename(custom_document.filename)
            print(f"El nombre del archivo es: {filename}")
            file_extension = os.path.splitext(filename)[1].lower()

            # Guardar temporalmente el archivo subido
            temp_path = os.path.join("/tmp", filename)
            custom_document.save(temp_path)

            # Extraer texto del documento personalizado
            if file_extension == ".docx":
                texto_documento = extraer_texto_de_docx(temp_path)
            elif file_extension == ".pdf":
                texto_documento = extraer_texto_de_pdf(temp_path)
            else:
                return "Formato de archivo no soportado", 400

            # Procesar el documento: normalizar, dividir, generar embeddings e indexar en Pinecone

            segmentos = dividir_en_segmentos(
                texto_documento, chunk_size=1000, chunk_overlap=100
            )
            embeddings_segmentos = generar_embeddings(segmentos)

            # Crear vectores con metadatos, incluyendo el nombre del archivo
            vectors = []
            for i, (embedding, segmento) in enumerate(
                zip(embeddings_segmentos, segmentos)
            ):
                vector_id = f"{filename}_{i}"
                metadata = {"texto": segmento, "filename": filename}
                vectors.append((vector_id, embedding, metadata))

            # Indexar en Pinecone
            index.upsert(vectors=vectors)

            # Eliminar el archivo temporal
            os.remove(temp_path)

            # Asignar el nombre de archivo a custom_filename
            custom_filename = filename

        if "patient_file" in request.files:
            file = request.files["patient_file"]
            if file.filename == "":
                return "Ningún archivo seleccionado", 400
            texto_pdf = ""
            try:
                # Procesar el archivo PDF subido
                doc = fitz.open(stream=file.read(), filetype="pdf")
                for pagina in doc:
                    texto_pdf += pagina.get_text()
                texto_normalizado = texto_pdf
            except Exception as e:
                return f"Error al procesar el archivo: {e}"
        else:
            # Recopilar y normalizar los datos del formulario
            texto_normalizado = " ".join(
                [
                    request.form.get("patient_age", ""),
                    request.form.get("patient_sex", ""),
                    request.form.get("patient_height", ""),
                    request.form.get("patient_weight", ""),
                    request.form.get("medication_allergies", ""),
                    request.form.get("cv_risk_factors", ""),
                    request.form.get("comorbidities", ""),
                    request.form.get("neoplasia_history", ""),
                    request.form.get("infections_history", ""),
                    request.form.get("tb_history", ""),
                    request.form.get("personal_history", ""),
                    request.form.get("family_history", ""),
                    request.form.get("vaccination_status", ""),
                    request.form.get("mantoux_qtf", ""),
                    request.form.get("prophylaxis", ""),
                    request.form.get("treatment", ""),
                    request.form.get("vaccination_schedule", ""),
                    request.form.get("fertility_history", ""),
                    request.form.get("gestational_desire", ""),
                    request.form.get("current_pregnancy", ""),
                    request.form.get("medication", ""),
                    request.form.get("psoriasis_type", ""),
                    request.form.get("lesion_location", ""),
                    request.form.get("joint_involvement", ""),
                    request.form.get("pasi_severity", ""),
                    request.form.get("bsa_extent", ""),
                    request.form.get("previous_treatments", ""),
                    request.form.get("phototherapy", ""),
                    request.form.get("classic_systemics", ""),
                    request.form.get("anti_tnf", ""),
                    request.form.get("biologics", ""),
                    request.form.get("biomarker_levels", ""),
                    request.form.get("imaging_results", ""),
                    request.form.get("algorithm_considerations", ""),
                ]
            )

        # Verificar si se ha subido una imagen
        imagen_base64 = None
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file.filename != "":
                try:
                    # Convertir la imagen a base64
                    image_bytes = BytesIO(image_file.read())
                    imagen_base64 = base64.b64encode(image_bytes.getvalue()).decode(
                        "utf-8"
                    )
                except Exception as e:
                    return f"Error al procesar la imagen: {e}"

        form_path = f"/home/IAenPsoriasis/mysite/static/{user_id}_form.txt"
        with open(form_path, "w", encoding="utf-8") as f:
            f.write(texto_normalizado)

        respuesta_md, justificacion = consultar_modelo(
            texto_normalizado,
            language,
            imagen_base64,
            custom_filename=custom_filename,
            advanced_instructions=advanced_instructions,
            pathology=pathology,
        )

        respuesta_combinada = f"{respuesta_md}\n\n{justificacion}"

        # Incrementar el contador de consultas realizadas
        consultas_realizadas += 1
        actualizar_consultas(user_id, consultas_realizadas)

        respuesta_html = markdown.markdown(respuesta_combinada)

        trat_path = f"/home/IAenPsoriasis/mysite/static/{user_id}_tratamiento.txt"
        with open(trat_path, "w", encoding="utf-8") as f:
            f.write(respuesta_html)

        session["respuesta_html"] = respuesta_html  # Guardar respuesta en sesión
        print("Respuesta guardada en la sesión:", session["respuesta_html"])

        txt_formulario_url = (
            f"https://iaenpsoriasis.pythonanywhere.com/static/{user_id}_form.txt"
        )
        txt_tratamiento_url = (
            f"https://iaenpsoriasis.pythonanywhere.com/static/{user_id}_tratamiento.txt"
        )

        if is_ajax:
            return respuesta_html  # Devuelve solo la respuesta HTML para AJAX
        else:
            return render_template_string(
                HTML_TEMPLATE,
                respuesta=respuesta_html,
                txt_formulario_url=txt_formulario_url,
                txt_tratamiento_url=txt_tratamiento_url,
            )

    except Exception as e:
        # Registrar el error para depuración
        print(f"Error en la ruta /upload: {e}")
        # Retornar una respuesta JSON con el error
        return jsonify({"error": str(e)}), 500


@app.route("/download-response", methods=["POST"])
def download_response():
    try:
        data = request.get_json()
        html_content = data.get("response_content")
        if not html_content:
            return "No hay contenido de respuesta para descargar", 400

        pdf = HTML(string=html_content).write_pdf()

        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            'attachment; filename="tratamiento_psoriasis.pdf"'
        )
        return response
    except Exception as e:
        return f"Error al generar el PDF: {e}", 500


def normalizar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"[^\w\s]", "", texto)
    return texto


def justificacion_tratamiento(tratamiento, fragmentos_recuperados):

    system_prompt = {
        "role": "system",
        "content": """
            Eres un agente inteligente especializado en justificar con que secciones de fragmentos pertenecientes a un protocolo de psoriasis se ha generado un tratamiento.
            Recibirás el tratamiento generado y los fragmentos del protocolo que han servido como fuente de información para generarlo.
            Tu misión es analizar tanto el tratamiento como los fragmentos para identificar que secciones (oraciones, frases, párrafos) se han utilizado para generar el tratamiento.
            Presenta el resultado de manera concisa y profesional. Puedes citar coincidencias exactas.
            Ten en cuenta que esto lo leerá un dermatólogo para determinar si el tratamiento generado es correcto.
            Si lo haces bien serás recompensado.
            """,
    }

    user_prompt = {
        "role": "user",
        "content": f"""
            El tratamiento generado es: {tratamiento}
            Los fragmentos utilizados como fuente de información para generar el tratamiento son: {fragmentos_recuperados}.
            """,
    }

    # Generar la recomendación de tratamiento con OpenAI GPT
    response_gpt = openai.ChatCompletion.create(
        model="chatgpt-4o-latest", messages=[system_prompt, user_prompt]
    )

    # Devolver la respuesta generada por el modelo
    return response_gpt.choices[0].message["content"]


def consultar_modelo(
    texto_normalizado,
    language,
    imagen_base64=None,
    custom_filename=None,
    advanced_instructions="",
    pathology="psoriasis",
):

    # Crear el embedding del texto normalizado
    response_embedding = openai.Embedding.create(
        input=texto_normalizado,
        model="text-embedding-3-large",  # Asegúrate de usar el modelo correcto según tu necesidad
    )
    embedding_vector = response_embedding["data"][0]["embedding"]

    # Configurar filtros para la consulta en Pinecone
    filter_conditions = {}

    print(f"El nombre del metadato del archivo a buscar es: {custom_filename}")
    if custom_filename:
        filter_conditions = {"filename": {"$eq": custom_filename}}

    else:
        if pathology == "psoriasis":
            # Si la patología es 'psoriasis', buscamos vectores que solo tengan el metadato 'texto'
            filter_conditions = {
                "$and": [
                    {"texto": {"$exists": True}},  # El metadato 'texto' debe existir
                    {
                        "fuente": {"$exists": False}
                    },  # El metadato 'fuente' no debe existir
                ]
            }
        else:
            # Si la patología es diferente de 'psoriasis', buscamos vectores que tengan tanto 'texto' como 'fuente'
            filter_conditions = {
                "$and": [
                    {"texto": {"$exists": True}},  # El metadato 'texto' debe existir
                    {
                        "fuente": {"$exists": True}
                    },  # El metadato 'fuente' también debe existir
                ]
            }

    # Consultar el índice de Pinecone para obtener los documentos relevantes
    resultados = index.query(
        vector=embedding_vector,
        top_k=20,
        include_values=True,
        include_metadata=True,
        filter=filter_conditions,
    )
    # Extraer IDs y textos similares de los resultados
    textos_similares = [res["metadata"]["texto"] for res in resultados["matches"]]

    # Concatenar los textos de los resultados para crear el contexto
    texto_concatenado = " ".join(textos_similares)

    print(f"La fuente para determinar el tratamiento es: {texto_concatenado}")

    # Definir el contexto y las instrucciones para el prompt de GPT
    contexto = (
        f"El paciente tiene las siguientes condiciones: {texto_normalizado}. "
        f"La información que debes usar, es decir, la fuente que usarás para determinar el mejor fármaco para la {pathology} es: {texto_concatenado}."
    )
    instrucciones = (
        f"Dadas estas condiciones, ¿cuál sería el fármaco recomendado para la {pathology} del paciente? "
        "Dime también la dosis, frecuencia y duración del tratamiento."
    )

    if language == "ES":
        instrucciones += " Genera la respuesta en español."
    elif language == "EN":
        instrucciones += " Genera la respuesta en inglés."
    elif language == "FR":
        instrucciones += " Genera la respuesta en francés."

    # Verificar si se ha proporcionado una imagen en base64
    if imagen_base64:
        print("Imagen recibida en base64. Longitud del string:", len(imagen_base64))
        # Incluir tanto el contexto textual como la imagen en formato data:image/jpeg;base64
        image_content = {
            "role": "user",
            "content": [
                {"type": "text", "text": contexto + " " + instrucciones},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{imagen_base64}"},
                },
            ],
        }
    else:
        print("No se ha recibido ninguna imagen.")
        # Si no hay imagen, solo enviar el contexto textual
        image_content = {"role": "user", "content": contexto + " " + instrucciones}

    if pathology == "psoriasis":
        # Construir el contexto basado en si el usuario proporcionó un documento personalizado
        if custom_filename:
            fuente_instruccion = f"Siempre debes nombrar la fuente. Al nombrarla, menciona el documento proporcionado por el usuario llamado '{custom_filename}'. No menciones más fuentes que esa."
        else:
            fuente_instruccion = "Siempre debes nombrar la fuente. Al nombrarla, menciona el Protocolo de Psoriasis de SESCAM. No menciones más fuentes que esa."
    else:
        # Construir el contexto basado en si el usuario proporcionó un documento personalizado
        if custom_filename:
            fuente_instruccion = f"Siempre debes nombrar la fuente. Al nombrarla, menciona el documento proporcionado por el usuario llamado '{custom_filename}'. No menciones más fuentes que esa."
        else:
            fuente_instruccion = "Siempre debes nombrar la fuente. Al nombrarla, menciona que los datos los obtenemos de nuestra base de datos vectorial de dermatología. No menciones más fuentes que esa."

    print(f"Las instrucciones avanzadas son: {advanced_instructions}")

    if pathology == "psoriasis":
        system_prompt = {
            "role": "system",
            "content": f"""
            Eres un dermatólogo experto con muchos años de experiencia. No hables en primera persona.
            Por favor, proporciona una recomendación de tratamiento detallada para un paciente con psoriasis, basándote en su historial médico, características clínicas y experiencias previas de tratamiento. Asegúrate de incluir:

            Fármaco recomendado: Elige uno de los siguientes fármacos disponibles:

            Betabloqueantes
            Litio
            Antipalúdicos
            Inhibidores de los puntos de control
            Anti-TNF
            Metotrexato
            Adalimumab
            Ciclosporina
            Acitretino
            Dimetilfumarato
            Infliximab
            Etanercept
            Certolizumab
            Brodalumab
            Secukinumab
            Ixekizumab
            Ustekinumab
            Risankizumab
            Guselkumab
            Bimekizumab
            Tildrakizumab
            Tazaroteno
            Calcipotriol
            Calcitriol
            Tacrolimus
            Pimecrolimus
            Psoraleno
            Nota: No tengas tendencia a recomendar el fármaco Cosentyx (secukinumab). Si lo haces, asegúrate de que es el indicado y justifícalo adecuadamente.

            Dosis: Especifica la dosis adecuada del fármaco seleccionado.

            Consideraciones especiales: Incluye cualquier consideración especial relevante.

            Además, añade los siguientes apartados:

            Justificación de la elección del fármaco: Explica por qué has seleccionado ese fármaco en particular.
            Previsión de evolución: Describe cómo debería evolucionar la psoriasis del paciente en función del tratamiento propuesto.
            Instrucciones de administración: Proporciona instrucciones detalladas sobre cómo administrar el fármaco recomendado.
            Efectos secundarios: Informa sobre los efectos secundarios más comunes del fármaco y cómo manejarlos.
            Análisis de imagen (si aplica): Si recibes una imagen de la psoriasis del paciente, tenla en cuenta al determinar el tratamiento e incluye un apartado analizándola y describiéndola. Si no recibes ninguna imagen, ignora este apartado.
            {fuente_instruccion}

            Aquí tienes las instrucciones avanzadas que ha añadido el dermátologo, aplícalas a la hora de generar el tratamiento:
            {advanced_instructions}

            Puedes usar formato Markdown para mostrar un estilo más visual y puedes resaltar con negrita lo que consideres importante.

            Los fragmentos que debes usar como fuente de datos para generar el tratamiento son: {texto_concatenado}. Tu misión es incluir las partes clave que hayas utilizado como citas textuales.

            Por favor, NO enumeres los apartados.

            Si lo haces bien te recompensaré.
            """,
        }

    else:

        system_prompt = {
            "role": "system",
            "content": f"""
            Eres un dermatólogo experto con muchos años de experiencia. No hables en primera persona.
            Por favor, proporciona una recomendación de tratamiento detallada para un paciente con {pathology}, basándote en su historial médico, características clínicas y experiencias previas de tratamiento. Asegúrate de incluir:

            Fármaco recomendado: Elige el fármaco que creas conveniente en base a la información que tienes.

            Dosis: Especifica la dosis adecuada del fármaco seleccionado.

            Consideraciones especiales: Incluye cualquier consideración especial relevante.

            Además, añade los siguientes apartados:

            Justificación de la elección del fármaco: Explica por qué has seleccionado ese fármaco en particular.
            Previsión de evolución: Describe cómo debería evolucionar la {pathology} del paciente en función del tratamiento propuesto.
            Instrucciones de administración: Proporciona instrucciones detalladas sobre cómo administrar el fármaco recomendado.
            Efectos secundarios: Informa sobre los efectos secundarios más comunes del fármaco y cómo manejarlos.
            Análisis de imagen (si aplica): Si recibes una imagen de la {pathology} del paciente, tenla en cuenta al determinar el tratamiento e incluye un apartado analizándola y describiéndola. Si no recibes ninguna imagen, ignora este apartado.
            {fuente_instruccion}

            Aquí tienes las instrucciones avanzadas que ha añadido el dermátologo, aplícalas a la hora de generar el tratamiento:
            {advanced_instructions}

            Puedes usar formato Markdown para mostrar un estilo más visual y puedes resaltar con negrita lo que consideres importante.

            Por favor, NO enumeres los apartados.

            Si lo haces bien te recompensaré.
            """,
        }

    # Generar la recomendación de tratamiento con OpenAI GPT
    response_gpt = openai.ChatCompletion.create(
        model="chatgpt-4o-latest", messages=[system_prompt, image_content]
    )

    tratamiento = response_gpt.choices[0].message["content"]
    justificacion = justificacion_tratamiento(tratamiento, texto_concatenado)

    # Devolver la respuesta generada por el modelo
    return tratamiento, justificacion


def send_email(email, response_content):
    # Configuración del correo
    sender_email = "apmdermatologia@gmail.com"
    sender_password = "jzxn fhlr cagp lgob"
    subject = "Resultados Tratamiento Dermatología mediante IA"
    body = """
    Hola! Muchas gracias por usar la herramienta APM Dermatología.
    Te adjuntamos el tratamiento generado ajustado a las condiciones del paciente.
    ¡Espero que te sirva de ayuda!
    """

    # Crear el contenido del correo
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Adjuntar el tratamiento en PDF
    pdf = HTML(string=response_content).write_pdf()
    pdf_attachment = MIMEApplication(pdf, _subtype="pdf")
    pdf_attachment.add_header(
        "Content-Disposition", "attachment", filename="tratamiento_apm_dermatologia.pdf"
    )
    msg.attach(pdf_attachment)

    # Enviar el correo
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)  # Usa el servidor SMTP adecuado
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        return (
            "Correo enviado correctamente. En unos segundos recibirá el correo con los resultados.",
            200,
        )
    except Exception as e:
        return f"Error al enviar el correo: {e}", 500


@app.route("/send_email", methods=["POST"])
def send_email_route():
    try:
        data = request.get_json()  # Asegúrate de obtener el JSON correctamente
        email = data.get("email")
        response_content = data.get("response-content")
        if not email:
            return jsonify({"message": "Debe introducir un correo"}), 400
        if not response_content:
            return (
                jsonify({"message": "No hay contenido de respuesta para enviar"}),
                400,
            )
        response, status = send_email(email, response_content)
        return jsonify({"message": response}), status
    except Exception as e:
        return jsonify({"message": f"Error al procesar la solicitud: {e}"}), 500


@app.route("/download-form", methods=["GET"])
def download_form():
    return send_from_directory(
        ".", "formulario_tipo_psoriasis.docx", as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True, port=5003)

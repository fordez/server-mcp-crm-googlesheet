# AgeStudio MCP Server

Servidor MCP (Model Context Protocol) para gestión de nombres de clientes y preguntas de calificación usando Google Sheets como base de datos.

## 📁 Estructura del Proyecto

```
agestudio-mcp/
├── mcp.py                    # Servidor MCP principal
├── .env                      # Variables de entorno
├── requirements.txt          # Dependencias de Python
├── credentials.json         # Credenciales de Google (no incluir en git)
├── tools/
│   ├── __init__.py
│   └── sheet_operations.py  # Funciones de Google Sheets
└── README.md
```

## 🚀 Instalación

### 1. Clonar o crear el proyecto

```bash
mkdir agestudio-mcp
cd agestudio-mcp
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Google Sheets API

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Sheets:
   - Ve a "APIs y servicios" > "Biblioteca"
   - Busca "Google Sheets API"
   - Haz clic en "Habilitar"

4. Crear credenciales de cuenta de servicio:
   - Ve a "APIs y servicios" > "Credenciales"
   - Clic en "Crear credenciales" > "Cuenta de servicio"
   - Completa el formulario y crea la cuenta
   - En la cuenta creada, ve a "Claves"
   - Clic en "Agregar clave" > "Crear clave nueva"
   - Selecciona formato JSON
   - Guarda el archivo como `credentials.json` en la raíz del proyecto

5. Compartir tu Google Sheet:
   - Abre tu hoja de cálculo en Google Sheets
   - Copia el email de la cuenta de servicio (está en el archivo credentials.json)
   - Comparte la hoja con ese email dándole permisos de edición

### 5. Configurar variables de entorno

Edita el archivo `.env` con tus valores:

```bash
SPREADSHEET_ID=tu_id_de_spreadsheet_aqui
GOOGLE_CREDENTIALS_FILE=credentials.json
NAMES_SHEET=Nombres
QUALIFICATIONS_SHEET=Calificaciones
```

**Para obtener el SPREADSHEET_ID:**
- Abre tu Google Sheet
- Mira la URL: `https://docs.google.com/spreadsheets/d/AQUI_ESTA_EL_ID/edit`
- Copia el ID que está entre `/d/` y `/edit`

### 6. Crear el directorio tools

```bash
mkdir tools
touch tools/__init__.py
```

## 🎯 Uso

### Iniciar el servidor

```bash
python mcp.py
```

### Tools disponibles

#### 1. `update_client_name`
Actualiza o agrega un nombre de cliente en Google Sheets.

**Parámetros:**
- `name` (str, opcional): Nombre completo del cliente
- `row` (int, opcional): Número de fila donde actualizar

**Ejemplo de uso:**
```python
# Si no proporcionas el nombre, el sistema lo solicitará
update_client_name()

# Agregar un nuevo nombre
update_client_name(name="Juan Pérez García")

# Actualizar nombre en fila específica
update_client_name(name="María González", row=5)
```

#### 2. `save_qualification`
Guarda preguntas de calificación del cliente.

**Parámetros:**
- `questions` (list[dict]): Lista de preguntas con sus respuestas
- `client_name` (str, opcional): Nombre del cliente

**Ejemplo de uso:**
```python
questions = [
    {
        "question": "¿Cuál es su nivel de satisfacción?",
        "answer": "Muy satisfecho",
        "score": 5
    },
    {
        "question": "¿Recomendaría nuestros servicios?",
        "answer": "Definitivamente sí",
        "score": 5
    }
]

save_qualification(questions=questions, client_name="Juan Pérez")
```

## 📊 Estructura de Google Sheets

El sistema crea automáticamente dos hojas:

### Hoja "Nombres"
```
| Columna A    |
|--------------|
| Juan Pérez   |
| María López  |
| Carlos Ruiz  |
```

### Hoja "Calificaciones"
```
| Fecha       | Cliente    | Pregunta              | Respuesta       | Puntaje |
|-------------|------------|-----------------------|-----------------|---------|
| 2025-10-23  | Juan Pérez | ¿Nivel satisfacción? | Muy satisfecho  | 5       |
```

## 🔧 Recursos y Prompts

### Recursos
- `sheets://main`: Información sobre la hoja de cálculo

### Prompts
- `ask_for_name()`: Template para solicitar nombres
- `qualification_questions_template()`: Template para preguntas de calificación

## ⚠️ Notas Importantes

1. **Seguridad:**
   - Nunca subas `credentials.json` a git
   - Añade este archivo a `.gitignore`

2. **Permisos:**
   - La cuenta de servicio debe tener acceso de edición a la hoja

3. **Límites de API:**
   - Google Sheets API tiene límites de uso
   - Para producción, considera implementar rate limiting

## 📝 Archivo .gitignore recomendado

```
# Credenciales
credentials.json
*.json

# Entorno virtual
venv/
env/

# Variables de entorno
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# IDE
.vscode/
.idea/
```

## 🆘 Solución de Problemas

### Error: "File not found: credentials.json"
- Verifica que el archivo credentials.json esté en la raíz del proyecto
- Revisa que la ruta en .env sea correcta

### Error: "The caller does not have permission"
- Comparte la hoja de Google con el email de la cuenta de servicio
- Verifica que tenga permisos de edición

### Error: "Spreadsheet not found"
- Verifica que el SPREADSHEET_ID en .env sea correcto
- Asegúrate de copiar el ID completo de la URL

## 📞 Soporte

Para más información sobre FastMCP: [https://github.com/jlowin/fastmcp](https://github.com/jlowin/fastmcp)

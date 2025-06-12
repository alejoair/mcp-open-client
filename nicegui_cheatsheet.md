### **Componentes de datos y estructura**

#### **ui.tree()**
Árbol jerárquico
```python
# Árbol básico
tree = ui.tree([
    {
        'id': 'raiz',
        'label': 'Carpeta Principal',
        'children': [
            {'id': 'doc1', 'label': 'Documento 1.pdf'},
            {'id': 'doc2', 'label': 'Documento 2.txt'},
            {
                'id': 'subcarpeta',
                'label': 'Subcarpeta',
                'children': [
                    {'id': 'subdoc1', 'label': 'Archivo.xlsx'},
                    {'id': 'subdoc2', 'label': 'Imagen.jpg'}
                ]
            }
        ]
    },
    {
        'id': 'otra_carpeta',
        'label': 'Otra Carpeta',
        'children': [
            {'id': 'archivo3', 'label': 'Script.py'}
        ]
    }
], 
label_key='label',
on_select=lambda e: ui.notify(f'Seleccionado: {e.value}'),
on_expand=lambda e: ui.notify(f'Expandido: {e.value}'))

# Árbol con checkboxes
tree_check = ui.tree([
    {'id': 'tarea1', 'label': 'Completar proyecto', 'children': [
        {'id': 'subtarea1', 'label': 'Diseño'},
        {'id': 'subtarea2', 'label': 'Desarrollo'},
        {'id': 'subtarea3', 'label': 'Testing'}
    ]},
    {'id': 'tarea2', 'label': 'Documentación'}
], 
label_key='label',
tick_strategy='leaf',  # Permite checkboxes
on_tick=lambda e: ui.notify(f'Marcado: {e.value}'))
```

#### **ui.log()**
Visor de logs en tiempo real
```python
from datetime import datetime

# Log básico
log = ui.log(max_lines=20).classes('w-full h-32 border')

def agregar_log():
    timestamp = datetime.now().strftime('%H:%M:%S')
    log.push(f'[{timestamp}] Nueva entrada de log')

ui.button('Agregar log', on_click=agregar_log)

# Log con diferentes tipos
log_sistema = ui.log().classes('w-full h-40 font-mono')

def log_info():
    log_sistema.push(f'[INFO] {datetime.now()} - Operación completada')

def log_warning():
    log_sistema.push(f'[WARNING] {datetime.now()} - Advertencia del sistema')

def log_error():
    log_sistema.push(f'[ERROR] {datetime.now()} - Error crítico detectado')

with ui.row():
    ui.button('Info', on_click=log_info).props('color=blue')
    ui.button('Warning', on_click=log_warning).props('color=orange')
    ui.button('Error', on_click=log_error).props('color=red')
```

#### **ui.editor()**
Editor WYSIWYG
```python
# Editor rich text
editor = ui.editor(
    placeholder='Escribe tu contenido aquí...',
    value='<h3>Título inicial</h3><p>Contenido con <strong>texto en negrita</strong></p>'
)

# Mostrar HTML generado
ui.markdown().bind_content_from(
    editor, 'value',
    backward=lambda v: f'**HTML generado:**\n```html\n{v}\n```'
)

# Editor con configuración personalizada
editor_avanzado = ui.editor().props('''
    :toolbar="[
        ['bold', 'italic', 'underline'],
        ['quote', 'unordered', 'ordered'],
        ['link', 'custom_btn'],
        ['print', 'fullscreen']
    ]"
''')
```

#### **ui.code()**
Visor de código con sintaxis
```python
# Código Python
ui.code('''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Ejemplo de uso
print(fibonacci(10))
''', language='python').classes('w-full')

# Código JavaScript
ui.code('''
const datos = [1, 2, 3, 4, 5];
const cuadrados = datos.map(x => x * x);
console.log(cuadrados);
''', language='javascript')

# Código SQL
ui.code('''
SELECT usuarios.nombre, COUNT(pedidos.id) as total_pedidos
FROM usuarios
LEFT JOIN pedidos ON usuarios.id = pedidos.usuario_id
GROUP BY usuarios.id, usuarios.nombre
HAVING COUNT(pedidos.id) > 5
ORDER BY total_pedidos DESC;
''', language='sql')
```

#### **ui.json_editor()**
Editor JSON interactivo
```python
# Datos de ejemplo
datos_json = {
    'usuario': {
        'id': 123,
        'nombre': 'Juan Pérez',
        'email': 'juan@ejemplo.com',
        'activo': True,
        'roles': ['usuario', 'editor'],
        'configuracion': {
            'tema': 'oscuro',
            'idioma': 'es',
            'notificaciones': True
        }
    },
    'metadata': {
        'creado': '2024-01-15T10:30:00Z',
        'version': '1.0.0'
    }
}

# Schema de validación (opcional)
schema = {
    'type': 'object',
    'properties': {
        'usuario': {
            'type': 'object',
            'properties': {
                'id': {'type': 'number'},
                'nombre': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'activo': {'type': 'boolean'}
            },
            'required': ['id', 'nombre', 'email']
        }
    }
}

# Editor JSON
json_editor = ui.json_editor(
    {'content': {'json': datos_json}},
    schema=schema,
    on_select=lambda e: ui.notify(f'Seleccionado: {e}'),
    on_change=lambda e: ui.notify(f'Cambiado: {e}')
).classes('w-full h-96')

# Botón para obtener datos
def obtener_datos():
    datos = json_editor.properties['content']['json']
    ui.notify(f'Datos actuales: {datos}')

ui.button('Obtener datos JSON', on_click=obtener_datos)
```

# NiceGUI Components Cheatsheet 🚀

*Una guía rápida de referencia para los componentes de NiceGUI*

---

## 📋 Instalación y Configuración Básica

```python
# Instalación
pip install nicegui

# Importación básica
from nicegui import ui

# Estructura básica de una aplicación
from nicegui import ui

ui.label('¡Hola NiceGUI!')
ui.run()  # Ejecuta la aplicación en localhost:8080
```

---

## 🎨 Componentes de Texto

### **ui.label()**
Muestra texto estático
```python
ui.label('Texto simple')
ui.label('Texto con **markdown**')
ui.label('Texto con color').style('color: red')
```

### **ui.markdown()**
Renderiza contenido Markdown
```python
ui.markdown('# Título H1')
ui.markdown('## Título H2')
ui.markdown('**Texto en negrita** e _italica_')
ui.markdown('- Lista\n- De elementos')
```

### **ui.html()**
Contenido HTML directo
```python
ui.html('<h3>Título HTML</h3>')
ui.html('<div style="color: blue;">Contenido HTML</div>')
```

---

## 🎛️ Componentes de Control

### **ui.button()**
Botón interactivo
```python
# Botón básico
ui.button('Clic aquí', on_click=lambda: ui.notify('¡Botón presionado!'))

# Botón con icono
ui.button('Guardar', icon='save', on_click=save_function)

# Botón con estilo
ui.button('Primario').props('color=primary')
ui.button('Secundario').props('color=secondary')
```

### **ui.input()**
Campo de entrada de texto
```python
# Input básico
nombre = ui.input('Nombre')

# Input con placeholder y validación
email = ui.input('Email', placeholder='usuario@ejemplo.com')

# Input de contraseña
password = ui.input('Contraseña', password=True)

# Input numérico
edad = ui.input('Edad', value=25).props('type=number')
```

### **ui.textarea()**
Área de texto multilínea
```python
comentario = ui.textarea('Comentarios', 
                        placeholder='Escribe tu comentario...')
comentario.props('rows=4')
```

### **ui.checkbox()**
Casilla de verificación
```python
# Checkbox básico
acepto = ui.checkbox('Acepto los términos')

# Checkbox con valor inicial
activo = ui.checkbox('Activo', value=True)
```

### **ui.switch()**
Interruptor on/off
```python
# Switch básico
notificaciones = ui.switch('Notificaciones')

# Switch con valor inicial
modo_oscuro = ui.switch('Modo oscuro', value=False)
```

### **ui.radio()**
Botones de radio (selección única)
```python
with ui.radio(['Opción 1', 'Opción 2', 'Opción 3'], value='Opción 1') as radio:
    pass

# Radio con diccionario
opciones = {'s': 'Pequeño', 'm': 'Mediano', 'l': 'Grande'}
tamaño = ui.radio(opciones, value='m')
```

### **ui.select()**
Lista desplegable de selección
```python
# Select básico
pais = ui.select(['España', 'México', 'Argentina'], 
                 label='País', value='España')

# Select con opciones como diccionario
estado = ui.select({'act': 'Activo', 'inact': 'Inactivo'}, 
                   label='Estado')

# Select múltiple
idiomas = ui.select(['Español', 'Inglés', 'Francés'], 
                    multiple=True, label='Idiomas')
```

### **ui.slider()**
Control deslizante
```python
# Slider básico
volumen = ui.slider(min=0, max=100, value=50)

# Slider con etiquetas
temperatura = ui.slider(min=0, max=40, value=20, step=0.5)
```

### **ui.range()**
Selector de rango
```python
rango_precio = ui.range(min=0, max=1000, value={'min': 100, 'max': 500})
```

### **ui.upload()**
Subida de archivos
```python
def handle_upload(e):
    ui.notify(f'Archivo subido: {e.name}')

ui.upload(on_upload=handle_upload, max_file_size=1_000_000)
    .props('accept=.jpg,.png')
```

---

## 📊 Componentes de Visualización y Datos

```python
# Grid con funcionalidades avanzadas
grid = ui.aggrid({
    'defaultColDef': {'flex': 1, 'resizable': True, 'sortable': True},
    'columnDefs': [
        {'headerName': 'Nombre', 'field': 'name', 'pinned': 'left'},
        {'headerName': 'Edad', 'field': 'age', 'type': 'numericColumn'},
        {'headerName': 'Salario', 'field': 'salary', 'valueFormatter': 'params.value.toLocaleString("es-ES", {style: "currency", currency: "EUR"})'},
        {'headerName': 'Activo', 'field': 'active', 'cellRenderer': 'params.value ? "✓" : "✗"'},
    ],
    'rowData': [
        {'name': 'Alice', 'age': 28, 'salary': 50000, 'active': True},
        {'name': 'Bob', 'age': 32, 'salary': 65000, 'active': False},
        {'name': 'Carol', 'age': 29, 'salary': 58000, 'active': True},
    ],
    'rowSelection': 'multiple',
    'enableRangeSelection': True,
    'pagination': True,
    'paginationPageSize': 20,
}).classes('max-h-96')

# Métodos del grid
ui.button('Seleccionar todo', on_click=lambda: grid.run_grid_method('selectAll'))
ui.button('Exportar CSV', on_click=lambda: grid.run_grid_method('exportDataAsCsv'))
ui.button('Ajustar columnas', on_click=lambda: grid.run_grid_method('sizeColumnsToFit'))

# Actualizar datos
def actualizar_datos():
    grid.options['rowData'][0]['age'] += 1
    grid.update()

ui.button('Actualizar edad', on_click=actualizar_datos)
```

### **ui.echart()**
```python
ui.checkbox('Activar actualización').bind_value(timer, 'active')
```

### **Componentes de progreso**

#### **ui.linear_progress()**
Barra de progreso lineal
```python
# Progreso básico
slider = ui.slider(min=0, max=1, step=0.01, value=0.5)
ui.linear_progress(size='20px', color='green').bind_value_from(slider, 'value')

# Progreso indeterminado
ui.linear_progress(value=None, color='blue')  # Animación continua

# Con porcentaje personalizado
progress = ui.linear_progress(value=0.75, show_value=True)
```

#### **ui.circular_progress()**
Progreso circular
```python
# Progreso circular básico
slider = ui.slider(min=0, max=100, value=50)
ui.circular_progress(min=0, max=100, size='xl', color='orange').bind_value_from(slider, 'value')

# Progreso indeterminado
ui.circular_progress(value=None, size='lg', color='red')
```

#### **ui.spinner()**
Indicadores de carga
```python
with ui.row():
    ui.spinner(size='lg')  # Spinner por defecto
    ui.spinner('audio', size='lg', color='green')
    ui.spinner('bars', size='lg', color='blue')
    ui.spinner('dots', size='lg', color='red')
    ui.spinner('grid', size='lg', color='purple')
    ui.spinner('hourglass', size='lg', color='orange')
```

### **ui.scene()**
Escenas 3D con Three.js
```python
# Escena 3D completa
with ui.scene(width=600, height=400).classes('border') as scene:
    # Configuración de la escena
    scene.background_color = '#87CEEB'  # Azul cielo
    scene.axes_helper()  # Ejes de coordenadas
    
    # Formas básicas
    scene.box(1, 1, 1).material('#ff0000').move(x=-3)
    scene.sphere(0.5).material('#00ff00').move(x=-1)
    scene.cylinder(1, 0.5, 2).material('#0000ff', opacity=0.7).move(x=1)
    scene.cone(1, 2).material('#ffff00').move(x=3)
    
    # Líneas y curvas
    scene.line([0, 0, -2], [0, 2, -2]).material('#ff00ff')
    scene.curve([0, 0, 2], [1, 1, 2], [2, 0, 2], [3, 1, 2]).material('#00ffff')
    
    # Texto 2D y 3D
    scene.text('Texto 2D', 'background: rgba(255,255,255,0.8); padding: 5px').move(y=2, z=1)
    scene.text3d('Texto 3D', font_size=0.2).move(y=-1, z=1).material('#800080')
    
    # Grupo de objetos
    with scene.group().move(y=2) as grupo:
        scene.box(0.5, 0.5, 0.5).material('#ff8800').move(x=-1)
        scene.box(0.5, 0.5, 0.5).material('#ff8800').move(x=1)
    
    # Texturas
    logo_url = 'https://picsum.photos/200/200'
    scene.texture(logo_url, [[[0, 0, 3], [2, 0, 3]], [[0, 2, 3], [2, 2, 3]]]).move(x=-1)
    
    # Modelos 3D
    stl_url = 'https://upload.wikimedia.org/wikipedia/commons/9/93/Utah_teapot_(solid).stl'
    scene.stl(stl_url).scale(0.1).move(x=5, y=1)
    
    # Interacciones
    def on_click(e):
        ui.notify(f'Clic en objeto: {e.object.name}')
    
    scene.on_click = on_click

# Cámara personalizada
with ui.scene(camera=ui.scene.orthographic_camera(left=-5, right=5, top=5, bottom=-5)):
    scene.box().material('#ff0000')
```

### **ui.leaflet()**
Mapas interactivos
```python
# Mapa básico
mapa = ui.leaflet(center=(40.4168, -3.7038), zoom=10)  # Madrid

# Información del mapa
ui.label().bind_text_from(mapa, 'center', 
    lambda center: f'Centro: {center[0]:.4f}, {center[1]:.4f}')
ui.label().bind_text_from(mapa, 'zoom', 
    lambda zoom: f'Zoom: {zoom}')

# Controles del mapa
with ui.row():
    ui.button('Madrid', on_click=lambda: mapa.set_center((40.4168, -3.7038)))
    ui.button('Barcelona', on_click=lambda: mapa.set_center((41.3851, 2.1734)))
    ui.button('Zoom +', on_click=lambda: mapa.set_zoom(mapa.zoom + 1))
    ui.button('Zoom -', on_click=lambda: mapa.set_zoom(mapa.zoom - 1))

# Mapa con controles de dibujo
mapa_dibujo = ui.leaflet(
    center=(51.505, -0.09), 
    zoom=13, 
    draw_control=True
)
```

---

## 📦 Componentes de Layout

### **Auto-context**
NiceGUI rastrea automáticamente el contexto de los elementos
```python
with ui.card():
    ui.label('Contenido de tarjeta')
    ui.button('Agregar', on_click=lambda: ui.label('¡Clic!'))
    ui.timer(1.0, lambda: ui.label('¡Tick!'), once=True)
```

### **ui.row()**
Layout horizontal
```python
# Row básico
with ui.row():
    ui.button('Botón 1')
    ui.button('Botón 2')
    ui.button('Botón 3')

# Row con propiedades
with ui.row().classes('w-full border'):
    ui.label('Izquierda')
    ui.space()  # Ocupa todo el espacio disponible
    ui.label('Derecha')
```

### **ui.column()**
Layout vertical
```python
# Column básico
with ui.column():
    ui.label('Título')
    ui.input('Campo 1')
    ui.input('Campo 2')

# Column con alineación
with ui.column().props('align_items=center'):
    ui.label('Centrado')
    ui.button('Botón centrado')
```

### **ui.grid()**
Layout en cuadrícula
```python
# Grid con columnas fijas
with ui.grid(columns=2):
    ui.label('Nombre:')
    ui.label('Tom')
    ui.label('Edad:')
    ui.label('42')

# Grid con template CSS
with ui.grid(columns='auto 1fr'):
    ui.label('Etiqueta')
    ui.input('Campo que se expande')
```

### **ui.card()**
Tarjeta contenedora
```python
# Card básico
with ui.card():
    ui.label('Título de la tarjeta')
    ui.label('Contenido de la tarjeta')
    ui.button('Acción')

# Card tight (sin padding)
with ui.card().tight():
    ui.image('https://picsum.photos/640/360')
    with ui.card_section():
        ui.label('Descripción de la imagen')
```

### **ui.expansion()**
Panel expandible (acordeón)
```python
# Expansion básico
with ui.expansion('Configuración avanzada'):
    ui.switch('Opción 1')
    ui.switch('Opción 2')

# Expansion con icono y grupo
with ui.expansion('Sección 1', icon='settings', group='accordion'):
    ui.label('Contenido de sección 1')
    
with ui.expansion('Sección 2', icon='help', group='accordion'):
    ui.label('Contenido de sección 2')
```

### **ui.tabs()**
Pestañas
```python
with ui.tabs().classes('w-full') as tabs:
    tab1 = ui.tab('Pestaña 1')
    tab2 = ui.tab('Pestaña 2')

with ui.tab_panels(tabs, value=tab1):
    with ui.tab_panel(tab1):
        ui.label('Contenido de pestaña 1')
    with ui.tab_panel(tab2):
        ui.label('Contenido de pestaña 2')
```

### **ui.splitter()**
Divisor redimensionable
```python
# Splitter vertical
with ui.splitter() as splitter:
    with splitter.before:
        ui.label('Panel izquierdo').classes('mr-2')
    with splitter.after:
        ui.label('Panel derecho').classes('ml-2')

# Splitter horizontal
with ui.splitter(horizontal=True, limits=(20, 80), value=30):
    with splitter.before:
        ui.label('Panel superior')
    with splitter.after:
        ui.label('Panel inferior')
```

### **ui.list()**
Lista de elementos
```python
with ui.list().props('dense separator'):
    ui.item('3 Manzanas')
    ui.item('5 Plátanos')
    ui.item('8 Fresas')
    ui.item('13 Nueces')
```

### **ui.slide_item()**
Elemento deslizable con acciones
```python
with ui.list().props('bordered separator'):
    with ui.slide_item('Desliza izq/der') as slide:
        slide.left('Izquierda', color='green')
        slide.right('Derecha', color='red')
    
    with ui.slide_item('Desliza arriba/abajo') as slide:
        slide.top('Arriba', color='blue')
        slide.bottom('Abajo', color='purple')
```

### **ui.scroll_area()**
Área con scroll personalizado
```python
with ui.scroll_area().classes('w-32 h-32 border'):
    ui.label('Contenido largo que requiere scroll. ' * 20)
```

### **ui.stepper()**
Asistente paso a paso
```python
with ui.stepper().props('vertical').classes('w-full') as stepper:
    with ui.step('Paso 1'):
        ui.label('Contenido del primer paso')
        with ui.stepper_navigation():
            ui.button('Siguiente', on_click=stepper.next)
    
    with ui.step('Paso 2'):
        ui.label('Contenido del segundo paso')
        with ui.stepper_navigation():
            ui.button('Siguiente', on_click=stepper.next)
            ui.button('Atrás', on_click=stepper.previous).props('flat')
    
    with ui.step('Finalizar'):
        ui.label('¡Completado!')
        with ui.stepper_navigation():
            ui.button('Finalizar', on_click=lambda: ui.notify('¡Listo!'))
```

### **ui.timeline()**
Línea de tiempo
```python
with ui.timeline(side='right'):
    ui.timeline_entry('Inicio del proyecto.',
                      title='Primer commit',
                      subtitle='7 Mayo, 2021')
    ui.timeline_entry('Primera versión pública.',
                      title='Release v0.1',
                      subtitle='14 Mayo, 2021')
    ui.timeline_entry('Versión estable lanzada.',
                      title='Release v1.0',
                      subtitle='15 Diciembre, 2022',
                      icon='rocket')
```

### **ui.carousel()**
Carrusel de contenido
```python
with ui.carousel(animated=True, arrows=True, navigation=True).props('height=180px'):
    with ui.carousel_slide().classes('p-0'):
        ui.image('https://picsum.photos/id/30/270/180')
    with ui.carousel_slide().classes('p-0'):
        ui.image('https://picsum.photos/id/31/270/180')
    with ui.carousel_slide().classes('p-0'):
        ui.image('https://picsum.photos/id/32/270/180')
```

### **ui.pagination()**
Paginación
```python
p = ui.pagination(1, 10, direction_links=True)
ui.label().bind_text_from(p, 'value', lambda v: f'Página {v}')
```

### **Elementos de utilidad**

#### **ui.separator()**
Separador visual
```python
ui.label('Texto arriba')
ui.separator()
ui.label('Texto abajo')
```

#### **ui.space()**
Espacio flexible en layouts
```python
with ui.row().classes('w-full'):
    ui.label('Izquierda')
    ui.space()  # Toma todo el espacio disponible
    ui.label('Derecha')
```

#### **ui.skeleton()**
Placeholder de carga
```python
ui.skeleton().classes('w-full h-8')  # Rectángulo
ui.skeleton(type='text', animation='pulse')  # Texto
ui.skeleton(type='circle', size='50px')  # Círculo
```

#### **ui.teleport()**
Teletransportar contenido a otro lugar
```python
markdown = ui.markdown('Ingresa tu **nombre**!')

def inject_input():
    with ui.teleport(f'#{markdown.html_id} strong'):
        ui.input('nombre').classes('inline-flex').props('dense')

ui.button('Inyectar input', on_click=inject_input)
```

#### **ui.fullscreen()**
Control de pantalla completa
```python
fullscreen = ui.fullscreen()
ui.button('Pantalla completa', on_click=fullscreen.enter)
ui.button('Salir pantalla completa', on_click=fullscreen.exit)
ui.button('Alternar', on_click=fullscreen.toggle)
```

---

## 🎪 Componentes Interactivos

### **ui.dialog()**
Ventana modal
```python
# Dialog básico
with ui.dialog() as dialogo:
    with ui.card():
        ui.label('¿Estás seguro?')
        with ui.row():
            ui.button('Sí', on_click=dialogo.close)
            ui.button('No', on_click=dialogo.close)

ui.button('Abrir diálogo', on_click=dialogo.open)

# Dialog persistente (no se cierra con ESC o clic fuera)
with ui.dialog().props('persistent') as dialog_persistente:
    with ui.card():
        ui.label('Este diálogo requiere acción explícita')
        ui.button('Cerrar', on_click=dialog_persistente.close)
```

### **ui.menu()**
Menú contextual
```python
# Menú básico
with ui.row().classes('w-full items-center'):
    resultado = ui.label().classes('mr-auto')
    with ui.button(icon='menu'):
        with ui.menu() as menu:
            ui.menu_item('Opción 1', lambda: resultado.set_text('Seleccionaste 1'))
            ui.menu_item('Opción 2', lambda: resultado.set_text('Seleccionaste 2'))
            ui.menu_item('Opción 3 (no cierra)', 
                         lambda: resultado.set_text('Seleccionaste 3'), 
                         auto_close=False)
            ui.separator()
            ui.menu_item('Cerrar', menu.close)
```

### **ui.context_menu()**
Menú de clic derecho
```python
with ui.image('https://picsum.photos/640/360'):
    with ui.context_menu():
        ui.menu_item('Voltear horizontalmente')
        ui.menu_item('Voltear verticalmente')
        ui.separator()
        ui.menu_item('Reiniciar', auto_close=False)
```

### **ui.tooltip()**
Información emergente
```python
# Tooltip simple
with ui.button(icon='thumb_up'):
    ui.tooltip('Me gusta esto').classes('bg-green')

# Tooltip con contenido complejo
with ui.button('Información'):
    with ui.tooltip():
        ui.label('Tooltip personalizado')
        ui.label('Con múltiples líneas')
```

### **ui.notify()**
Notificaciones toast
```python
# Notificaciones básicas
ui.notify('Mensaje informativo')
ui.notify('Éxito', type='positive')
ui.notify('Advertencia', type='warning')
ui.notify('Error', type='negative')

# Notificación con botón de cierre
ui.notify('Mensaje persistente', close_button='OK')

# Notificación en posición específica
ui.notify('Esquina superior', position='top-right')

# Notificación multilínea
ui.notify('Línea 1\nLínea 2\nLínea 3', multi_line=True)
```

### **ui.notification()**
Notificación actualizable
```python
import asyncio

async def proceso_largo():
    n = ui.notification(timeout=None)
    for i in range(10):
        n.message = f'Progreso {i*10}%'
        n.spinner = True
        await asyncio.sleep(0.2)
    n.message = '¡Completado!'
    n.spinner = False
    await asyncio.sleep(1)
    n.dismiss()

ui.button('Iniciar proceso', on_click=proceso_largo)
```

### **ui.timer()**
Temporizador para actualizaciones
```python
import datetime

# Timer básico
tiempo = ui.label()

def actualizar_tiempo():
    tiempo.text = datetime.datetime.now().strftime('%H:%M:%S')

ui.timer(1.0, actualizar_tiempo)  # Cada segundo

# Timer que se ejecuta una sola vez
ui.timer(5.0, lambda: ui.notify('¡5 segundos!'), once=True)
```

---

## 🎨 Personalización y Estilo

### **Estilos CSS**
```python
# Estilo directo
ui.label('Texto rojo').style('color: red; font-size: 20px')

# Clases CSS
ui.label('Texto con clase').classes('text-center font-bold')

# Props de Quasar
ui.button('Botón').props('flat round color=primary')
```

### **Colores del tema**
```python
# Configurar colores globales
ui.colors(primary='#1976d2', secondary='#26a69a')
```

### **Tailwind CSS**
```python
# Usando clases de Tailwind
ui.label('Texto').classes('text-2xl font-bold text-blue-600')
ui.button('Botón').classes('bg-green-500 hover:bg-green-600')
```

---

## 🎯 Eventos y Funciones Útiles

### **Manejo de eventos**
```python
def on_click():
    ui.notify('¡Botón presionado!')

def on_change(e):
    ui.notify(f'Valor cambiado a: {e.value}')

ui.button('Clic', on_click=on_click)
ui.input('Campo', on_change=on_change)
```

### **Binding de datos**
```python
nombre = ui.input('Nombre')
ui.label().bind_text_from(nombre, 'value', lambda x: f'Hola, {x}!')
```

### **Actualización dinámica**
```python
contador = ui.label('0')
valor = 0

def incrementar():
    global valor
    valor += 1
    contador.text = str(valor)

ui.button('Incrementar', on_click=incrementar)
```

---

## 🗄️ Sistema de Almacenamiento (Storage)

NiceGUI ofrece 5 tipos de almacenamiento diferentes según las necesidades:

### **app.storage.tab**
Almacenamiento por pestaña (server-side, en memoria)
```python
@ui.page('/')
def pagina():
    # Único por pestaña, se pierde al reiniciar servidor
    app.storage.tab['contador'] = app.storage.tab.get('contador', 0) + 1
    ui.label(f'Visitas en esta pestaña: {app.storage.tab["contador"]}')
```

### **app.storage.client**
Almacenamiento por cliente (server-side, en memoria)
```python
@ui.page('/')
def pagina():
    # Se pierde al recargar la página o navegar
    app.storage.client['session_data'] = 'datos de la sesión'
    ui.label('Datos guardados para este cliente')
```

### **app.storage.user**
Almacenamiento por usuario (server-side, persistente)
```python
@ui.page('/')
def pagina():
    # Persiste entre pestañas y reinicios del servidor
    app.storage.user['visitas'] = app.storage.user.get('visitas', 0) + 1
    
    with ui.row():
        ui.label('Tus visitas totales:')
        ui.label().bind_text_from(app.storage.user, 'visitas')

# Requiere storage_secret en ui.run()
ui.run(storage_secret='clave_secreta_para_cookies')
```

### **app.storage.general**
Almacenamiento general (compartido entre todos los usuarios)
```python
# Accesible desde cualquier lugar, no requiere página específica
app.storage.general['contador_global'] = app.storage.general.get('contador_global', 0) + 1

@ui.page('/')
def pagina():
    ui.label(f'Visitantes totales: {app.storage.general["contador_global"]}')
```

### **app.storage.browser**
Almacenamiento en cookie del navegador
```python
@ui.page('/')
def pagina():
    # Almacenado como cookie del navegador
    app.storage.browser['preferencia'] = 'tema_oscuro'
    
    # Cada navegador tiene un ID único
    user_id = app.storage.browser['id']
    ui.label(f'Tu ID de navegador: {user_id}')

ui.run(storage_secret='clave_secreta_para_cookies')
```

### **Tabla comparativa de almacenamiento**
```python
# ┌─────────────┬─────────┬─────┬──────────┬──────┬─────────┐
# │ Tipo        │ Client  │ Tab │ Browser  │ User │ General │
# ├─────────────┼─────────┼─────┼──────────┼──────┼─────────┤
# │ Ubicación   │ Servidor│ Srv │ Navegador│ Srv  │ Servidor│
# │ Entre tabs  │ No      │ No  │ Sí       │ Sí   │ Sí      │
# │ Entre naveg │ No      │ No  │ No       │ No   │ Sí      │
# │ Reinicio srv│ No      │ Sí  │ No       │ Sí   │ Sí      │
# │ Recarga pág │ No      │ Sí  │ Sí       │ Sí   │ Sí      │
# │ Requiere @ui│ Sí      │ Sí  │ Sí       │ Sí   │ No      │
# │ Req secret  │ No      │ No  │ Sí       │ Sí   │ No      │
# └─────────────┴─────────┴─────┴──────────┴──────┴─────────┘
```

## 🎛️ Eventos del Sistema

### **Eventos de aplicación**
Ciclo de vida de la aplicación
```python
from datetime import datetime
from nicegui import app

# Eventos de aplicación
@app.on_startup
async def startup():
    print('NiceGUI iniciado')
    app.storage.general['start_time'] = datetime.now()

@app.on_shutdown  
async def shutdown():
    print('NiceGUI cerrándose')

@app.on_connect
def client_connected(client):
    print(f'Cliente conectado: {client}')
    app.storage.general['connections'] = app.storage.general.get('connections', 0) + 1

@app.on_disconnect
def client_disconnected(client):
    print(f'Cliente desconectado: {client}')

@app.on_exception
def handle_exception(exception):
    print(f'Excepción: {exception}')
    ui.notify(f'Error: {exception}', type='negative')

# Cerrar programáticamente
ui.button('Cerrar aplicación', on_click=app.shutdown)
```

### **Ejemplo completo de storage**
```python
from nicegui import app, ui
from datetime import datetime

@ui.page('/')
def index():
    # Contador por usuario (persistente)
    app.storage.user['visitas'] = app.storage.user.get('visitas', 0) + 1
    
    # Última visita en esta pestaña
    app.storage.tab['ultima_visita'] = datetime.now().strftime('%H:%M:%S')
    
    # Datos temporales del cliente
    app.storage.client['session_id'] = f"sess_{datetime.now().timestamp()}"
    
    # Contador global
    app.storage.general['total_visitas'] = app.storage.general.get('total_visitas', 0) + 1
    
    # Preferencias en browser
    if 'tema' not in app.storage.browser:
        app.storage.browser['tema'] = 'claro'
    
    with ui.column():
        ui.label(f"Tus visitas: {app.storage.user['visitas']}")
        ui.label(f"Última visita esta pestaña: {app.storage.tab['ultima_visita']}")
        ui.label(f"Visitas totales del sitio: {app.storage.general['total_visitas']}")
        ui.label(f"Tema actual: {app.storage.browser['tema']}")
        
        def cambiar_tema():
            tema_actual = app.storage.browser['tema']
            app.storage.browser['tema'] = 'oscuro' if tema_actual == 'claro' else 'claro'
            ui.notify(f'Tema cambiado a: {app.storage.browser["tema"]}')
        
        ui.button('Cambiar tema', on_click=cambiar_tema)

ui.run(storage_secret='mi_clave_secreta_super_segura')
```

### **Configuración básica**
```python
# Configuración del servidor
ui.run(
    title='Mi Aplicación',
    port=8080,
    host='0.0.0.0',
    dark=True,  # Tema oscuro por defecto
    favicon='🚀'
)
```

### **Páginas múltiples**
```python
@ui.page('/')
def index():
    ui.label('Página principal')
    ui.link('Ir a about', '/about')

@ui.page('/about')
def about():
    ui.label('Página about')
    ui.link('Volver al inicio', '/')

ui.run()
```

---

## 💡 Consejos y Trucos

### **1. Auto-reload**
NiceGUI recarga automáticamente cuando cambias el código

### **2. Acceso a valores**
```python
# Obtener valor de componente
input_field = ui.input('Nombre')
print(input_field.value)  # Obtiene el valor actual
```

### **3. Contexto de elementos**
```python
# Usar 'with' para anidar elementos
with ui.card():
    with ui.column():
        ui.label('Título')
        ui.button('Acción')
```

### **4. Manipulación de contenedores**
```python
container = ui.row()

# Agregar elementos dinámicamente
def agregar_elemento():
    with container:
        ui.icon('face')

# Limpiar contenedor
container.clear()

# Remover elemento específico
container.remove(0)  # Por índice
container.remove(elemento)  # Por referencia
elemento.delete()  # Eliminar elemento directamente
```

### **5. Binding de datos**
```python
# Binding unidireccional
nombre = ui.input('Nombre')
ui.label().bind_text_from(nombre, 'value', lambda x: f'Hola, {x}!')

# Binding bidireccional
campo1 = ui.input('Campo 1')
campo2 = ui.input('Campo 2')
campo1.bind_value(campo2, 'value')
```

### **6. Props de Quasar**
```python
# Usar propiedades de Quasar directamente
ui.button('Botón').props('flat round color=primary size=lg')
ui.input('Campo').props('filled dense clearable')
```

### **7. Manejo de eventos avanzado**
```python
def handle_key(e):
    if e.key == 'Enter':
        ui.notify('Enter presionado')

ui.input('Campo').on('keydown', handle_key)
```

### **8. Depuración**
```python
# Logs en consola del navegador
ui.run(show=True)  # Abre automáticamente el navegador
ui.run(reload=False)  # Desactiva auto-reload
ui.run(port=3000)  # Cambia puerto por defecto
```

### **9. Persistencia entre sesiones**
```python
# Usar FastAPI para sesiones
from fastapi import Request

@ui.page('/')
def index(request: Request):
    # Acceso a sesión HTTP
    session = request.session
```

### **10. JavaScript personalizado y APIs del navegador**
```python
# Ejecutar JavaScript
ui.run_javascript('alert("Hola desde JS")')

# Obtener información del navegador
async def info_navegador():
    info = await ui.run_javascript('''
        return {
            userAgent: navigator.userAgent,
            language: navigator.language,
            screen: {width: screen.width, height: screen.height}
        }
    ''')
    ui.notify(f'Navegador: {info}')

# Agregar CSS personalizado
ui.add_head_html('<style>body { background: #f0f0f0; }</style>')

# Portapapeles (solo en páginas específicas)
@ui.page('/')
async def pagina():
    ui.button('Copiar', on_click=lambda: ui.clipboard.write('Texto copiado'))
    
    async def leer():
        texto = await ui.clipboard.read()
        ui.notify(f'Leído: {texto}')
    ui.button('Leer', on_click=leer)
```

### **11. Rendimiento y tareas pesadas**
```python
from nicegui import run
import time

# CPU-bound (proceso separado)
def calculo_pesado(n):
    time.sleep(2)  # Simular trabajo
    return n * n

async def ejecutar_calculo():
    resultado = await run.cpu_bound(calculo_pesado, 100)
    ui.notify(f'Resultado: {resultado}')

# I/O-bound (hilo separado)  
async def descarga():
    import requests
    response = await run.io_bound(requests.get, 'https://api.github.com')
    ui.notify(f'Status: {response.status_code}')

ui.button('Cálculo pesado', on_click=ejecutar_calculo)
ui.button('Descarga', on_click=descarga)
```

### **12. Almacenamiento persistente**
```python
# 5 tipos de storage disponibles:
# - app.storage.client (por conexión)
# - app.storage.tab (por pestaña)  
# - app.storage.browser (cookie del navegador)
# - app.storage.user (por usuario, persistente)
# - app.storage.general (global, compartido)

@ui.page('/')
def pagina():
    app.storage.user['visitas'] = app.storage.user.get('visitas', 0) + 1
    ui.label(f'Visitas: {app.storage.user["visitas"]}')

ui.run(storage_secret='clave_secreta')
```

---

## 📚 Recursos Adicionales

- **Documentación oficial**: https://nicegui.io/documentation
- **GitHub**: https://github.com/zauberzeug/nicegui
- **Ejemplos**: https://github.com/zauberzeug/nicegui/tree/main/examples
- **Wiki con tutoriales**: https://github.com/zauberzeug/nicegui/wiki

---

*¡Happy coding with NiceGUI! 🎉*
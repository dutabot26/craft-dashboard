# 📊 Dashboard Presupuesto 2026 · Craft Logistics
## Versión conectada a SharePoint · Guía de instalación y actualización

---

## ¿Qué hace esta versión?

- Lee los archivos Excel **directamente desde SharePoint** cada vez que alguien abre el dashboard
- **No hay que reemplazar archivos ni ejecutar comandos** para actualizar los datos
- El equipo solo edita los Excel en SharePoint como siempre → el dashboard se actualiza solo
- Se refresca automáticamente cada 30 minutos en segundo plano

---

## PASO 1 · Obtener los links de descarga de SharePoint

Esto se hace **una sola vez**, para cada uno de los 4 archivos Excel.

Para **cada archivo**:

1. Abre SharePoint en el navegador y navega hasta el archivo
2. Haz clic en los **tres puntos (···)** que aparecen al pasar el mouse sobre el archivo
3. Selecciona **"Compartir"**
4. En la ventana que aparece, haz clic en **"Configuración del vínculo"** (el lápiz o engranaje)
5. Selecciona **"Cualquier persona con el vínculo puede ver"**
6. En **"Más configuraciones"**, asegúrate de que **NO haya fecha de expiración**
7. Haz clic en **"Aplicar"** y luego en **"Copiar vínculo"**
8. Guarda ese link en un lugar seguro

Repite para los 4 archivos:
- `CUADRO_SEGUIMIENTO_FACTURAS_MAJO__ALEJO.xlsx`
- `4__ADM_PPTO_gastos_año_2026_BR.xlsx`
- `5__GH_PPTO_gastos_año_2026_BR.xlsx`
- `6__IT_PPTO_gastos_año_2026_BR.xlsx`

---

## PASO 2 · Editar el archivo config.toml

Abre el archivo `config.toml` con cualquier editor de texto (Bloc de notas, VS Code, etc.).

Encontrarás esto:

```toml
[archivos]
facturas = "PEGA_AQUI_EL_LINK_DEL_ARCHIVO_CUADRO_SEGUIMIENTO_FACTURAS"
ppto_adm = "PEGA_AQUI_EL_LINK_DEL_ARCHIVO_4__ADM_PPTO"
ppto_gh  = "PEGA_AQUI_EL_LINK_DEL_ARCHIVO_5__GH_PPTO"
ppto_it  = "PEGA_AQUI_EL_LINK_DEL_ARCHIVO_6__IT_PPTO"
```

Reemplaza cada texto entre comillas con el link que copiaste en el Paso 1:

```toml
[archivos]
facturas = "https://craftms-my.sharepoint.com/:x:/g/personal/dutabot_..."
ppto_adm = "https://craftms-my.sharepoint.com/:x:/g/personal/dutabot_..."
ppto_gh  = "https://craftms-my.sharepoint.com/:x:/g/personal/dutabot_..."
ppto_it  = "https://craftms-my.sharepoint.com/:x:/g/personal/dutabot_..."
```

Guarda el archivo.

---

## PASO 3 · Instalar Python (solo la primera vez)

1. Ve a https://www.python.org/downloads/
2. Descarga Python 3.11 o superior
3. Durante la instalación marca **"Add Python to PATH"**

Verifica en la terminal:
```bash
python --version
# Debe mostrar: Python 3.11.x
```

---

## PASO 4 · Instalar las dependencias (solo la primera vez)

Abre la terminal en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

---

## PASO 5 · Ejecutar el dashboard

```bash
streamlit run app.py
```

El dashboard se abre en `http://localhost:8501` y descarga automáticamente los archivos de SharePoint.

---

## ¿Cómo se actualizan los datos de ahora en adelante?

**El equipo no tiene que hacer nada en el dashboard.**

El flujo es exactamente el mismo de siempre:

```
1. Alguien del equipo edita el Excel en SharePoint (agrega facturas, corrige datos, etc.)
2. Guarda el archivo en SharePoint
3. La próxima vez que alguien abra el dashboard → datos actualizados
4. O se puede forzar la actualización con el botón "🔄 Forzar actualización ahora"
   que aparece en el panel izquierdo del dashboard
```

**Frecuencia de refresco automático:** cada 30 minutos (configurable en `config.toml`).

---

## Estructura de archivos

```
craft_v2/
├── app.py                    ← dashboard principal (no tocar)
├── sharepoint_connector.py   ← conexión a SharePoint (no tocar)
├── requirements.txt          ← dependencias (no tocar)
├── config.toml               ← ⭐ ÚNICO ARCHIVO QUE SE EDITA
└── README.md                 ← esta guía
```

---

## Solución de problemas

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| "Sin permiso para descargar" | El link no es "Cualquier persona" | Repetir Paso 1, asegurarse de elegir "Cualquier persona" |
| "Archivo no encontrado" | Link incorrecto o expirado | Generar un nuevo link en SharePoint |
| "No parece ser un Excel" | Se copió el link de la carpeta, no del archivo | Compartir el archivo individual, no la carpeta |
| Dashboard muestra datos viejos | Caché activo | Usar botón "🔄 Forzar actualización" en el sidebar |
| "config.toml no encontrado" | Terminal no está en la carpeta correcta | Asegurarse de ejecutar `streamlit run app.py` desde la carpeta `craft_v2/` |

---

## Para compartirlo con todo el equipo sin instalar nada

### Opción A · Streamlit Community Cloud (recomendada · gratuita)

1. Sube la carpeta `craft_v2/` a un repositorio de GitHub (privado)
2. Ve a https://share.streamlit.io → conecta tu cuenta de GitHub
3. Selecciona el repositorio y el archivo `app.py`
4. El dashboard queda disponible en una URL pública o privada
5. Cualquier persona del equipo lo abre desde el navegador, sin instalar nada
6. Cuando el equipo actualice los Excel en SharePoint, el dashboard se actualiza solo

### Opción B · Servidor interno

Instala Python en un servidor de la empresa y ejecuta `streamlit run app.py`.
La URL será `http://IP-DEL-SERVIDOR:8501` y cualquier persona en la red interna puede acceder.

---

*Versión SharePoint · Dashboard Presupuesto 2026 · Craft Logistics · Junio 2026*

# 📊 Dashboard Presupuesto 2026 · Craft Logistics
## Guía de uso completa para el equipo

---

> Esta guía explica cómo ver, filtrar e interpretar el dashboard.
> No se necesita saber programación ni tocar ningún archivo.

---

## ¿Cómo acceder al dashboard?

Abre este link en cualquier navegador (Chrome, Edge, Safari):

**🔗 https://craft-dashboard-fz9oi7fxnuhsxeaj7erg4r.streamlit.app**

No necesitas crear cuenta, instalar nada ni iniciar sesión.
Funciona desde el computador, la tableta y el celular.

---

## ¿Cómo se actualiza el dashboard?

**No hay que hacer nada especial.**

El dashboard lee directamente los archivos Excel que están en SharePoint.
Cada vez que alguien del equipo edita y guarda un Excel en SharePoint,
el dashboard muestra esos cambios automáticamente en los próximos 30 minutos.

Si necesitas ver los cambios **ahora mismo**, usa el botón
**"🔄 Forzar actualización"** en el panel izquierdo.

---

## Partes del dashboard

```
┌──────────────────────────────────────────────────────────┐
│  PANEL IZQUIERDO          │  ÁREA PRINCIPAL              │
│  (Filtros y controles)    │  (KPIs y gráficos)           │
│                           │                              │
│  📅 Mes de ejecución      │  💰 Tarjetas KPI             │
│  🏢 Área                  │  📊 Gráfico mensual          │
│  📍 Sucursal              │  📈 Por área                 │
│  📌 Fijo / Variable       │  📍 Por sucursal             │
│  📋 Vista presupuesto     │  🍩 Tipo de gasto            │
│  🔄 Actualización         │  👥 Top proveedores          │
│  🔍 Calidad de datos      │  📋 Tabla de facturas        │
└──────────────────────────────────────────────────────────┘
```

---

## Los 5 indicadores clave (KPIs)

Están en la parte superior del dashboard y cambian según los filtros aplicados.

| Indicador | Qué significa |
|-----------|--------------|
| **Total Gastado** | Suma de todas las facturas en los meses/áreas/sedes filtradas |
| **Presupuesto** | Presupuesto planeado (anual o mensual según la vista elegida) |
| **% Ejecución** | Qué porcentaje del presupuesto ya se gastó |
| **Saldo Disponible** | Lo que queda por gastar (verde = hay saldo, rojo = excedido) |
| **Facturas** | Cuántas facturas hay en la selección actual |

---

## Cómo usar los filtros del panel izquierdo

### 📅 Mes de ejecución
Muestra el gasto solo de los meses que selecciones.

- **"Todos"** (por defecto): muestra todo el año
- Si seleccionas **"Enero"** y **"Febrero"**: solo verás las facturas de esos dos meses
- Puedes combinar varios meses a la vez

> 💡 **Consejo:** Este filtro también afecta el presupuesto cuando usas la vista "Mensual"

---

### 🏢 Área
Filtra por área de la empresa: ADM, IT, GH o Sin clasificar.

- Puedes seleccionar una, varias o todas
- Los KPIs y todos los gráficos se actualizan al instante

---

### 📍 Sucursal / Sede
Filtra por ciudad o sede:

- Calle 100 (Bogotá)
- Aeropuerto
- Cartagena
- Buenaventura
- Medellín
- Cali
- Barranquilla
- Transversal (gastos que aplican a varias sedes)
- Sin clasificar (facturas sin sede asignada)

---

### 📌 Fijo / Variable
Separa los gastos fijos (arriendos, internet, etc.) de los variables (viajes, materiales, etc.)

---

### 📋 Vista de Presupuesto ← **El filtro nuevo que pedía tu compañero**

Este es el control más importante para el análisis de ejecución:

**Opción 1 · "Anual (total año)"**
Compara el gasto contra el presupuesto **completo del año**.
Útil para ver cuánto queda del año en total.

Ejemplo: si en enero gasté $172M y el presupuesto anual de ADM es $5.020B,
la ejecución aparece como 3.4%.

---

**Opción 2 · "Mensual (según filtro de meses)"**
Compara el gasto contra el presupuesto **solo de los meses seleccionados**.
Útil para saber si ese mes específico se fue sobre o bajo presupuesto.

Ejemplo: si selecciono solo "Enero" en el filtro de meses y elijo esta vista,
el presupuesto que aparece es el de enero, y la ejecución te dice si enero
quedó bien, sobre o bajo presupuesto.

> 💡 **Cómo usarlo para el análisis mensual que pedía tu compañero:**
> 1. En "Mes de ejecución" selecciona el mes que quieres analizar (ej: Marzo)
> 2. En "Vista de Presupuesto" selecciona "Mensual (según filtro de meses)"
> 3. Ahora los KPIs muestran: gasto de Marzo vs presupuesto de Marzo
> 4. El % de ejecución te dice si marzo fue eficiente o no

---

## Los gráficos explicados

### 📊 Ejecución Mensual vs Presupuesto
Barras agrupadas: la barra azul clara es el presupuesto, la azul oscura es el gasto real.
La línea naranja muestra la tendencia del gasto.
Si la barra de gasto supera la de presupuesto en algún mes → ese mes se pasó.

### ⚖️ Presupuesto vs Ejecutado por Área
Compara ADM, IT y GH lado a lado.
El porcentaje encima de cada barra de gasto indica el % de ejecución de esa área.

### 📍 Gasto por Sucursal
Barras horizontales ordenadas de mayor a menor gasto.
Muestra el monto y el porcentaje del total que representa cada sede.

### 📅 Presupuesto Mensual por Área
Muestra cuánto está planeado gastar cada mes en cada área.
Útil para ver si hay meses donde el presupuesto es más alto (ej: IT en abril).

### 🍩 Distribución por Tipo de Gasto
Muestra qué tipo de gastos concentran más el presupuesto.
Arriendos suelen ser el mayor.

### 👥 Top 10 Proveedores
Los 10 proveedores con mayor facturación en la selección actual.

### 📋 Tabla de facturas
Muestra el detalle de todas las facturas que cumplen con los filtros aplicados.
Se puede hacer scroll para ver todas.

---

## Ejemplos de análisis útiles

### ¿Cómo saber si un área se pasó del presupuesto en un mes específico?
1. Seleccionar el mes en "Mes de ejecución"
2. Seleccionar el área en "Área"
3. Cambiar "Vista de Presupuesto" a "Mensual"
4. Ver el KPI "% Ejecución" y el KPI "Saldo Disponible"

### ¿Cómo ver cuánto gasta una sede en el año?
1. Dejar todos los meses
2. En "Sucursal" seleccionar solo esa sede
3. El KPI "Total Gastado" muestra el acumulado del año de esa sede

### ¿Cómo comparar dos meses?
1. En "Mes de ejecución" seleccionar los dos meses (ej: Enero y Febrero)
2. El gráfico "Ejecución Mensual" muestra ambas barras juntas

### ¿Cómo ver solo gastos fijos?
1. En "Fijo / Variable" deseleccionar "Variable"
2. Todos los gráficos se actualizan para mostrar solo gastos fijos

---

## La alerta amarilla de calidad de datos

Si aparece este mensaje en la parte superior:

> ⚠️ X facturas sin área y Y sin sucursal están incluidas como "Sin clasificar"

Significa que esas facturas en el Excel no tienen el campo Área o Sucursal completado.
**El gasto de esas facturas SÍ está incluido en los totales** (no se eliminó).
Se recomienda completar esos campos directamente en el Excel de SharePoint.

---

## ¿Cómo actualizar los datos?

Solo edita y guarda el Excel en SharePoint como siempre.
En los próximos 30 minutos el dashboard lo refleja automáticamente.

Si quieres ver los cambios ya, usa el botón **"🔄 Forzar actualización"** en el panel izquierdo.

---

## ¿Algo no funciona?

| Síntoma | Qué hacer |
|---------|-----------|
| Gráficos en blanco o vacíos | Verificar que los filtros no estén muy restrictivos |
| Error rojo en la pantalla | Avisar a la persona responsable del dashboard |
| Los datos se ven desactualizados | Usar "🔄 Forzar actualización" |
| No carga desde el celular | Intentar con WiFi en lugar de datos móviles |

---

*Dashboard Presupuesto 2026 · Craft Logistics · Versión 2 · Junio 2026*
*Desarrollado con Streamlit + Python · Conectado a SharePoint*

# 📊 DataAnalyst Pro

**Aplicación de escritorio para análisis estadístico, exploración de datos, visualización y modelado predictivo desarrollada en Python.**

DataAnalyst Pro es una herramienta que integra diferentes funcionalidades de análisis de datos en una sola aplicación. Permite importar conjuntos de datos desde distintos formatos, explorar información, realizar análisis estadísticos, generar visualizaciones, entrenar modelos predictivos y elaborar informes en PDF.

Su objetivo es facilitar el procesamiento y la interpretación de datos mediante una interfaz gráfica intuitiva, reuniendo herramientas que normalmente se utilizan de manera independiente.

---

## 🚀 Funcionalidades principales

### 📂 1. Importación de datos
- Importación de archivos Excel (`.xlsx` y `.xls`).
- Importación de archivos CSV.
- Lectura de archivos SQL compatibles con SQLite.
- Apertura de bases de datos SQLite (`.db` y `.sqlite`).
- Exploración de tablas y hojas disponibles.
- Visualización de registros y columnas.
- Carga de conjuntos de datos para su posterior análisis.

### 🔎 2. Exploración y preparación de datos
- Identificación de variables numéricas y categóricas.
- Revisión de valores faltantes.
- Exploración de registros y columnas.
- Análisis de la estructura de los datos.
- Revisión de la calidad de la información.
- Selección de variables para los análisis.

### 📈 3. Análisis estadístico
- Estadística descriptiva.
- Media, mediana y moda.
- Varianza y desviación estándar.
- Valores mínimos y máximos.
- Cuartiles y percentiles.
- Distribuciones y frecuencias.
- Análisis de correlaciones.
- Interpretación de resultados estadísticos.

### 📊 4. Visualización de datos

La aplicación incorpora diferentes alternativas para representar e interpretar conjuntos de datos:

- Histogramas.
- Diagramas de caja (*Boxplot*).
- Gráficos de barras.
- Gráficos circulares.
- Diagramas de dispersión.
- Gráficos de líneas.
- Gráficos de densidad.
- Gráficos de violín.
- Mapas de correlación.
- Gráficos de promedios.
- Gráficos de área.
- Frecuencias acumuladas.
- Diagramas de Pareto.
- Diagramas de dispersión con tendencia.

También dispone de herramientas de navegación e interacción con los gráficos, selección de variables y paneles de estadísticas e interpretación para facilitar el análisis visual.

### 🤖 5. Modelado predictivo
- Selección de la variable objetivo.
- Selección de variables predictoras.
- Configuración del método de modelado.
- Entrenamiento de modelos predictivos.
- Evaluación del rendimiento del modelo.
- Comparación entre valores reales y estimados.
- Análisis de residuos.
- Visualización de resultados.
- Presentación de ecuaciones del modelo cuando corresponda.
- Calculadora para realizar predicciones con nuevos valores de entrada.

### 🔮 6. Pronóstico
- Análisis de tendencias temporales.
- Configuración de periodos de pronóstico.
- Generación de estimaciones futuras.
- Representación gráfica de los resultados.
- Exploración del comportamiento de las variables a través del tiempo.

### 📄 7. Generación de informes PDF
La aplicación permite generar informes con información relevante del análisis realizado, incluyendo:

- Resumen ejecutivo.
- Estructura y calidad de los datos.
- Estadísticas descriptivas.
- Análisis de variables.
- Visualizaciones.
- Interpretaciones de resultados.
- Evaluación del modelo predictivo.
- Resultados del pronóstico cuando corresponda.

---

## 🛠️ Tecnologías y herramientas

| Tecnología | Utilización |
|---|---|
| Python 3.13 | Lenguaje principal de desarrollo |
| Tkinter | Construcción de la interfaz gráfica |
| Pandas | Manipulación y análisis de datos |
| NumPy | Operaciones y cálculos numéricos |
| Matplotlib | Generación y visualización de gráficos |
| Scikit-learn | Entrenamiento y evaluación de modelos predictivos |
| OpenPyXL | Lectura de archivos Excel |
| SQLite3 | Lectura y gestión de bases de datos SQLite |
| ReportLab | Generación de informes PDF |

---

## 📋 Requisitos del sistema

Para ejecutar DataAnalyst Pro se necesita:

- Windows, Linux o macOS.
- Python 3.13 (versión utilizada durante el desarrollo).
- Pip, administrador de paquetes de Python.
- Las bibliotecas y dependencias del proyecto.
- Espacio disponible para almacenar los archivos y conjuntos de datos.

**Nota:** Tkinter y SQLite3 forman parte de las herramientas estándar de Python en las instalaciones que incluyen sus respectivos componentes. En Windows se recomienda utilizar una instalación de Python que incluya Tcl/Tk.

---

## ⚙️ Instalación y configuración

### 1. Instalar Python

Instalar Python 3.13 y verificar que esté disponible desde la terminal.

Comprobar la versión:

```bash
python --version
```

Comprobar la disponibilidad de Pip:

```bash
python -m pip --version
```

### 2. Abrir la carpeta del proyecto

Desde CMD (Símbolo del sistema de Windows), ingresar al directorio donde se encuentra el proyecto:

```bash
cd /d "RUTA_DEL_PROYECTO"
```

### 3. Actualizar Pip

Se recomienda actualizar el administrador de paquetes:

```bash
python -m pip install --upgrade pip
```

### 4. Crear un entorno virtual

Para mantener las dependencias organizadas y separadas de otras instalaciones de Python:

```bash
python -m venv .venv
```

Activar el entorno virtual:

```bash
.venv\Scripts\activate
```

### 5. Instalar las dependencias

DataAnalyst Pro utiliza las siguientes bibliotecas externas:

```bash
pip install pandas numpy matplotlib scikit-learn openpyxl reportlab
```

| Biblioteca | Función |
|---|---|
| `pandas` | Lectura, organización y procesamiento de datos. |
| `numpy` | Operaciones matemáticas y numéricas. |
| `matplotlib` | Creación de gráficos y visualizaciones. |
| `scikit-learn` | Modelos predictivos y herramientas de aprendizaje automático. |
| `openpyxl` | Lectura y procesamiento de archivos Excel. |
| `reportlab` | Creación y exportación de informes PDF. |

También es posible instalar las dependencias mediante el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 6. Ejecutar la aplicación

Una vez instaladas las dependencias, ejecutar:

```bash
python app.py
```

---

## 🔄 Flujo de trabajo

El funcionamiento general de DataAnalyst Pro se desarrolla mediante las siguientes etapas:

1. **Carga de información:** importar un archivo o una base de datos.
2. **Exploración:** examinar la estructura, los registros y las variables.
3. **Análisis estadístico:** calcular medidas y estudiar el comportamiento de los datos.
4. **Visualización:** construir gráficos para identificar patrones y relaciones.
5. **Modelado predictivo:** seleccionar variables, entrenar modelos y evaluar resultados.
6. **Pronóstico:** generar estimaciones a partir de la información temporal disponible.
7. **Generación de informes:** exportar los resultados y visualizaciones en PDF.

---

## 🎯 Objetivo del proyecto

Desarrollar una aplicación de escritorio que integre herramientas de análisis estadístico, exploración de datos, visualización y modelado predictivo, permitiendo transformar conjuntos de datos en información comprensible y útil para apoyar la toma de decisiones.

## 🔮 Mejoras futuras

- Incorporación de nuevos algoritmos de aprendizaje automático.
- Ampliación de las herramientas estadísticas.
- Nuevas alternativas de visualización.
- Compatibilidad con otros motores de bases de datos.
- Mejoras en la generación y personalización de informes.
- Optimización del procesamiento de grandes conjuntos de datos.

---

## 👨‍💻 Autor

Proyecto desarrollado con Python, orientado al análisis de datos, la estadística y el modelado predictivo.

---

**DataAnalyst Pro — De los datos a la información.**

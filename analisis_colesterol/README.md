# 🧬 Análisis Predictivo de Colesterol con R

**Proyecto de análisis estadístico y modelado predictivo utilizando R y RStudio.**

## 📌 Descripción del proyecto

Este proyecto tiene como finalidad analizar los factores relacionados con los niveles de colesterol y desarrollar un modelo predictivo que permita estimar la probabilidad de presentar colesterol alto a partir de diferentes características y hábitos de vida.

Se trabaja con un conjunto de datos sintéticos de **6.500 registros**, almacenados en un archivo Excel, para realizar análisis estadísticos, identificar posibles relaciones entre variables y aplicar técnicas de aprendizaje estadístico.

> **Nota:** Los datos son sintéticos y se utilizan exclusivamente con fines académicos y de práctica. No representan pacientes reales ni deben utilizarse para diagnósticos médicos.

## 🎯 Objetivos

- Analizar la distribución de los niveles de colesterol.
- Identificar posibles relaciones entre el colesterol y los hábitos de vida.
- Comparar los resultados según factores demográficos y familiares.
- Calcular porcentajes y estadísticas descriptivas.
- Construir un modelo de regresión logística.
- Estimar probabilidades de presentar colesterol alto.
- Evaluar el rendimiento del modelo predictivo.
- Representar los resultados mediante gráficos estadísticos.

## 📂 Estructura del proyecto

```text
Analisis-Colesterol-R/
│
├── analisis_colesterol_6500_registros.xlsx
│
├── modelo_predictivo_colesterol.R
│
├── grafico_colesterol_por_factores.png
│
└── README.md
```

## 📊 Conjunto de datos

El archivo `analisis_colesterol_6500_registros.xlsx` contiene 6.500 registros y tres hojas de trabajo:

| Hoja | Descripción |
|---|---|
| Datos | Registros utilizados para el análisis. |
| Resumen | Información estadística resumida. |
| Diccionario | Descripción de las variables. |

### Variables analizadas

- **Colesterol:** clasificación del nivel de colesterol.
- **Alimentación:** hábitos de alimentación saludable o no saludable.
- **Ejercicio:** realización de actividad física.
- **Zona:** zona de residencia.
- **Convivencia:** condición de convivencia.
- **Sexo:** clasificación de sexo registrada en los datos.
- **Antecedentes familiares:** presencia o ausencia de antecedentes familiares.
- **Tabaquismo:** condición relacionada con el consumo de tabaco.
- **Sueño:** características relacionadas con el descanso.
- **Estrés:** clasificación del nivel de estrés.
- **Edad:** edad de los registros, entre 18 y 85 años.

## 🧮 Análisis estadístico y predictivo

El proyecto incorpora diferentes procedimientos para estudiar los datos:

### 1. Análisis descriptivo

- Frecuencias y porcentajes.
- Distribución de colesterol alto y no alto.
- Comparaciones entre grupos.
- Análisis de los factores relacionados con los hábitos de vida.

### 2. Regresión logística

Se utiliza un modelo de regresión logística para estimar la probabilidad de presentar colesterol alto a partir de las variables seleccionadas.

### 3. Predicciones

El modelo permite obtener probabilidades estimadas y clasificaciones predictivas para los registros analizados.

### 4. Evaluación del modelo

Se utilizan métricas para evaluar el comportamiento del modelo:

- Matriz de confusión.
- Exactitud (*Accuracy*): proporción de predicciones correctas.
- Sensibilidad (*Sensitivity*): capacidad para identificar correctamente los casos positivos.

### 5. Visualización

Se utiliza `ggplot2` para representar gráficamente los resultados y facilitar la interpretación de las relaciones entre las variables.

## 🛠️ Tecnologías utilizadas

| Tecnología | Utilidad |
|---|---|
| R | Procesamiento y análisis estadístico. |
| RStudio | Entorno de desarrollo. |
| Excel | Almacenamiento de los registros. |
| readxl | Importación de archivos Excel. |
| ggplot2 | Construcción de gráficos estadísticos. |

## ⚙️ Instalación y ejecución

### 1. Requisitos previos

- Tener instalado R.
- Tener instalado RStudio.
- Descargar los archivos del repositorio.

### 2. Instalar las dependencias

Ejecutar en la consola de RStudio:

```r
install.packages("readxl")
install.packages("ggplot2")
```

### 3. Preparar los archivos

Descargar los archivos del proyecto y ubicarlos en una misma carpeta.

### 4. Ejecutar el programa

Abrir el archivo:

```text
modelo_predictivo_colesterol.R
```

Ejecutar el código desde RStudio.

Si el programa solicita seleccionar el archivo Excel, elegir:

```text
analisis_colesterol_6500_registros.xlsx
```

### 5. Consultar los resultados

Al ejecutar el programa se realizan los análisis estadísticos, se construye el modelo predictivo y se generan las visualizaciones y los resultados correspondientes.

El programa también contempla la exportación de las predicciones a un archivo CSV.

## 📈 Resultados esperados

El proyecto permite:

- Obtener estadísticas sobre la distribución del colesterol.
- Comparar los resultados según diferentes factores.
- Identificar patrones presentes en los datos sintéticos.
- Estimar probabilidades mediante regresión logística.
- Evaluar el rendimiento del modelo.
- Visualizar los resultados mediante gráficos.

## 📚 Aplicación académica

Este ejercicio permite poner en práctica conocimientos de:

- Estadística descriptiva e inferencial.
- Manipulación y procesamiento de datos.
- Análisis exploratorio de datos.
- Regresión logística.
- Modelos predictivos.
- Evaluación de modelos estadísticos.
- Visualización de información.

## 👨‍💻 Autor

Proyecto académico desarrollado como práctica de análisis de datos y modelado predictivo utilizando R.

---

**Tecnologías principales:** R · RStudio · Excel · Regresión logística · ggplot2.

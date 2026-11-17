# Modelo predictivo de colesterol alto (datos simulados, 6.500 registros)
# Coloca este script y el Excel en la misma carpeta y ejecuta todo el archivo.

paquetes <- c("readxl", "ggplot2", "writexl")
nuevos <- paquetes[!(paquetes %in% rownames(installed.packages()))]
if (length(nuevos) > 0) install.packages(nuevos, repos = "https://cloud.r-project.org")
library(readxl)
library(ggplot2)
library(writexl)

archivo <- "analisis_colesterol_6500_registros.xlsx"
args <- commandArgs(trailingOnly = FALSE)
f <- sub("^--file=", "", args[grep("^--file=", args)])
carpetas <- c(getwd(), if (length(f) == 1) dirname(f))
rutas <- file.path(carpetas, archivo)
ruta <- rutas[file.exists(rutas)][1]
if (is.na(ruta)) {
  message("No encontre el Excel en la carpeta actual. Seleccionalo manualmente.")
  ruta <- file.choose()
}
salida <- dirname(normalizePath(ruta))

datos <- as.data.frame(read_excel(ruta, sheet = "Datos"))

columnas_factor <- c(
  "Sexo", "Zona_residencia", "Alimentacion", "Actividad_fisica",
  "Convivencia", "Antecedentes_familiares", "Tabaquismo",
  "Calidad_sueno", "Nivel_estres", "Colesterol_alto"
)
faltantes <- setdiff(c("ID_persona", "Edad", columnas_factor), names(datos))
if (length(faltantes) > 0) {
  stop("Faltan columnas en la hoja Datos: ", paste(faltantes, collapse = ", "))
}

datos <- datos[complete.cases(datos), ]
for (v in columnas_factor) datos[[v]] <- factor(trimws(as.character(datos[[v]])))
datos$Colesterol_alto <- relevel(datos$Colesterol_alto, ref = "No")
si <- setdiff(levels(datos$Colesterol_alto), "No")[1]

cat("REGISTROS:", nrow(datos), "\n\n")
cat("Distribucion de colesterol alto (%):\n")
print(round(prop.table(table(datos$Colesterol_alto)) * 100, 2))

factores <- c(
  "Alimentacion", "Actividad_fisica", "Zona_residencia", "Convivencia",
  "Antecedentes_familiares", "Tabaquismo", "Calidad_sueno", "Nivel_estres", "Sexo"
)
for (v in factores) {
  cat("\nPorcentaje de colesterol alto segun", v, "\n")
  print(round(prop.table(table(datos[[v]], datos$Colesterol_alto), margin = 1) * 100, 2))
}

set.seed(2026)
indices <- sample(seq_len(nrow(datos)), size = floor(0.80 * nrow(datos)))
entrenamiento <- datos[indices, ]
prueba <- datos[-indices, ]

modelo <- glm(
  Colesterol_alto ~ Edad + Sexo + Zona_residencia + Alimentacion +
    Actividad_fisica + Convivencia + Antecedentes_familiares +
    Tabaquismo + Calidad_sueno + Nivel_estres,
  data = entrenamiento,
  family = binomial
)
cat("\nRESUMEN DEL MODELO\n")
print(summary(modelo))

ic <- exp(confint.default(modelo))
or_tabla <- data.frame(
  Variable = names(coef(modelo)),
  OR = exp(coef(modelo)),
  IC95_inf = ic[, 1],
  IC95_sup = ic[, 2],
  row.names = NULL
)
cat("\nODDS RATIOS\n")
print(or_tabla, digits = 3)

probabilidades <- predict(modelo, newdata = prueba, type = "response")
prediccion <- factor(ifelse(probabilidades >= 0.5, si, "No"), levels = c("No", si))

matriz <- table(Real = prueba$Colesterol_alto, Predicho = prediccion)
cat("\nMATRIZ DE CONFUSION\n")
print(matriz)

exactitud <- sum(diag(matriz)) / sum(matriz)
sensibilidad <- if (sum(matriz[si, ]) == 0) NA else matriz[si, si] / sum(matriz[si, ])
especificidad <- if (sum(matriz["No", ]) == 0) NA else matriz["No", "No"] / sum(matriz["No", ])
cat("\nExactitud:", round(exactitud * 100, 2), "%\n")
cat("Sensibilidad:", round(sensibilidad * 100, 2), "%\n")
cat("Especificidad:", round(especificidad * 100, 2), "%\n")

resumen <- do.call(rbind, lapply(factores, function(v) {
  tmp <- data.frame(
    Categoria = as.character(datos[[v]]),
    Alto = as.numeric(datos$Colesterol_alto == si),
    stringsAsFactors = FALSE
  )
  ag <- aggregate(Alto ~ Categoria, data = tmp, FUN = mean)
  data.frame(Factor = v, Categoria = ag$Categoria,
             Porcentaje = ag$Alto * 100, stringsAsFactors = FALSE)
}))

grafico <- ggplot(resumen, aes(x = Porcentaje, y = Categoria, fill = Factor)) +
  geom_col(show.legend = FALSE) +
  geom_text(aes(label = sprintf("%.1f%%", Porcentaje)), hjust = -0.1, size = 3) +
  facet_wrap(~ Factor, scales = "free_y") +
  coord_cartesian(xlim = c(0, max(resumen$Porcentaje) * 1.2)) +
  labs(
    title = "Porcentaje de colesterol alto segun factores",
    subtitle = "Datos simulados; analisis descriptivo, no diagnostico medico",
    x = "Personas con colesterol alto (%)",
    y = NULL
  ) +
  theme_minimal(base_size = 11)

print(grafico)
ggsave(file.path(salida, "plot_colesterol_factores.png"), grafico,
       width = 12, height = 9, dpi = 300)

resultados <- data.frame(
  ID_persona = prueba$ID_persona,
  Colesterol_real = as.character(prueba$Colesterol_alto),
  Probabilidad_estimada = round(as.numeric(probabilidades), 4),
  Clasificacion_modelo = as.character(prediccion),
  stringsAsFactors = FALSE
)
write.csv(resultados, file.path(salida, "predicciones_colesterol.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
write_xlsx(list(Predicciones = resultados, Odds_ratios = or_tabla),
           file.path(salida, "predicciones_colesterol.xlsx"))

cat("\nArchivos guardados en:", salida, "\n")

import os, re, sqlite3, tempfile
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage, PageBreak

class App:
    def __init__(self, root):
        self.root=root; root.title("DataAnalyst Pro"); root.geometry("1120x760")
        self.df=None; self.source=""; self.model=None; self.forecast=None; self.canvas=None; self.datasets={}; self.active_dataset=""
        top=ttk.Frame(root,padding=10); top.pack(fill="x")
        ttk.Label(top,text="DataAnalyst Pro",font=("Segoe UI",18,"bold")).pack(side="left")
        ttk.Button(top,text="Cargar Excel / CSV / SQL / SQLite",command=self.load).pack(side="left",padx=12)
        ttk.Button(top,text="Generar reporte PDF",command=self.pdf).pack(side="left")
        self.src=ttk.Label(top,text="Sin datos"); self.src.pack(side="left",padx=12)
        self.nb=ttk.Notebook(root); self.nb.pack(fill="both",expand=True,padx=10,pady=8)
        self.tdata=ttk.Frame(self.nb,padding=8); self.tstats=ttk.Frame(self.nb,padding=8)
        self.tpred=ttk.Frame(self.nb,padding=8); self.tfore=ttk.Frame(self.nb,padding=8); self.tchart=ttk.Frame(self.nb,padding=8)
        for tab,name in [(self.tdata,"Datos"),(self.tstats,"Estadística"),(self.tpred,"Predicción"),(self.tfore,"Pronóstico"),(self.tchart,"Gráficos")]: self.nb.add(tab,text=name)
        treebox=ttk.Panedwindow(self.tdata,orient="horizontal"); treebox.pack(fill="both",expand=True)
        nav=ttk.Frame(treebox); view=ttk.Frame(treebox); treebox.add(nav,weight=1); treebox.add(view,weight=4)
        ttk.Label(nav,text="Estructura del archivo",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,5))
        self.dataset_nav=ttk.Treeview(nav,show="tree",selectmode="browse"); self.dataset_nav.pack(fill="both",expand=True)
        self.dataset_nav.bind("<<TreeviewSelect>>",self.switch_dataset)
        self.tree=ttk.Treeview(view,show="headings")
        self.page_size=500; self.page_index=0
        pager=ttk.Frame(view); pager.grid(row=2,column=0,columnspan=2,sticky="ew",pady=(5,0))
        self.prev_page=ttk.Button(pager,text="◀ Anterior",command=lambda:self.show_data_page(-1)); self.prev_page.pack(side="left")
        self.page_label=ttk.Label(pager,text="Página 1"); self.page_label.pack(side="left",padx=10)
        self.next_page=ttk.Button(pager,text="Siguiente ▶",command=lambda:self.show_data_page(1)); self.next_page.pack(side="left")
        ttk.Label(pager,text="500 filas por página · el análisis utiliza todos los registros").pack(side="right")
        yscroll=ttk.Scrollbar(view,orient="vertical",command=self.tree.yview)
        xscroll=ttk.Scrollbar(view,orient="horizontal",command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set,xscrollcommand=xscroll.set)
        self.tree.grid(row=0,column=0,sticky="nsew"); yscroll.grid(row=0,column=1,sticky="ns"); xscroll.grid(row=1,column=0,sticky="ew")
        view.rowconfigure(0,weight=1); view.columnconfigure(0,weight=1)
        self.info=tk.Text(self.tdata,height=5); self.info.pack(fill="x")
        row=ttk.Frame(self.tstats); row.pack(fill="x")
        self.svar=tk.StringVar(); self.scombo=ttk.Combobox(row,textvariable=self.svar,state="readonly",width=30); self.scombo.pack(side="left")
        ttk.Button(row,text="Analizar variable",command=self.stats_one).pack(side="left",padx=5)
        ttk.Button(row,text="Resumen general",command=self.stats_all).pack(side="left")
        self.statsout=tk.Text(self.tstats,font=("Consolas",10)); self.statsout.pack(fill="both",expand=True,pady=8)
        row=ttk.Frame(self.tpred); row.pack(fill="x")
        self.target=tk.StringVar(); self.tcombo=ttk.Combobox(row,textvariable=self.target,state="readonly",width=28); self.tcombo.pack(side="left")
        self.test=tk.StringVar(value="20"); ttk.Label(row,text="Prueba %").pack(side="left",padx=(12,3)); ttk.Entry(row,textvariable=self.test,width=6).pack(side="left")
        self.pred_method=tk.StringVar(value="Regresión lineal múltiple"); ttk.Label(row,text="Método:").pack(side="left",padx=(10,3)); self.method_combo=ttk.Combobox(row,textvariable=self.pred_method,state="readonly",width=27,values=["Regresión lineal múltiple","Regresión polinómica (grado 2)","Ridge (regularizada)","Random Forest","Clasificación (Random Forest)"]); self.method_combo.pack(side="left")
        self.tcombo.bind("<<ComboboxSelected>>",self.invalidate_prediction_model)
        self.method_combo.bind("<<ComboboxSelected>>",self.invalidate_prediction_model)
        ttk.Button(row,text="Entrenar modelo",command=self.predict).pack(side="left",padx=8)
        self.pred_input=ttk.LabelFrame(self.tpred,text="Probar la ecuación / modelo con datos nuevos",padding=8); self.pred_input.pack(fill="x",pady=(6,2))
        self.pred_input_fields=ttk.Frame(self.pred_input); self.pred_input_fields.pack(fill="x")
        self.pred_input_hint=ttk.Label(self.pred_input,text="Entrena un modelo para habilitar la calculadora de nuevos casos."); self.pred_input_hint.pack(anchor="w")
        ttk.Button(self.pred_input,text="Calcular nuevo caso",command=self.predict_new_case).pack(anchor="e",pady=(4,0))
        self.predout=tk.Text(self.tpred,font=("Consolas",10)); self.predout.pack(fill="both",expand=True,pady=8)
        self.pred_entries={}; self.pred_input_button=None
        row=ttk.Frame(self.tfore); row.pack(fill="x")
        self.date=tk.StringVar(); self.value=tk.StringVar(); self.periods=tk.StringVar(value="6")
        self.dcombo=ttk.Combobox(row,textvariable=self.date,state="readonly",width=22); self.dcombo.pack(side="left")
        self.vcombo=ttk.Combobox(row,textvariable=self.value,state="readonly",width=22); self.vcombo.pack(side="left",padx=5)
        ttk.Label(row,text="Periodos").pack(side="left"); ttk.Entry(row,textvariable=self.periods,width=5).pack(side="left",padx=4)
        ttk.Button(row,text="Pronosticar",command=self.make_forecast).pack(side="left")
        self.foreout=tk.Text(self.tfore,height=9,font=("Consolas",10)); self.foreout.pack(fill="x",pady=8)
        self.foreplot=ttk.Frame(self.tfore); self.foreplot.pack(fill="both",expand=True)
        row=ttk.Frame(self.tchart); row.pack(fill="x",pady=(0,6))
        self.chart_type=tk.StringVar(value="Histograma")
        ttk.Label(row,text="Tipo de gráfico:").pack(side="left")
        self.chart_combo=ttk.Combobox(row,textvariable=self.chart_type,state="readonly",width=22,values=["Histograma","Diagrama de caja","Barras (frecuencias)","Gráfico circular","Dispersión","Líneas","Densidad","Violín","Mapa de correlación","Barras de promedio","Área","Frecuencia acumulada","Dispersión con tendencia","Pareto"])
        self.chart_combo.pack(side="left",padx=5); self.chart_combo.bind("<<ComboboxSelected>>",self.update_chart_fields)
        self.cx=tk.StringVar(); self.cy=tk.StringVar(); self.ccat=tk.StringVar()
        ttk.Label(row,text="Variable X:").pack(side="left",padx=(8,2))
        self.cxcombo=ttk.Combobox(row,textvariable=self.cx,state="readonly",width=18); self.cxcombo.pack(side="left")
        ttk.Label(row,text="Variable Y:").pack(side="left",padx=(8,2))
        self.cycombo=ttk.Combobox(row,textvariable=self.cy,state="readonly",width=18); self.cycombo.pack(side="left")
        ttk.Button(row,text="Generar gráfico",command=self.charts).pack(side="left",padx=8)
        self.chart_hint=ttk.Label(self.tchart,text="Selecciona el tipo de gráfico y las variables."); self.chart_hint.pack(anchor="w")
        # Panel dividido y ajustable: evita que el gráfico empuje las estadísticas
        # fuera del área visible cuando la ventana tiene poca altura.
        self.chart_pane=ttk.Panedwindow(self.tchart,orient="vertical")
        self.chart_pane.pack(fill="both",expand=True,pady=(4,0))
        self.chartframe=ttk.Frame(self.chart_pane)
        self.charttoolbarhost=ttk.Frame(self.chartframe)
        self.charttoolbarhost.pack(side="top",fill="x",pady=(0,3))
        self.chartcanvasframe=ttk.Frame(self.chartframe)
        self.chartcanvasframe.pack(side="top",fill="both",expand=True)
        self.chartstats=ttk.LabelFrame(self.chart_pane,text="Estadísticas e interpretación",padding=6)
        self.chart_pane.add(self.chartframe,weight=3)
        self.chart_pane.add(self.chartstats,weight=1)
        self.chartstatsout=tk.Text(self.chartstats,height=7,wrap="word")
        self.chartstatsout.pack(fill="both",expand=True)
        self.chartstatsout.insert("1.0","Aquí aparecerán las estadísticas descriptivas y la interpretación del gráfico generado.")
        # Las barras se conectan DESPUÉS de crear todos los widgets.
        # En versiones anteriores se intentaba acceder a foreout y chartstatsout
        # antes de inicializarlos, provocando un AttributeError al arrancar.
        for widget in (self.dataset_nav,self.info,self.statsout,self.predout,self.foreout,self.chartstatsout):
            self.attach_scrollbars(widget)
        self.status=tk.StringVar(value="Carga un conjunto de datos para iniciar.")
        ttk.Label(root,textvariable=self.status,relief="sunken",anchor="w").pack(fill="x",side="bottom")

    @staticmethod
    def enable_plot_zoom(canvas, ax):
        """Zoom centrado en el puntero con rueda; toolbar permite zoom por selección y paneo."""
        def on_scroll(event):
            if event.inaxes is None or event.xdata is None or event.ydata is None: return
            factor=0.8 if event.button=="up" else 1.25
            xlim=event.inaxes.get_xlim(); ylim=event.inaxes.get_ylim()
            x=event.xdata; y=event.ydata
            event.inaxes.set_xlim([x+(v-x)*factor for v in xlim])
            event.inaxes.set_ylim([y+(v-y)*factor for v in ylim])
            canvas.draw_idle()
        canvas.mpl_connect("scroll_event",on_scroll)

    def attach_scrollbars(self, widget):
        """Añade barras vertical/horizontal arrastrables sin alterar el diseño existente."""
        vertical=ttk.Scrollbar(widget.master,orient="vertical",command=widget.yview)
        horizontal=ttk.Scrollbar(widget.master,orient="horizontal",command=widget.xview)
        widget.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set)
        vertical.place(in_=widget,relx=1.0,rely=0,relheight=1.0,anchor="ne")
        horizontal.place(in_=widget,relx=0,rely=1.0,relwidth=1.0,anchor="sw")
        widget.bind("<MouseWheel>",lambda e,w=widget:w.yview_scroll(int(-1*(e.delta/120)),"units"),add="+")
        widget.bind("<Shift-MouseWheel>",lambda e,w=widget:w.xview_scroll(int(-1*(e.delta/120)),"units"),add="+")

    def invalidate_prediction_model(self, event=None):
        """Evita mostrar campos/resultados de un objetivo o método distinto al seleccionado."""
        if self.model is not None:
            self.model = None
            self.clear_prediction_inputs("Cambiaste el objetivo o el método. Entrena nuevamente para crear los campos correctos.")
            self.predout.delete("1.0", "end")
            self.status.set("Configuración predictiva modificada; vuelve a entrenar el modelo.")

    @staticmethod
    def parse_date_series(series):
        """Convierte fechas comunes, incluyendo texto día/mes/año, sin asumir formato único."""
        try:
            parsed = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)
        except (TypeError, ValueError):
            parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
        return parsed

    @classmethod
    def date_columns(cls, frame):
        """Detecta columnas que realmente contienen fechas utilizables."""
        found=[]
        for col in frame.columns:
            if pd.api.types.is_datetime64_any_dtype(frame[col]):
                parsed=cls.parse_date_series(frame[col])
            else:
                nonnull=frame[col].dropna()
                if nonnull.empty: continue
                # Evita interpretar números ordinarios como nanosegundos desde epoch.
                if pd.api.types.is_numeric_dtype(frame[col]): continue
                parsed=cls.parse_date_series(frame[col])
            valid=parsed.notna().sum()
            if valid>=3 and valid/max(1,frame[col].notna().sum())>=0.65 and parsed.nunique()>=3:
                found.append(col)
        return found

    def clear_prediction_inputs(self, message="Entrena un modelo para habilitar la calculadora de nuevos casos."):
        """Elimina los campos del modelo anterior al cambiar de datos o reiniciar el modelo."""
        for child in self.pred_input_fields.winfo_children():
            child.destroy()
        self.pred_entries = {}
        self.pred_input_hint.config(text=message)

    def build_prediction_inputs(self, X):
        """Reconstruye los controles usando exclusivamente los predictores del último modelo."""
        self.clear_prediction_inputs("Introduce un valor para cada variable predictora del modelo recién entrenado.")
        features = list(self.model.get("features", []))
        if not features:
            self.pred_input_hint.config(text="El modelo no tiene variables predictoras disponibles.")
            return
        for i, col in enumerate(features):
            if col not in X.columns:
                continue
            series = X[col].copy()
            box = ttk.Frame(self.pred_input_fields)
            box.grid(row=i // 3, column=i % 3, sticky="ew", padx=5, pady=4)
            ttk.Label(box, text=str(col), font=("Segoe UI", 9, "bold")).pack(anchor="w")
            if pd.api.types.is_numeric_dtype(series):
                clean = pd.to_numeric(series, errors="coerce").dropna()
                default = str(float(clean.median())) if not clean.empty else "0"
                var = tk.StringVar(value=default)
                control = ttk.Entry(box, textvariable=var, width=27)
                control.pack(fill="x")
                self.pred_entries[col] = {"var": var, "kind": "numeric", "series": series}
            else:
                choices = sorted(series.dropna().astype(str).unique().tolist())
                mode = series.dropna().astype(str).mode()
                default = str(mode.iloc[0]) if len(mode) else (choices[0] if choices else "")
                var = tk.StringVar(value=default)
                control = ttk.Combobox(box, textvariable=var, values=choices, width=25)
                control.pack(fill="x")
                self.pred_entries[col] = {"var": var, "kind": "category", "series": series, "choices": choices}
        for i in range(3):
            self.pred_input_fields.columnconfigure(i, weight=1)
        self.pred_input_hint.config(text=f"Modelo actual: {self.model.get('method','')} · {len(self.pred_entries)} variables de entrada. Los campos se actualizan al entrenar otro modelo.")

    def predict_new_case(self):
        if not self.model or not self.pred_entries:
            messagebox.showinfo("Calculadora predictiva", "Primero entrena un modelo con al menos una variable predictora.")
            return
        try:
            row = {}
            expected = list(self.model["features"])
            if set(self.pred_entries) != set(expected):
                raise ValueError("Los campos de entrada no corresponden al modelo actual. Vuelve a entrenar el modelo.")
            for col in expected:
                item = self.pred_entries[col]
                raw = item["var"].get().strip()
                if not raw:
                    raise ValueError(f"Ingresa un valor para '{col}'.")
                if item["kind"] == "numeric":
                    value = float(raw.replace(",", "."))
                    if not np.isfinite(value):
                        raise ValueError(f"El valor de '{col}' debe ser un número finito.")
                    row[col] = value
                else:
                    row[col] = raw
            sample = pd.DataFrame([row], columns=expected)
            result = self.model["pipeline"].predict(sample)[0]
            target = self.model["target"]
            out = ["", "=" * 72, "EVALUACIÓN DEL NUEVO CASO", f"Modelo: {self.model['method']}", "Valores ingresados:"]
            out.extend(f"  {col}: {row[col]}" for col in expected)
            out.append(f"Variable objetivo estimada ({target}): {result}")
            if self.model["type"] == "Regresión":
                ytrain = pd.to_numeric(self.model["y_train"], errors="coerce").dropna()
                if len(ytrain):
                    mean = float(ytrain.mean()); sd = float(ytrain.std())
                    out += [f"Media histórica de entrenamiento: {mean:.6g}", f"Desviación estándar: {sd:.6g}", f"Diferencia frente a la media: {float(result)-mean:+.6g}"]
                    if sd > 0:
                        z = (float(result)-mean)/sd
                        interpretation = "cerca del promedio" if abs(z) < 1 else "por encima del promedio" if z > 0 else "por debajo del promedio"
                        out += [f"Puntuación estandarizada (z): {z:.3f}", f"Interpretación: estimación {interpretation} de la distribución de entrenamiento."]
                    out.append("Nota: esta comparación es descriptiva; no constituye un intervalo de confianza.")
            else:
                model_step = self.model["pipeline"].named_steps["model"]
                classes = getattr(model_step, "classes_", None)
                if classes is not None and hasattr(self.model["pipeline"], "predict_proba"):
                    probs = self.model["pipeline"].predict_proba(sample)[0]
                    out.append("Probabilidades estimadas por categoría:")
                    out.extend(f"  {c}: {prob:.1%}" for c, prob in sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)[:10])
            self.predout.insert("end", "\n".join(out)); self.predout.see("end")
        except Exception as exc:
            messagebox.showerror("Error al calcular nuevo caso", f"{type(exc).__name__}: {exc}")

    def choose(self, items, title):
        if len(items)==1: return items[0]
        w=tk.Toplevel(self.root); w.title(title); w.transient(self.root); w.grab_set()
        v=tk.StringVar(value=items[0]); ttk.Label(w,text=title).pack(padx=12,pady=8)
        ttk.Combobox(w,textvariable=v,values=items,state="readonly",width=40).pack(padx=12)
        out={"v":None}
        ttk.Button(w,text="Aceptar",command=lambda:(out.update(v=v.get()),w.destroy())).pack(pady=10)
        self.root.wait_window(w); return out["v"]

    @staticmethod
    def split_sql_statements(sql):
        """Divide SQL respetando comillas y comentarios simples/de bloque."""
        statements=[]; buf=[]; quote=None; i=0; line_comment=False; block_comment=False
        while i < len(sql):
            ch=sql[i]; nxt=sql[i+1] if i+1 < len(sql) else ""
            if line_comment:
                if ch == "\n": line_comment=False; buf.append(ch)
                i+=1; continue
            if block_comment:
                if ch == "*" and nxt == "/": block_comment=False; i+=2
                else: i+=1
                continue
            if quote:
                buf.append(ch)
                if ch == quote:
                    if nxt == quote: buf.append(nxt); i+=2; continue
                    # Backslash escaping is common in MySQL string literals.
                    if i > 0 and sql[i-1] == "\\": i+=1; continue
                    quote=None
                i+=1; continue
            if ch == "-" and nxt == "-": line_comment=True; i+=2; continue
            if ch == "#": line_comment=True; i+=1; continue
            if ch == "/" and nxt == "*": block_comment=True; i+=2; continue
            if ch in ("'", '"', '`'):
                quote=ch; buf.append(ch); i+=1; continue
            if ch == ";":
                stmt="".join(buf).strip()
                if stmt: statements.append(stmt)
                buf=[]; i+=1; continue
            buf.append(ch); i+=1
        tail="".join(buf).strip()
        if tail: statements.append(tail)
        return statements

    @staticmethod
    def mysql_to_sqlite(statement):
        q=statement.strip()
        upper=q.upper()
        if not q or upper.startswith(("--", "#", "DELIMITER ", "CREATE DATABASE", "DROP DATABASE", "USE ", "SET ", "LOCK TABLES", "UNLOCK TABLES", "START TRANSACTION", "COMMIT", "ROLLBACK", "ALTER TABLE")):
            return None
        # Stored routines/triggers need a MySQL-compatible server and are not executable in SQLite.
        if re.match(r"(?is)^CREATE\s+(PROCEDURE|FUNCTION|TRIGGER|EVENT)\b", q): return None
        q=re.sub(r"(?is)\s+ENGINE\s*=\s*\w+", "", q)
        q=re.sub(r"(?is)\s+DEFAULT\s+CHARSET\s*=\s*[\w]+", "", q)
        q=re.sub(r"(?is)\s+COLLATE\s*=\s*[\w]+", "", q)
        q=re.sub(r"(?is)\bINT\s+PRIMARY\s+KEY\s+AUTO_INCREMENT\b", "INTEGER PRIMARY KEY AUTOINCREMENT", q)
        q=re.sub(r"(?is)\bBIGINT\s+PRIMARY\s+KEY\s+AUTO_INCREMENT\b", "INTEGER PRIMARY KEY AUTOINCREMENT", q)
        q=re.sub(r"(?is)\b(?:INT|BIGINT)\s+(?:NOT\s+NULL\s+)?AUTO_INCREMENT\b", "INTEGER", q)
        q=re.sub(r"(?is)\bAUTO_INCREMENT\b", "", q)
        q=re.sub(r"(?is)\bUNSIGNED\b", "", q)
        q=re.sub(r"(?is)\bENUM\s*\([^)]*\)", "TEXT", q)
        q=re.sub(r"(?is)\bTINYINT\b", "INTEGER", q)
        q=re.sub(r"(?is)\bMEDIUMINT\b", "INTEGER", q)
        q=re.sub(r"(?is)\bDATETIME\b", "TEXT", q)
        q=re.sub(r"(?is)\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP", "", q)
        q=re.sub(r"(?is)\s+COMMENT\s+'(?:''|[^'])*'", "", q)
        q=re.sub(r"(?is)\bINSERT\s+IGNORE\s+INTO\b", "INSERT OR IGNORE INTO", q)
        # MySQL named unique constraints are valid SQLite UNIQUE constraints without the name.
        q=re.sub(r"(?is)\bUNIQUE\s+KEY\s+[\w`]+\s*\(([^)]*)\)", r"UNIQUE (\1)", q)
        # Remove non-unique KEY/INDEX declarations from MySQL CREATE TABLE.
        q=re.sub(r"(?is),\s*(?:KEY|INDEX)\s+[`\w]+\s*\([^)]*\)", "", q)
        q=re.sub(r"(?im)^\s*(?:KEY|INDEX)\s+[`\w]+\s*\([^)]*\)\s*,?\s*$", "", q)
        q=re.sub(r",\s*\)", ")", q)
        q=q.replace("`", '"')
        return q

    def load(self):
        f=filedialog.askopenfilename(filetypes=[("Datos","*.xlsx *.xls *.csv *.sql *.db *.sqlite *.sqlite3"),("Todos","*.*")])
        if not f:return
        con=None; tmp_path=None
        try:
            ext=Path(f).suffix.lower(); loaded={}
            if ext in (".xlsx", ".xls"):
                book=pd.ExcelFile(f)
                for sh in book.sheet_names:
                    frame=pd.read_excel(f,sheet_name=sh)
                    if len(frame.columns): loaded[f"Hoja · {sh}"]=frame
            elif ext==".csv":
                csv_errors=[]; frame=None
                # Prueba codificaciones habituales y deja que pandas detecte el separador.
                for encoding in ("utf-8-sig","utf-8","cp1252","latin-1"):
                    try:
                        frame=pd.read_csv(f,sep=None,engine="python",encoding=encoding,on_bad_lines="error")
                        break
                    except Exception as exc:
                        csv_errors.append(f"{encoding}: {type(exc).__name__}: {exc}")
                if frame is None:
                    raise ValueError("No se pudo interpretar el CSV. Comprueba el delimitador, las comillas y que cada fila tenga una estructura consistente.\n\n"+"\n".join(csv_errors))
                if len(frame.columns)==1:
                    # Respaldo para archivos separados por punto y coma o tabulador.
                    for sep in (";", "\t", ",", "|"):
                        try:
                            candidate=pd.read_csv(f,sep=sep,encoding="utf-8-sig",on_bad_lines="error")
                            if len(candidate.columns)>len(frame.columns):
                                frame=candidate; break
                        except Exception:
                            continue
                loaded["CSV · Datos"]=frame
            elif ext in (".db", ".sqlite", ".sqlite3"):
                con=sqlite3.connect(f)
                tabs=pd.read_sql_query("SELECT name,type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type,name",con)
                for _,r in tabs.iterrows():
                    name=str(r['name']); safe=name.replace('"','""')
                    frame=pd.read_sql_query(f'SELECT * FROM "{safe}"',con)
                    loaded[f"{r['type'].upper()} · {name}"]=frame
            elif ext==".sql":
                sql=Path(f).read_text(encoding="utf-8-sig",errors="replace")
                statements=self.split_sql_statements(sql)
                tmp=tempfile.NamedTemporaryFile(suffix=".db",delete=False); tmp_path=tmp.name; tmp.close()
                con=sqlite3.connect(tmp_path); con.execute("PRAGMA foreign_keys=OFF")
                errors=[]; executed=0; skipped=0
                for number,statement in enumerate(statements,1):
                    converted=self.mysql_to_sqlite(statement)
                    if converted is None: skipped+=1; continue
                    try:
                        con.execute(converted); executed+=1
                    except Exception as exc:
                        # Los errores se acumulan para informar sin ocultar qué instrucción falló.
                        errors.append(f"Instrucción {number}: {str(exc)[:180]} | {statement[:130].replace(chr(10),' ')}")
                con.commit()
                tabs=pd.read_sql_query("SELECT name,type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type,name",con)
                for _,r in tabs.iterrows():
                    name=str(r['name']); safe=name.replace('"','""')
                    try: loaded[f"{r['type'].upper()} · {name}"]=pd.read_sql_query(f'SELECT * FROM "{safe}"',con)
                    except Exception as exc: errors.append(f"Lectura {name}: {exc}")
                if not loaded:
                    details="\n".join(errors[:12]) or "No se encontraron tablas importables."
                    raise ValueError("No fue posible importar tablas del SQL. Puede contener sintaxis específica de MySQL que SQLite no admite, procedimientos o comandos de administración.\n\n"+details)
                self.sql_import_note=f"SQL: {executed} instrucciones procesadas; {skipped} instrucciones no aplicables omitidas; {len(loaded)} tablas/vistas detectadas."
                if errors:
                    self.sql_import_note += f"\nAdvertencias: {len(errors)} instrucciones presentaron incompatibilidades. Las tablas que sí se importaron están disponibles.\nDetalle (primeras 5):\n" + "\n".join(errors[:5])
            else: raise ValueError("Formato no compatible.")
            loaded={k:v for k,v in loaded.items() if v is not None and len(v.columns)>0}
            if not loaded: raise ValueError("No se encontraron hojas, tablas o conjuntos con columnas.")
            self.datasets=loaded; self.source=Path(f).name
            keys=list(loaded); self.dataset_nav.delete(*self.dataset_nav.get_children())
            rootnode=self.dataset_nav.insert("","end",text=self.source,open=True,iid="__source__")
            for i,key in enumerate(keys): self.dataset_nav.insert(rootnode,"end",text=key,iid=f"dataset_{i}",values=(key,))
            self.activate_dataset(keys[0])
            first=self.dataset_nav.get_children(rootnode)[0]; self.dataset_nav.selection_set(first)
            self.status.set(f"Archivo cargado: {len(loaded)} conjunto(s) disponibles.")
        except Exception as e:
            messagebox.showerror("Error al cargar el archivo",f"{type(e).__name__}: {e}\n\nArchivo: {Path(f).name if f else 'No seleccionado'}")
            self.status.set("No se pudo cargar el archivo. Revisa el detalle del error.")
        finally:
            if con is not None: con.close()
            if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)

    def switch_dataset(self, event=None):
        selection=self.dataset_nav.selection()
        if not selection: return
        item=selection[0]
        if item=="__source__": return
        key=self.dataset_nav.item(item,"text")
        if key in self.datasets and key!=self.active_dataset: self.activate_dataset(key)

    def activate_dataset(self,key):
        self.active_dataset=key; self.df=self.datasets[key].copy(); self.model=None; self.forecast=None; self.stats_text=""; self.clear_prediction_inputs()
        df=self.df; cols=list(df.columns); nums=list(df.select_dtypes(include=np.number).columns)
        # Incluir columnas numéricas guardadas como texto cuando son convertibles.
        for c in cols:
            if c not in nums and pd.to_numeric(df[c],errors="coerce").notna().mean()>=.85: nums.append(c)
        for c,vals in [(self.scombo,cols),(self.tcombo,cols),(self.dcombo,cols),(self.vcombo,nums),(self.cxcombo,cols),(self.cycombo,nums)]: c["values"]=vals
        if cols: self.svar.set(cols[0]); self.target.set(cols[-1]); self.date.set(cols[0]); self.cx.set(cols[0])
        if nums: self.value.set(nums[0]); self.cy.set(nums[0])
        self.tree.delete(*self.tree.get_children()); self.tree["columns"]=cols
        for c in cols: self.tree.heading(c,text=str(c)); self.tree.column(c,width=140)
        self.page_index=0; self.show_data_page()
        note=getattr(self,"sql_import_note","") if self.source.lower().endswith(".sql") else ""
        self.info.delete("1.0","end"); self.info.insert("1.0",f"Archivo: {self.source}\nConjunto: {key}\nDimensiones: {df.shape[0]} filas × {df.shape[1]} columnas\nConjuntos conservados en memoria: {len(self.datasets)}\n\nTipos:\n{df.dtypes}\n\n{note}")
        self.src.config(text=f"{len(df):,} filas · {len(cols)} columnas · {len(self.datasets)} conjunto(s)")
        self.update_chart_fields()


    def show_data_page(self, delta=0):
        if self.df is None: return
        total=len(self.df); pages=max(1,(total+self.page_size-1)//self.page_size)
        self.page_index=max(0,min(self.page_index+delta,pages-1))
        self.tree.delete(*self.tree.get_children())
        start=self.page_index*self.page_size; end=min(start+self.page_size,total)
        for row in self.df.iloc[start:end].itertuples(index=False,name=None):
            self.tree.insert("","end",values=[str(x)[:100] for x in row])
        self.page_label.config(text=f"Página {self.page_index+1} de {pages} · filas {start+1 if total else 0}-{end} de {total:,}")
        self.prev_page.config(state="normal" if self.page_index>0 else "disabled")
        self.next_page.config(state="normal" if self.page_index<pages-1 else "disabled")

    def update_chart_fields(self, event=None):
        """Actualiza X/Y según el gráfico y evita que Y quede vacía."""
        kind = self.chart_type.get()
        numeric = ([c for c in self.df.columns
                    if pd.to_numeric(self.df[c], errors="coerce").notna().mean() >= .85]
                   if self.df is not None else [])
        allcols = list(self.df.columns) if self.df is not None else []
        y_required = kind in ("Dispersión", "Líneas", "Barras de promedio", "Área", "Dispersión con tendencia")

        if kind in ("Histograma", "Diagrama de caja", "Densidad", "Violín", "Frecuencia acumulada"):
            self.cxcombo["values"] = numeric
            self.cycombo["values"] = []
            if numeric and self.cx.get() not in numeric: self.cx.set(numeric[0])
            self.cy.set("")
            hint = "Este gráfico utiliza una variable numérica (X)."
        elif kind in ("Barras (frecuencias)", "Gráfico circular", "Pareto"):
            self.cxcombo["values"] = allcols
            self.cycombo["values"] = []
            if allcols and self.cx.get() not in allcols: self.cx.set(allcols[0])
            self.cy.set("")
            hint = "Selecciona una variable para contar sus frecuencias."
        elif kind == "Mapa de correlación":
            self.cxcombo["values"] = numeric
            self.cycombo["values"] = []
            if numeric and self.cx.get() not in numeric: self.cx.set(numeric[0])
            self.cy.set("")
            hint = "Se calcula con todas las variables numéricas."
        else:
            self.cxcombo["values"] = allcols
            self.cycombo["values"] = numeric
            if allcols and self.cx.get() not in allcols: self.cx.set(allcols[0])
            current_y = self.cy.get()
            if y_required and numeric:
                if current_y not in numeric or current_y == self.cx.get():
                    alternatives = [c for c in numeric if c != self.cx.get()]
                    self.cy.set(alternatives[0] if alternatives else numeric[0])
                hint = "Selecciona X e Y. Y se asigna automáticamente a una columna numérica y puedes cambiarla."
            elif y_required:
                self.cy.set("")
                hint = "Este gráfico requiere una columna Y numérica, pero no se detectaron columnas numéricas válidas."
            else:
                self.cy.set("")
                hint = "Selecciona la variable X para este tipo de gráfico."
        self.chart_hint.config(text=hint)

    def ready(self):
        if self.df is None: messagebox.showwarning("Sin datos","Carga primero un archivo."); return False
        return True

    def stats_one(self):
        if not self.ready():return
        c=self.svar.get(); s=self.df[c]; miss=s.isna().sum()
        lines=[f"ANÁLISIS: {c}","="*65,f"Registros: {len(s)}",f"Válidos: {s.notna().sum()}",f"Faltantes: {miss} ({miss/len(s)*100:.2f}%)",f"Únicos: {s.nunique()}"]
        if pd.api.types.is_numeric_dtype(s):
            x=pd.to_numeric(s,errors="coerce").dropna()
            if x.empty:
                lines += ["", "No hay valores numéricos válidos para calcular medidas."]
            else:
                lines += ["","MEDIDAS ESTADÍSTICAS",f"Media: {x.mean():.6f}",f"Mediana: {x.median():.6f}",f"Moda: {x.mode().head(5).tolist()}",f"Varianza: {x.var():.6f}",f"Desviación estándar: {x.std():.6f}",f"Mínimo: {x.min():.6f}",f"Máximo: {x.max():.6f}",f"Rango: {x.max()-x.min():.6f}",f"Q1: {x.quantile(.25):.6f}",f"Q2: {x.quantile(.5):.6f}",f"Q3: {x.quantile(.75):.6f}",f"RIC: {x.quantile(.75)-x.quantile(.25):.6f}",f"Asimetría: {x.skew():.6f}",f"Curtosis: {x.kurtosis():.6f}"]
        else:
            lines += ["","FRECUENCIAS"]+[f"{k}: {v} ({v/len(s)*100:.2f}%)" for k,v in s.astype("string").fillna("(vacío)").value_counts().head(50).items()]
        self.statsout.delete("1.0","end"); self.statsout.insert("1.0","\n".join(lines)); self.stats_text="\n".join(lines)

    def stats_all(self):
        if not self.ready():return
        d=self.df; lines=[f"RESUMEN GENERAL: {self.source}",f"Dimensiones: {d.shape}",f"Duplicados: {d.duplicated().sum()}",f"Faltantes: {d.isna().sum().sum()}",""]
        for c in d:
            s=d[c]; lines.append(f"{c} | tipo={s.dtype} | faltantes={s.isna().sum()} | únicos={s.nunique()}")
            if pd.api.types.is_numeric_dtype(s):
                lines.append(f"  media={s.mean():.4f} mediana={s.median():.4f} desv={s.std():.4f} min={s.min()} max={s.max()} Q1={s.quantile(.25):.4f} Q3={s.quantile(.75):.4f}")
            else: lines.append(f"  moda={s.mode().head(1).tolist()}")
        n=d.select_dtypes(include=np.number)
        if n.shape[1]>1: lines += ["","CORRELACIONES",n.corr().round(3).to_string()]
        self.stats_text="\n".join(lines); self.statsout.delete("1.0","end"); self.statsout.insert("1.0",self.stats_text)

    def predict(self):
        if not self.ready(): return
        # Evita conservar controles o resultados de un modelo anterior si cambia el objetivo o el método.
        self.model = None
        self.clear_prediction_inputs("Entrenando un modelo nuevo; los campos se reconstruirán con sus predictores.")
        self.predout.delete("1.0","end")
        self.status.set("Entrenando modelo; procesando todos los registros válidos...")
        self.root.update_idletasks()
        try:
            target=self.target.get(); pct=float(self.test.get())/100; method=self.pred_method.get()
            if target not in self.df: raise ValueError("Selecciona una variable objetivo válida.")
            if not .1<=pct<=.4: raise ValueError("Usa entre 10% y 40% para prueba.")
            d=self.df.dropna(subset=[target]).copy(); y=d.pop(target)
            # Normaliza columnas numéricas guardadas como texto y descarta predictores constantes.
            X=d.copy()
            for col in X.columns:
                converted=pd.to_numeric(X[col],errors="coerce")
                if converted.notna().mean()>=.85: X[col]=converted
            X=X.loc[:,X.nunique(dropna=True)>1]
            if X.empty or len(d)<12: raise ValueError("Se requieren al menos 12 filas y una variable predictora con variación.")
            classification=(method=="Clasificación (Random Forest)")
            numeric_target=pd.to_numeric(y,errors="coerce")
            is_numeric=numeric_target.notna().mean()>=.9 and not classification
            if is_numeric:
                valid=numeric_target.notna(); X=X.loc[valid]; y=numeric_target.loc[valid]
                if y.nunique()<2: raise ValueError("La variable objetivo necesita al menos dos valores distintos.")
                estimator_name=method
                if method=="Regresión lineal múltiple": estimator=LinearRegression(n_jobs=-1)
                elif method=="Regresión polinómica (grado 2)":
                    from sklearn.preprocessing import PolynomialFeatures
                    estimator=Pipeline([("poly",PolynomialFeatures(degree=2,include_bias=False)),("reg",LinearRegression(n_jobs=-1))])
                elif method=="Ridge (regularizada)":
                    from sklearn.linear_model import Ridge
                    estimator=Ridge(alpha=1.0,solver="lsqr")
                else: estimator=RandomForestRegressor(n_estimators=250,random_state=42,n_jobs=-1,max_features="sqrt")
                strat=None; model_name=estimator_name
            else:
                y=y.astype("string").fillna("(vacío)").astype(str)
                if y.nunique()<2: raise ValueError("El objetivo de clasificación necesita al menos dos categorías.")
                estimator=RandomForestClassifier(n_estimators=250,random_state=42,class_weight="balanced",n_jobs=-1,max_features="sqrt")
                model_name="Random Forest · clasificación"
                strat=y if y.value_counts().min()>=2 else None
            if len(X)<12: raise ValueError("Después de limpiar los datos quedan menos de 12 registros utilizables.")
            try:
                Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=pct,random_state=42,stratify=strat)
            except ValueError:
                # Si el tamaño de prueba no permite representar todas las clases, se usa división aleatoria.
                Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=pct,random_state=42,stratify=None)
            nums=X.select_dtypes(include=np.number).columns.tolist(); cats=[c for c in X if c not in nums]
            transformers=[]
            if nums: transformers.append(("num",Pipeline([("imp",SimpleImputer(strategy="median",keep_empty_features=True))]),nums))
            if cats: transformers.append(("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("ohe",OneHotEncoder(handle_unknown="ignore",min_frequency=2))]),cats))
            prep=ColumnTransformer(transformers,remainder="drop",sparse_threshold=.3)
            pipe=Pipeline([("prep",prep),("model",estimator)])
            pipe.fit(Xtr,ytr); pred=pipe.predict(Xte)
            equation="No existe una ecuación única interpretable: Random Forest combina múltiples árboles y reglas."; equation_terms=[]
            if is_numeric and method!="Random Forest":
                fitted=pipe.named_steps["model"]; feature_names=pipe.named_steps["prep"].get_feature_names_out()
                if method=="Regresión polinómica (grado 2)":
                    poly=fitted.named_steps["poly"]; reg=fitted.named_steps["reg"]
                    feature_names=poly.get_feature_names_out(feature_names); coef=reg.coef_; intercept=reg.intercept_
                else: coef=fitted.coef_; intercept=fitted.intercept_
                terms=[f"({float(c):+.6g}·{name})" for c,name in zip(coef,feature_names) if abs(float(c))>1e-10]
                equation=f"ŷ = {float(intercept):.6g} " + " ".join(terms[:60])
                if len(terms)>60: equation+=f" … (+{len(terms)-60} términos)"
                equation_terms=terms
            if not is_numeric:
                metrics={"Exactitud":accuracy_score(yte,pred),"Precisión ponderada":precision_score(yte,pred,average="weighted",zero_division=0),"Sensibilidad ponderada":recall_score(yte,pred,average="weighted",zero_division=0),"F1 ponderado":f1_score(yte,pred,average="weighted",zero_division=0)}; typ="Clasificación"
            else:
                metrics={"MAE":mean_absolute_error(yte,pred),"RMSE":float(np.sqrt(mean_squared_error(yte,pred))),"R²":r2_score(yte,pred) if len(yte)>1 else float("nan")}; typ="Regresión"
            self.model={"type":typ,"target":target,"metrics":metrics,"features":list(X.columns),"n":len(X),"method":model_name,"equation":equation,"pipeline":pipe,"y_train":ytr.copy(),"y_test":pd.Series(yte).reset_index(drop=True),"y_pred":pd.Series(pred).reset_index(drop=True),"X_test":Xte.reset_index(drop=True)}
            self.build_prediction_inputs(Xtr)
            out=[f"MODELO: {model_name}",f"Tipo: {typ}",f"Variable objetivo: {target}",f"Registros utilizados: {len(X):,}",f"Variables predictoras ({len(X.columns)}): {', '.join(map(str,X.columns))}","", "ECUACIÓN / REPRESENTACIÓN DEL MODELO",equation,"Los datos faltantes se imputan y las categorías se codifican automáticamente.","", "EVALUACIÓN CON DATOS DE PRUEBA"]+[f"{k}: {v:.5f}" for k,v in metrics.items()]+["", "MUESTRA (real | predicho)"]+[f"{a} | {b}" for a,b in list(zip(yte.tolist(),pred.tolist()))[:25]]
            if is_numeric and metrics.get("R²",0)<0: out += ["", "Aviso: R² negativo indica que el modelo no supera al predictor basado en la media."]
            self.predout.insert("1.0","\n".join(out)); self.status.set(f"Modelo entrenado: {len(X):,} registros; {len(X.columns)} variables.")
        except Exception as e:
            self.status.set("No se pudo entrenar el modelo.")
            messagebox.showerror("Error de predicción",f"{type(e).__name__}: {e}")

    def make_forecast(self):
        if not self.ready():return
        try:
            dc=self.date.get(); vc=self.value.get(); n=int(self.periods.get())
            if n<1 or n>120: raise ValueError("Periodos permitidos: 1 a 120.")
            w=self.df[[dc,vc]].copy(); w[dc]=pd.to_datetime(w[dc],errors="coerce"); w[vc]=pd.to_numeric(w[vc],errors="coerce")
            w=w.dropna().groupby(dc)[vc].mean().sort_index()
            if len(w)<3: raise ValueError("Se requieren al menos 3 fechas distintas con valores.")
            x=np.arange(len(w)).reshape(-1,1); reg=LinearRegression().fit(x,w.values)
            pred=reg.predict(np.arange(len(w),len(w)+n).reshape(-1,1))
            freq=pd.infer_freq(w.index)
            if freq: dates=pd.date_range(w.index[-1],periods=n+1,freq=freq)[1:]; note=f"Frecuencia inferida: {freq}"
            else:
                delta=w.index.to_series().diff().dropna().median()
                if pd.isna(delta) or delta<=pd.Timedelta(0):delta=pd.Timedelta(days=30)
                dates=[w.index[-1]+delta*(i+1) for i in range(n)]; note=f"Intervalo mediano: {delta}"
            fut=pd.DataFrame({dc:dates,"Estimación":pred})
            self.forecast={"date":dc,"value":vc,"history":w,"future":fut,"equation":f"ŷ = {reg.intercept_:.6f} + ({reg.coef_[0]:.6f} × t)","note":note}
            out=["PRONÓSTICO POR TENDENCIA LINEAL",self.forecast["equation"],"t = índice temporal desde 0",note,"","FECHA | VALOR ESTIMADO"]+[f"{r[dc]} | {r['Estimación']:.4f}" for _,r in fut.iterrows()]
            out += ["","Nota: extrapolación lineal; no incorpora automáticamente estacionalidad ni factores externos."]
            self.foreout.delete("1.0","end"); self.foreout.insert("1.0","\n".join(out))
            for wdg in self.foreplot.winfo_children():wdg.destroy()
            fig,ax=plt.subplots(figsize=(8,3.3)); ax.plot(w.index,w.values,marker="o",label="Histórico"); ax.plot(fut[dc],fut["Estimación"],"--o",label="Pronóstico"); ax.set_title(vc); ax.grid(alpha=.25); ax.legend(); fig.autofmt_xdate(); fig.tight_layout()
            can=FigureCanvasTkAgg(fig,master=self.foreplot); can.draw(); can.get_tk_widget().pack(fill="both",expand=True); NavigationToolbar2Tk(can,self.foreplot,pack_toolbar=True).update(); self.enable_plot_zoom(can,ax); plt.close(fig)
            self.status.set("Pronóstico calculado.")
        except Exception as e:messagebox.showerror("Error de pronóstico",str(e))

    def chart_interpretation(self, kind, d, xname, yname):
        """Genera una lectura contextual según el tipo de visualización producido."""
        if kind == "Mapa de correlación":
            numeric_cols=[c for c in d.columns if pd.to_numeric(d[c],errors="coerce").notna().mean()>=.85]
            nums=pd.DataFrame({c:pd.to_numeric(d[c],errors="coerce") for c in numeric_cols},index=d.index)
            if nums.shape[1]<2: return "No hay suficientes variables numéricas para interpretar correlaciones."
            corr=nums.corr(numeric_only=True); pairs=[]
            for i in range(len(corr.columns)):
                for j in range(i+1,len(corr.columns)):
                    v=corr.iloc[i,j]
                    if pd.notna(v): pairs.append((abs(float(v)),float(v),corr.columns[i],corr.columns[j]))
            if not pairs: return "No se encontraron pares con correlación calculable."
            strength,val,a,b=max(pairs)
            level="fuerte" if strength>=.7 else "moderada" if strength>=.4 else "débil"
            direction="positiva" if val>0 else "negativa" if val<0 else "nula"
            return f"La relación lineal más marcada es entre {a} y {b}: correlación {val:.3f}, {level} y {direction}. Valores cercanos a +1 indican asociación positiva y cercanos a -1 asociación negativa. Correlación no implica causalidad."
        raw=d[xname] if xname in d else pd.Series(dtype=object)
        numeric=pd.to_numeric(raw,errors="coerce").dropna()
        if kind in ("Histograma","Densidad","Violín","Diagrama de caja","Frecuencia acumulada"):
            if numeric.empty: return f"{xname}: no hay valores numéricos suficientes para una interpretación."
            med=float(numeric.median()); mean=float(numeric.mean()); skew=float(numeric.skew()) if numeric.nunique()>2 else 0.0
            shape="asimetría hacia valores altos" if skew>.5 else "asimetría hacia valores bajos" if skew<-.5 else "forma aproximadamente simétrica"
            q1=float(numeric.quantile(.25)); q3=float(numeric.quantile(.75)); iqr=q3-q1
            if kind=="Diagrama de caja":
                low=q1-1.5*iqr; high=q3+1.5*iqr; outliers=int(((numeric<low)|(numeric>high)).sum())
                return f"La mediana de {xname} es {med:.4g}; el 50% central está entre {q1:.4g} y {q3:.4g} (RIC={iqr:.4g}). Se detectan {outliers:,} posibles valores atípicos según la regla de 1.5×RIC. Estos casos conviene revisarlos, no eliminarlos automáticamente."
            if kind=="Frecuencia acumulada":
                p90=float(numeric.quantile(.90))
                return f"El gráfico muestra qué porcentaje de registros queda por debajo de cada valor. Aproximadamente el 50% no supera {med:.4g} y el 90% no supera {p90:.4g}. Es útil para localizar umbrales y percentiles."
            if kind=="Violín":
                return f"La forma del violín representa la concentración de valores: las zonas más anchas reúnen mayor densidad de observaciones. {xname} tiene mediana {med:.4g}, media {mean:.4g} y {shape}; compara anchuras para detectar concentraciones o posibles subgrupos."
            if kind=="Densidad":
                return f"La curva de densidad estima dónde se concentran los valores de {xname}. La media es {mean:.4g}, la mediana {med:.4g} y la distribución presenta {shape}. Varios picos pueden sugerir subgrupos; no prueban por sí solos que existan poblaciones distintas."
            return f"El histograma resume la frecuencia de los valores de {xname}. Presenta {shape}; la media es {mean:.4g}, la mediana {med:.4g} y el 50% central se encuentra entre {q1:.4g} y {q3:.4g}. Revisa colas y picos para identificar dispersión o posibles valores extremos."
        if kind in ("Barras (frecuencias)","Gráfico circular","Pareto"):
            counts=raw.astype("string").fillna("(vacío)").value_counts()
            if counts.empty: return "No hay categorías válidas para interpretar."
            top=str(counts.index[0]); pct=float(counts.iloc[0]/counts.sum()*100)
            cumulative=float(counts.iloc[:min(3,len(counts))].sum()/counts.sum()*100)
            if kind=="Pareto": return f"La categoría {top} es la más frecuente ({pct:.1f}%). Las tres categorías principales acumulan {cumulative:.1f}% de los registros representados; esto ayuda a priorizar las categorías de mayor presencia."
            return f"La categoría más frecuente es {top}, con {int(counts.iloc[0]):,} registros ({pct:.1f}%). La visualización compara la participación de las categorías; las menos frecuentes tienen menor presencia en el conjunto."
        if kind in ("Dispersión","Dispersión con tendencia","Líneas","Barras de promedio","Área") and xname in d and yname in d:
            if kind=="Barras de promedio":
                z=d.groupby(xname,dropna=False)[yname].apply(lambda v:pd.to_numeric(v,errors="coerce").mean()).dropna()
                if z.empty: return "No hay promedios disponibles para comparar."
                return f"El promedio más alto de {yname} corresponde a {z.idxmax()} ({z.max():.4g}) y el más bajo a {z.idxmin()} ({z.min():.4g}). La diferencia entre grupos es {z.max()-z.min():.4g}."
            xx=pd.to_numeric(d[xname],errors="coerce") if pd.api.types.is_numeric_dtype(d[xname]) else d[xname].astype("category").cat.codes.replace(-1,np.nan)
            yy=pd.to_numeric(d[yname],errors="coerce"); z=pd.DataFrame({"x":xx,"y":yy}).dropna()
            if len(z)>=3 and z.x.nunique()>1 and z.y.nunique()>1:
                r=float(z.x.corr(z.y)); level="fuerte" if abs(r)>=.7 else "moderada" if abs(r)>=.4 else "débil"; direction="positiva" if r>0 else "negativa"
                return f"Entre {xname} y {yname} se observa una asociación lineal {level} {direction} (r={r:.3f}, n={len(z):,}). {('Al aumentar X, Y tiende a aumentar.' if r>0 else 'Al aumentar X, Y tiende a disminuir.') if r!=0 else 'No se aprecia dirección lineal.'} La asociación no demuestra causalidad."
            return "El gráfico permite observar patrones y cambios, pero no hay suficientes pares numéricos distintos para cuantificar la relación."
        return "Interpreta la forma, concentración, dispersión y posibles valores atípicos observando los ejes y las categorías representadas."

    def charts(self):
        if not self.ready():return
        kind=self.chart_type.get(); xname=self.cx.get(); yname=self.cy.get()
        for w in self.chartcanvasframe.winfo_children():w.destroy()
        for w in self.charttoolbarhost.winfo_children():w.destroy()
        try:
            fig,ax=plt.subplots(figsize=(9,5))
            d=self.df
            if kind=="Histograma":
                x=pd.to_numeric(d[xname],errors="coerce").dropna()
                if x.empty:raise ValueError("La variable no contiene valores numéricos válidos.")
                ax.hist(x,bins="auto",edgecolor="black"); ax.set_xlabel(xname); ax.set_ylabel("Frecuencia")
            elif kind=="Diagrama de caja":
                x=pd.to_numeric(d[xname],errors="coerce").dropna()
                if x.empty:raise ValueError("La variable no contiene valores numéricos válidos.")
                ax.boxplot(x,vert=True); ax.set_ylabel(xname)
            elif kind=="Barras (frecuencias)":
                counts=d[xname].astype("string").fillna("(vacío)").value_counts().head(25)
                if counts.empty:raise ValueError("No hay categorías para representar.")
                counts.sort_values().plot(kind="barh",ax=ax); ax.set_xlabel("Frecuencia"); ax.set_ylabel(xname)
            elif kind=="Gráfico circular":
                counts=d[xname].astype("string").fillna("(vacío)").value_counts().head(10)
                if counts.empty:raise ValueError("No hay categorías para representar.")
                ax.pie(counts.values,labels=counts.index,autopct="%1.1f%%",startangle=90); ax.axis("equal")
            elif kind in ("Dispersión","Líneas"):
                if not xname or not yname:raise ValueError("Selecciona las variables X e Y. Y se completa automáticamente si hay una columna numérica válida.")
                if kind=="Dispersión":
                    x=pd.to_numeric(d[xname],errors="coerce") if pd.api.types.is_numeric_dtype(d[xname]) else d[xname].astype("category").cat.codes.replace(-1,np.nan)
                    y=pd.to_numeric(d[yname],errors="coerce")
                    z=pd.DataFrame({"x":x,"y":y}).dropna()
                    if z.empty:raise ValueError("No hay pares válidos para graficar.")
                    ax.scatter(z.x,z.y,alpha=.65); ax.set_xlabel(xname); ax.set_ylabel(yname)
                else:
                    y=pd.to_numeric(d[yname],errors="coerce")
                    if pd.api.types.is_datetime64_any_dtype(d[xname]): x=pd.to_datetime(d[xname],errors="coerce")
                    else: x=d[xname]
                    z=pd.DataFrame({"x":x,"y":y}).dropna().sort_values("x")
                    if z.empty:raise ValueError("No hay pares válidos para graficar.")
                    ax.plot(z.x,z.y,marker="o",linewidth=1.5); ax.set_xlabel(xname); ax.set_ylabel(yname); fig.autofmt_xdate()
            elif kind=="Densidad":
                x=pd.to_numeric(d[xname],errors="coerce").dropna()
                if len(x)<2 or x.nunique()<2:raise ValueError("Se necesitan al menos dos valores numéricos distintos.")
                x.plot(kind="kde",ax=ax); ax.set_xlabel(xname); ax.set_ylabel("Densidad")
            elif kind=="Violín":
                x=pd.to_numeric(d[xname],errors="coerce").dropna()
                if x.empty:raise ValueError("La variable no contiene valores numéricos válidos.")
                ax.violinplot(x,showmeans=True,showmedians=True); ax.set_ylabel(xname)
            elif kind=="Mapa de correlación":
                numeric_cols=[c for c in d.columns if pd.to_numeric(d[c],errors="coerce").notna().mean()>=.85]
                nums=pd.DataFrame({c:pd.to_numeric(d[c],errors="coerce") for c in numeric_cols},index=d.index)
                if nums.shape[1]<2:raise ValueError("Se necesitan al menos dos columnas numéricas.")
                corr=nums.corr(numeric_only=True); im=ax.imshow(corr.values,vmin=-1,vmax=1,aspect="auto",cmap="coolwarm")
                ax.set_xticks(range(len(corr.columns))); ax.set_xticklabels(corr.columns,rotation=45,ha="right")
                ax.set_yticks(range(len(corr.index))); ax.set_yticklabels(corr.index)
                for i in range(len(corr.index)):
                    for j in range(len(corr.columns)):
                        val=corr.iloc[i,j]
                        if pd.notna(val):ax.text(j,i,f"{val:.2f}",ha="center",va="center",fontsize=8)
                fig.colorbar(im,ax=ax,label="Correlación")
            elif kind=="Barras de promedio":
                if not yname: raise ValueError("Selecciona una variable numérica Y.")
                z=d.groupby(xname,dropna=False)[yname].apply(lambda v:pd.to_numeric(v,errors="coerce").mean()).dropna().sort_values(ascending=False).head(25)
                if z.empty: raise ValueError("No hay promedios válidos para representar.")
                z.sort_values().plot(kind="barh",ax=ax); ax.set_xlabel(f"Promedio de {yname}"); ax.set_ylabel(xname)
            elif kind=="Área":
                if not yname: raise ValueError("Selecciona una variable numérica Y.")
                z=pd.DataFrame({"x":d[xname],"y":pd.to_numeric(d[yname],errors="coerce")}).dropna().sort_values("x")
                if z.empty: raise ValueError("No hay pares válidos para el área.")
                ax.fill_between(range(len(z)),z.y.to_numpy(),alpha=.35); ax.plot(range(len(z)),z.y.to_numpy()); ax.set_xlabel(xname); ax.set_ylabel(yname)
            elif kind=="Frecuencia acumulada":
                x=pd.to_numeric(d[xname],errors="coerce").dropna().sort_values()
                if x.empty: raise ValueError("No hay valores numéricos válidos.")
                ax.plot(x,np.arange(1,len(x)+1)/len(x)*100); ax.set_xlabel(xname); ax.set_ylabel("Frecuencia acumulada (%)"); ax.set_ylim(0,100)
            elif kind=="Dispersión con tendencia":
                if not yname: raise ValueError("Selecciona variable Y numérica.")
                xx=pd.to_numeric(d[xname],errors="coerce") if pd.api.types.is_numeric_dtype(d[xname]) else d[xname].astype("category").cat.codes.replace(-1,np.nan)
                yy=pd.to_numeric(d[yname],errors="coerce"); z=pd.DataFrame({"x":xx,"y":yy}).dropna()
                if len(z)<2: raise ValueError("Se requieren al menos dos pares numéricos.")
                ax.scatter(z.x,z.y,alpha=.55); co=np.polyfit(z.x,z.y,1); grid=np.linspace(z.x.min(),z.x.max(),100); ax.plot(grid,np.polyval(co,grid),linewidth=2); ax.set_xlabel(xname); ax.set_ylabel(yname)
            elif kind=="Pareto":
                counts=d[xname].astype("string").fillna("(vacío)").value_counts().head(25); cum=counts.cumsum()/counts.sum()*100
                if counts.empty: raise ValueError("No hay categorías para Pareto.")
                ax.bar(range(len(counts)),counts.values); ax.set_xticks(range(len(counts))); ax.set_xticklabels(counts.index,rotation=45,ha="right"); ax.set_ylabel("Frecuencia"); ax2=ax.twinx(); ax2.plot(range(len(cum)),cum.values,marker="o"); ax2.set_ylabel("Porcentaje acumulado")
            ax.set_title(kind); ax.grid(alpha=.22) if kind not in ("Gráfico circular","Mapa de correlación") else None
            fig.tight_layout()
            can=FigureCanvasTkAgg(fig,master=self.chartcanvasframe)
            can.draw()
            can.get_tk_widget().pack(fill="both",expand=True)
            toolbar=NavigationToolbar2Tk(can,self.charttoolbarhost,pack_toolbar=False)
            toolbar.update()
            toolbar.pack(side="left",fill="x")
            self.chart_canvas=can
            self.chart_toolbar=toolbar
            self.enable_plot_zoom(can,ax)
            plt.close(fig)
            # Resumen estadístico e interpretación contextual de las variables utilizadas.
            summary=[f"Gráfico: {kind}",f"Conjunto: {self.active_dataset}",f"Registros del conjunto: {len(d):,}"]
            chosen=[c for c in (xname,yname) if c and c in d.columns]
            for col in dict.fromkeys(chosen):
                raw=d[col]; num=pd.to_numeric(raw,errors="coerce"); valid=num.dropna()
                summary.append(f"\n{col}: válidos={raw.notna().sum():,}; faltantes={raw.isna().sum():,}; únicos={raw.nunique(dropna=True):,}")
                if len(valid):
                    summary.append(f"Media={valid.mean():.4g} | mediana={valid.median():.4g} | desviación={valid.std():.4g} | mínimo={valid.min():.4g} | máximo={valid.max():.4g}")
                    if valid.nunique()>1:
                        skew=valid.skew(); desc="asimetría positiva (cola hacia valores altos)" if skew>.5 else "asimetría negativa (cola hacia valores bajos)" if skew<-.5 else "distribución aproximadamente simétrica"
                        summary.append(f"Interpretación: {desc}; la desviación estándar resume la dispersión respecto a la media.")
                else:
                    top=raw.astype("string").fillna("(vacío)").value_counts().head(5)
                    if len(top):
                        share=top.iloc[0]/max(1,raw.notna().sum())*100
                        summary.append("Categorías más frecuentes: " + ", ".join(f"{k} ({v})" for k,v in top.items()))
                        summary.append(f"Interpretación: la categoría más frecuente representa aproximadamente {share:.1f}% de los registros no vacíos.")
            if xname in d.columns and yname in d.columns and xname!=yname:
                xx=pd.to_numeric(d[xname],errors="coerce"); yy=pd.to_numeric(d[yname],errors="coerce"); pair=pd.concat([xx,yy],axis=1).dropna()
                if len(pair)>=3 and pair.iloc[:,0].nunique()>1 and pair.iloc[:,1].nunique()>1:
                    corr=pair.iloc[:,0].corr(pair.iloc[:,1]); strength="fuerte" if abs(corr)>=.7 else "moderada" if abs(corr)>=.4 else "débil"
                    direction="positiva" if corr>0 else "negativa"
                    summary.append(f"\nRelación X–Y: correlación de Pearson={corr:.3f} ({strength} {direction}, n={len(pair):,}). Esto describe asociación, no demuestra causalidad.")
            summary += ["", "INTERPRETACIÓN DEL GRÁFICO", self.chart_interpretation(kind,d,xname,yname)]
            self.chartstatsout.delete("1.0","end"); self.chartstatsout.insert("1.0","\n".join(summary))
            self.status.set(f"Gráfico generado: {kind}; estadísticas calculadas con los datos disponibles.")
        except Exception as e:
            plt.close("all"); messagebox.showerror("Error de gráfico",str(e))

    def pdf(self):
        if not self.ready():
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Informe_DataAnalyst_Pro.pdf", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        temp_images = []
        try:
            from xml.sax.saxutils import escape
            styles = getSampleStyleSheet()
            styles["BodyText"].leading = 12
            d = self.df.copy()
            story = [
                Paragraph("DataAnalyst Pro", styles["Title"]),
                Paragraph("Informe integral de análisis de datos", styles["Heading2"]),
                Paragraph(f"Generado: {datetime.now():%Y-%m-%d %H:%M}", styles["Normal"]),
                Paragraph(f"Archivo / conjunto: {escape(str(self.source))}", styles["Normal"]),
                Spacer(1, 12),
                Paragraph("Resumen ejecutivo", styles["Heading1"]),
                Paragraph(f"El conjunto analizado contiene {len(d):,} registros y {len(d.columns):,} variables. Se detectaron {int(d.duplicated().sum()):,} filas duplicadas y {int(d.isna().sum().sum()):,} celdas vacías.", styles["BodyText"]),
                Spacer(1, 8)
            ]
            summary = [["Indicador", "Resultado"], ["Registros", f"{len(d):,}"], ["Variables", str(len(d.columns))], ["Duplicados", f"{int(d.duplicated().sum()):,}"], ["Celdas faltantes", f"{int(d.isna().sum().sum()):,}"], ["Memoria aproximada", f"{d.memory_usage(deep=True).sum()/1024**2:.2f} MB"]]
            story += [self.table(summary), Spacer(1, 12), Paragraph("1. Calidad y estructura de los datos", styles["Heading1"])]
            quality = [["Variable", "Tipo", "No vacíos", "Faltantes", "% faltantes", "Únicos"]]
            for col in d.columns:
                miss = int(d[col].isna().sum())
                quality.append([str(col)[:28], str(d[col].dtype), f"{d[col].notna().sum():,}", f"{miss:,}", f"{miss/max(1,len(d))*100:.1f}%", f"{d[col].nunique(dropna=True):,}"])
            story.append(self.table(quality, fs=7))
            missing = d.isna().sum().sort_values(ascending=False)
            if (missing > 0).any():
                fig, ax = plt.subplots(figsize=(8, 3.5))
                top = missing[missing > 0].head(20).sort_values()
                ax.barh([str(x)[:24] for x in top.index], top.values)
                ax.set_title("Valores faltantes por variable (máximo 20)"); ax.set_xlabel("Cantidad de celdas vacías"); fig.tight_layout()
                img = Path(tempfile.gettempdir()) / f"da_missing_{os.getpid()}.png"; fig.savefig(img, dpi=150); plt.close(fig); temp_images.append(img)
                story += [Spacer(1, 8), PDFImage(str(img), width=16*cm, height=7*cm), Paragraph("Interpretación: las barras más largas identifican las variables con mayor cantidad de datos faltantes. Conviene revisar su impacto antes de entrenar modelos o comparar resultados.", styles["BodyText"])]
            story += [PageBreak(), Paragraph("2. Estadística descriptiva", styles["Heading1"])]
            try:
                desc = d.describe(include="all", datetime_is_numeric=True).transpose().reset_index()
            except TypeError:
                desc = d.describe(include="all").transpose().reset_index()
            desc_data = [["Variable"] + [str(c)[:16] for c in desc.columns[1:]]]
            for _, r in desc.iterrows():
                vals = []
                for v in r.tolist():
                    if pd.isna(v): vals.append("—")
                    elif isinstance(v, (float, np.floating)): vals.append(f"{v:.4g}")
                    else: vals.append(str(v)[:28])
                desc_data.append(vals)
            story.append(self.table(desc_data, fs=6))
            nums = d.select_dtypes(include=np.number)
            if not nums.empty:
                story += [Spacer(1, 12), Paragraph("3. Distribuciones de variables numéricas", styles["Heading1"])]
                selected = list(nums.columns[:6])
                for col in selected:
                    values = pd.to_numeric(nums[col], errors="coerce").dropna()
                    if values.empty: continue
                    fig, ax = plt.subplots(figsize=(7, 2.7))
                    ax.hist(values, bins="auto", edgecolor="black", alpha=.8)
                    ax.set_title(f"Distribución: {str(col)[:60]}"); ax.set_xlabel(str(col)); ax.set_ylabel("Frecuencia"); ax.grid(axis="y", alpha=.2); fig.tight_layout()
                    img = Path(tempfile.gettempdir()) / f"da_hist_{len(temp_images)}_{os.getpid()}.png"; fig.savefig(img, dpi=135); plt.close(fig); temp_images.append(img)
                    story += [PDFImage(str(img), width=15.5*cm, height=6*cm), Paragraph(f"Interpretación: el histograma de {escape(str(col))} muestra la concentración y dispersión de los valores. Una cola prolongada indica asimetría; varios picos pueden sugerir subgrupos en los datos.", styles["BodyText"])]
                if len(nums.columns) >= 2:
                    corr = nums.corr(numeric_only=True)
                    if not corr.empty:
                        fig, ax = plt.subplots(figsize=(7, 5.2))
                        im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
                        ax.set_xticks(range(len(corr.columns))); ax.set_xticklabels([str(c)[:16] for c in corr.columns], rotation=55, ha="right", fontsize=7)
                        ax.set_yticks(range(len(corr.index))); ax.set_yticklabels([str(c)[:20] for c in corr.index], fontsize=7)
                        ax.set_title("Mapa de correlaciones de Pearson")
                        if len(corr.columns) <= 18:
                            for i in range(len(corr.index)):
                                for j in range(len(corr.columns)):
                                    if pd.notna(corr.iloc[i,j]): ax.text(j,i,f"{corr.iloc[i,j]:.2f}",ha="center",va="center",fontsize=6)
                        fig.colorbar(im, ax=ax, label="Correlación"); fig.tight_layout()
                        img = Path(tempfile.gettempdir()) / f"da_corr_{os.getpid()}.png"; fig.savefig(img, dpi=150); plt.close(fig); temp_images.append(img)
                        story += [Spacer(1, 8), PDFImage(str(img), width=15.5*cm, height=11.5*cm), Paragraph("Interpretación: los coeficientes próximos a +1 reflejan asociación lineal positiva; próximos a -1, asociación negativa; y cercanos a 0, asociación lineal débil. No implican causalidad.", styles["BodyText"])]
                        corr_rows = [["Variable X", "Variable Y", "Correlación"]]
                        pairs = []
                        for i in range(len(corr.columns)):
                            for j in range(i+1, len(corr.columns)):
                                val = corr.iloc[i,j]
                                if pd.notna(val): pairs.append((abs(float(val)), str(corr.columns[i]), str(corr.columns[j]), float(val)))
                        for _, a, b, val in sorted(pairs, reverse=True)[:12]: corr_rows.append([a[:30], b[:30], f"{val:.3f}"])
                        if len(corr_rows)>1: story += [Paragraph("Relaciones lineales más destacadas", styles["Heading2"]), self.table(corr_rows, fs=7)]
            # Variables categóricas: frecuencias principales
            cats = [c for c in d.columns if c not in nums.columns]
            if cats:
                story += [PageBreak(), Paragraph("4. Variables categóricas", styles["Heading1"])]
                for col in cats[:8]:
                    counts = d[col].astype("string").fillna("(vacío)").value_counts().head(10)
                    rows = [[str(col)[:45], "Frecuencia"]] + [[str(k)[:55], f"{int(v):,}"] for k,v in counts.items()]
                    story += [self.table(rows, fs=7), Spacer(1, 7)]
            if self.model:
                m = self.model
                story += [PageBreak(), Paragraph("5. Modelo predictivo", styles["Heading1"]),
                          Paragraph(f"Tipo: {escape(str(m['type']))} · Método: {escape(str(m.get('method','N/D')))}", styles["BodyText"]),
                          Paragraph(f"Variable objetivo: {escape(str(m['target']))}", styles["BodyText"]),
                          Paragraph(f"Predictores ({len(m['features'])}): {escape(', '.join(map(str,m['features'])))}", styles["BodyText"]),
                          Paragraph(f"Registros usados: {m['n']:,}", styles["BodyText"]), Spacer(1, 6),
                          Paragraph("Ecuación o representación del modelo", styles["Heading2"]),
                          Paragraph(escape(str(m.get("equation", "No disponible"))).replace("·", "&#183;"), styles["BodyText"])]
                metric_rows = [["Métrica", "Resultado"]] + [[str(k), f"{v:.5f}" if isinstance(v,(int,float,np.number)) and np.isfinite(v) else str(v)] for k,v in m["metrics"].items()]
                story += [Spacer(1, 6), self.table(metric_rows)]
                if m["type"] == "Regresión":
                    actual = pd.to_numeric(m.get("y_test", pd.Series(dtype=float)), errors="coerce")
                    predicted = pd.to_numeric(m.get("y_pred", pd.Series(dtype=float)), errors="coerce")
                    pair = pd.DataFrame({"real":actual, "estimado":predicted}).dropna()
                    if not pair.empty:
                        fig, ax = plt.subplots(figsize=(6.8, 4.2)); ax.scatter(pair.real, pair.estimado, alpha=.65)
                        lo=min(pair.min().min(), pair.max().min()); hi=max(pair.max().max(), pair.min().max())
                        ax.plot([lo,hi],[lo,hi],"--",label="Estimación ideal"); ax.set_xlabel("Valor real"); ax.set_ylabel("Valor estimado"); ax.set_title("Valores reales frente a predicciones"); ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
                        img=Path(tempfile.gettempdir())/f"da_model_{os.getpid()}.png"; fig.savefig(img,dpi=145); plt.close(fig); temp_images.append(img)
                        story += [Spacer(1, 8), PDFImage(str(img), width=14.5*cm, height=9*cm), Paragraph("Interpretación: los puntos cercanos a la diagonal representan estimaciones próximas a los valores reales. Separaciones grandes indican errores de predicción más altos.", styles["BodyText"])]
                        residual = pair.real-pair.estimado
                        fig, ax = plt.subplots(figsize=(6.8, 3.5)); ax.hist(residual,bins="auto",edgecolor="black"); ax.set_title("Distribución de residuos (real − estimado)"); ax.set_xlabel("Residuo"); ax.set_ylabel("Frecuencia"); fig.tight_layout()
                        img=Path(tempfile.gettempdir())/f"da_resid_{os.getpid()}.png"; fig.savefig(img,dpi=140); plt.close(fig); temp_images.append(img)
                        story += [PDFImage(str(img), width=14.5*cm, height=7.5*cm), Paragraph("Interpretación: residuos centrados alrededor de cero y sin asimetrías marcadas son una señal descriptiva favorable. Colas amplias o sesgo pueden indicar errores sistemáticos o casos difíciles de estimar.", styles["BodyText"])]
                story.append(Paragraph("La evaluación se calcula sobre el conjunto de prueba separado del entrenamiento. Las métricas describen el desempeño en esos datos y no garantizan el mismo resultado en datos futuros.", styles["BodyText"]))
            else:
                story += [PageBreak(), Paragraph("5. Modelo predictivo", styles["Heading1"]), Paragraph("No se entrenó un modelo predictivo durante esta sesión.", styles["BodyText"])]
            if self.forecast:
                f=self.forecast
                story += [PageBreak(), Paragraph("6. Pronóstico", styles["Heading1"]), Paragraph(escape(str(f["equation"])), styles["BodyText"]), Paragraph(escape(str(f["note"])), styles["BodyText"])]
                fut_rows=[["Fecha", "Estimación"]]+[[str(r[f["date"]])[:24], f"{r['Estimación']:.5g}"] for _,r in f["future"].iterrows()]
                story.append(self.table(fut_rows))
                fig,ax=plt.subplots(figsize=(7,3.5)); ax.plot(f["history"].index,f["history"].values,label="Histórico"); ax.plot(f["future"][f["date"]],f["future"]["Estimación"],"--o",label="Pronóstico"); ax.set_title("Serie histórica y valores pronosticados"); ax.set_ylabel(str(f["value"])); ax.legend(); ax.grid(alpha=.2); fig.autofmt_xdate(); fig.tight_layout()
                img=Path(tempfile.gettempdir())/f"da_forecast_{os.getpid()}.png"; fig.savefig(img,dpi=145); plt.close(fig); temp_images.append(img)
                story += [PDFImage(str(img), width=15.5*cm, height=8*cm), Paragraph(f"Interpretación: la tendencia estimada es {escape(str(f.get('trend','no determinada')))}. La pendiente representa el cambio medio estimado por periodo; la proyección supone que la tendencia histórica continúa y no incorpora automáticamente estacionalidad ni eventos externos.", styles["BodyText"])]
            else:
                story += [Spacer(1, 8), Paragraph("6. Pronóstico", styles["Heading1"]), Paragraph("No se calculó un pronóstico durante esta sesión.", styles["BodyText"])]
            story += [Spacer(1, 12), Paragraph("7. Interpretación y limitaciones", styles["Heading1"]), Paragraph("Las estadísticas describen los datos cargados. La correlación mide asociación lineal y no demuestra causalidad. Los gráficos de distribución muestran hasta seis variables numéricas y los resúmenes categóricos hasta ocho variables para mantener el informe legible. Las predicciones son estimaciones dependientes de la calidad, representatividad y características de los datos; no deben interpretarse como certezas.", styles["BodyText"])]
            doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=1.35*cm, leftMargin=1.35*cm, topMargin=1.5*cm, bottomMargin=1.5*cm, title="Informe DataAnalyst Pro", author="DataAnalyst Pro")
            doc.build(story)
            messagebox.showinfo("PDF creado", f"Informe integral guardado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error PDF", f"{type(e).__name__}: {e}")
        finally:
            for img in temp_images:
                try: img.unlink(missing_ok=True)
                except Exception: pass

    @staticmethod
    def table(data, fs=8):
        from xml.sax.saxutils import escape
        from reportlab.lib.styles import ParagraphStyle
        rows = []
        cell_style = ParagraphStyle("TableCell", fontName="Helvetica", fontSize=fs, leading=fs+2, wordWrap="CJK")
        header_style = ParagraphStyle("TableHeader", parent=cell_style, fontName="Helvetica-Bold", textColor=colors.white)
        for ri, row in enumerate(data):
            converted = []
            for value in row:
                if isinstance(value, (int, float, np.number)):
                    value = str(value)
                elif value is None:
                    value = "—"
                converted.append(Paragraph(escape(str(value)), header_style if ri == 0 else cell_style))
            rows.append(converted)
        ncols = max(1, max((len(r) for r in rows), default=1))
        # Ancho útil A4 con márgenes laterales de 1.35 cm; permite ajustar tablas anchas.
        widths = [18.3*cm/ncols] * ncols
        t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#174A70")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.3,colors.grey),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#EEF3F7")]),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
        return t

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()

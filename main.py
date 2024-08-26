import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os

def resource_path(relative_path):
    """Obtenha o caminho absoluto do recurso, seja no diretório de desenvolvimento ou no executável."""
    try:
        # Para o ambiente de desenvolvimento e PyInstaller
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    except Exception as e:
        print(f"Erro ao obter o caminho do recurso: {e}")
        return relative_path

# Definição dos meses
months = {
    "Janeiro": "01",
    "Fevereiro": "02",
    "Março": "03",
    "Abril": "04",
    "Maio": "05",
    "Junho": "06",
    "Julho": "07",
    "Agosto": "08",
    "Setembro": "09",
    "Outubro": "10",
    "Novembro": "11",
    "Dezembro": "12"
}

# Funções
def create_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            date TEXT NOT NULL,
            hour TEXT NOT NULL,
            pressure TEXT NOT NULL,
            glucose TEXT NOT NULL
        )
    ''')
    conn.commit()
    
    # Verifique se a tabela foi criada corretamente
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records';")
    table_exists = cursor.fetchone()
    if table_exists:
        print("Tabela 'records' criada com sucesso!")
    else:
        print("Erro: Tabela 'records' não foi criada.")
    
    conn.close()

def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return ""

def add_record():
    name = name_entry.get()
    age = age_entry.get()
    pressure = pressure_entry.get()
    glucose = glucose_entry.get()

    # Preenche automaticamente a data e a hora atuais
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H:%M")

    if not name or not age or not pressure or not glucose:
        messagebox.showwarning("Warning", "All fields except Date and Time are required")
        return

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO records (name, age, date, hour, pressure, glucose) VALUES (?, ?, ?, ?, ?, ?)",
                   (name, age, date, hour, pressure, glucose))
    conn.commit()
    conn.close()

    name_entry.delete(0, tk.END)
    age_entry.delete(0, tk.END)
    pressure_entry.delete(0, tk.END)
    glucose_entry.delete(0, tk.END)

    update_table()

def update_table():
    for item in table.get_children():
        table.delete(item)

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM records WHERE 1=1"
    params = []
    
    name_filter = name_filter_var.get()
    period_filter = period_filter_var.get()

    if name_filter:
        query += " AND name LIKE ?"
        params.append(f"%{name_filter}%")
    
    if period_filter == "Todo Período":
        # No additional filter
        pass
    elif period_filter in months:
        month_number = months[period_filter]
        query += " AND strftime('%m', date) = ?"
        params.append(month_number)
    else:
        messagebox.showwarning("Warning", "Invalid period filter")
        return

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        table.insert("", tk.END, iid=row[0], values=(row[1], row[2], format_date(row[3]), row[4], row[5], row[6]))  # Exclui ID

def edit_record():
    selected_item = table.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No record selected")
        return

    item_id = selected_item[0]
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records WHERE id=?", (item_id,))
    record = cursor.fetchone()
    conn.close()

    if not record:
        messagebox.showwarning("Warning", "Record not found")
        return

    global editing_item
    editing_item = item_id
    name_entry.delete(0, tk.END)
    age_entry.delete(0, tk.END)
    pressure_entry.delete(0, tk.END)
    glucose_entry.delete(0, tk.END)

    name_entry.insert(0, record[1])
    age_entry.insert(0, record[2])
    pressure_entry.insert(0, record[5])
    glucose_entry.insert(0, record[6])

def save_record():
    if 'editing_item' not in globals():
        messagebox.showwarning("Warning", "No record is being edited")
        return

    item_id = editing_item
    name = name_entry.get()
    age = age_entry.get()
    pressure = pressure_entry.get()
    glucose = glucose_entry.get()

    if not name or not age or not pressure or not glucose:
        messagebox.showwarning("Warning", "All fields are required")
        return

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE records SET name=?, age=?, pressure=?, glucose=? WHERE id=?",
                   (name, age, pressure, glucose, item_id))
    conn.commit()
    conn.close()

    update_table()

def delete_record():
    selected_item = table.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No record selected")
        return

    item_id = selected_item[0]

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM records WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    update_table()

def generate_pdf():
    # Coleta os registros exibidos na tabela
    records = []
    for child in table.get_children():
        record = table.item(child)['values']
        records.append(record)
    
    if not records:
        messagebox.showwarning("Warning", "Não há registros para gerar o PDF.")
        return

    # Obtém o caminho para a área de trabalho do usuário
    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    pdf_file = os.path.join(desktop_path, "relatório_de_saúde.pdf")
    
    # Criação do arquivo PDF
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter
    
    # Adicionando título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Relatório de Registros de Saúde")
    
    # Cabeçalhos da tabela
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 1.5 * inch, "Nome")
    c.drawString(3 * inch, height - 1.5 * inch, "Idade")
    c.drawString(4 * inch, height - 1.5 * inch, "Data")
    c.drawString(5 * inch, height - 1.5 * inch, "Hora")
    c.drawString(6 * inch, height - 1.5 * inch, "Pressão")
    c.drawString(7 * inch, height - 1.5 * inch, "Glicose")
    
    c.setFont("Helvetica", 10)
    y_position = height - 2 * inch
    
    for record in records:
        c.drawString(1 * inch, y_position, str(record[0]))  # Nome
        c.drawString(3 * inch, y_position, str(record[1]))  # Idade
        c.drawString(4 * inch, y_position, str(record[2]))  # Data
        c.drawString(5 * inch, y_position, str(record[3]))  # Hora
        c.drawString(6 * inch, y_position, str(record[4]))  # Pressão
        c.drawString(7 * inch, y_position, str(record[5]))  # Glicose
        y_position -= 0.2 * inch
    
    c.save()
    messagebox.showinfo("PDF Gerado", f"O PDF foi gerado com sucesso na área de trabalho: {pdf_file}")

def create_ui():
    create_database()

    root = tk.Tk()
    root.title("Monitoramento de Saúde App")
    root.geometry("1200x600")  # Ajustado para aumentar a largura da janela

    # Definindo o ícone da janela
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)  
    else:
        print(f"Ícone não encontrado: {icon_path}")

    # Frame para campos de entrada
    input_frame = tk.Frame(root, padx=10, pady=10)
    input_frame.pack(side=tk.TOP, fill=tk.X)

    tk.Label(input_frame, text="Nome").grid(row=0, column=0, padx=5, pady=5)
    tk.Label(input_frame, text="Idade").grid(row=0, column=1, padx=5, pady=5)
    tk.Label(input_frame, text="Pressão").grid(row=0, column=2, padx=5, pady=5)
    tk.Label(input_frame, text="Glicose").grid(row=0, column=3, padx=5, pady=5)

    global name_entry, age_entry, pressure_entry, glucose_entry
    name_entry = tk.Entry(input_frame, width=15)
    age_entry = tk.Entry(input_frame, width=10)
    pressure_entry = tk.Entry(input_frame, width=15)
    glucose_entry = tk.Entry(input_frame, width=15)

    name_entry.grid(row=1, column=0, padx=5, pady=5)
    age_entry.grid(row=1, column=1, padx=5, pady=5)
    pressure_entry.grid(row=1, column=2, padx=5, pady=5)
    glucose_entry.grid(row=1, column=3, padx=5, pady=5)

    tk.Button(input_frame, text="Adicionar", command=add_record).grid(row=1, column=4, padx=5, pady=5)

    # Frame para filtros
    filter_frame = tk.Frame(root, padx=10, pady=10)
    filter_frame.pack(side=tk.TOP, fill=tk.X)

    global name_filter_var, period_filter_var
    name_filter_var = tk.StringVar()
    period_filter_var = tk.StringVar()

    tk.Label(filter_frame, text="Filtro por Nome").grid(row=0, column=0, padx=5, pady=5)
    tk.Entry(filter_frame, textvariable=name_filter_var, width=20).grid(row=0, column=1, padx=5, pady=5)

    tk.Label(filter_frame, text="Período").grid(row=0, column=2, padx=5, pady=5)

    period_options = ["Todo Período"] + list(months.keys())
    period_filter_var.set("Todo Período")
    period_filter_menu = ttk.Combobox(filter_frame, textvariable=period_filter_var, values=period_options, width=20)
    period_filter_menu.grid(row=0, column=3, padx=5, pady=5)
    
    tk.Button(filter_frame, text="Filtrar", command=update_table).grid(row=0, column=4, padx=5, pady=5)

    # Tabela
    global table
    table_frame = tk.Frame(root, padx=10, pady=10)
    table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    table = ttk.Treeview(table_frame, columns=("name", "age", "date", "hour", "pressure", "glucose"), show="headings")

    # Define cabeçalhos e largura das colunas
    table.heading("name", text="Nome")
    table.heading("age", text="Idade")
    table.heading("date", text="Data")
    table.heading("hour", text="Hora")
    table.heading("pressure", text="Pressão")
    table.heading("glucose", text="Glicose")

    table.column("name", width=150)  # Ajusta a largura da coluna "Nome"
    table.column("age", width=80)    # Ajusta a largura da coluna "Idade"
    table.column("date", width=120)  # Ajusta a largura da coluna "Data"
    table.column("hour", width=100)  # Ajusta a largura da coluna "Hora"
    table.column("pressure", width=120)  # Ajusta a largura da coluna "Pressão"
    table.column("glucose", width=120)   # Ajusta a largura da coluna "Glicose"

    table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Barra de rolagem
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    table.configure(yscrollcommand=scrollbar.set)

    # Frame para botões da tabela e Gerar PDF
    button_frame = tk.Frame(root, padx=10, pady=10)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    tk.Button(button_frame, text="Editar", command=edit_record).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(button_frame, text="Salvar", command=save_record).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(button_frame, text="Excluir", command=delete_record).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(button_frame, text="Gerar PDF", command=generate_pdf).pack(side=tk.RIGHT, padx=5, pady=5)

    update_table()
    root.mainloop()

create_ui()

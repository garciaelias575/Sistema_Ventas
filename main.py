import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime

# --- CONSTANTES ---
DB_PRODUCTOS = 'productos.json'
DB_VENTAS = 'ventas.json'


class DatabaseManager:
    """Clase especializada en la persistencia de datos."""
    @staticmethod
    def cargar(archivo):
        if not os.path.exists(archivo):
            return []
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def guardar(archivo, datos):
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error al guardar: {e}")


class SistemaInventario:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema PRO Inventario | Gestión Empresarial")
        self.root.geometry("900x600")

        # Carga de datos inicial
        self.productos = DatabaseManager.cargar(DB_PRODUCTOS)
        self.ventas = DatabaseManager.cargar(DB_VENTAS)

        self.setup_ui()
        self.actualizar_tabla()

    def setup_ui(self):
        """Configuración modular de la interfaz."""
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(expand=True, fill="both")

        # Tab 1: Gestión de Inventario
        self.tab_inv = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_inv, text="📦 Inventario")
        self.crear_modulo_inventario()

        # Tab 2: Ventas y Reportes
        self.tab_ventas = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_ventas, text="💰 Ventas")
        self.crear_modulo_ventas()

    def crear_modulo_inventario(self):
        # Frame de Formulario
        form_frame = ttk.LabelFrame(
            self.tab_inv, text=" Registro de Productos ")
        form_frame.pack(fill="x", padx=10, pady=5)

        campos = ["Código", "Nombre", "Precio", "Cantidad", "Categoría"]
        self.entries = {}

        for i, campo in enumerate(campos):
            ttk.Label(form_frame, text=f"{campo}:").grid(
                row=0, column=i*2, padx=5, pady=10)
            entry = ttk.Entry(form_frame, width=15)
            entry.grid(row=0, column=i*2+1, padx=5)
            self.entries[campo.lower()] = entry

        # Botones
        btn_frame = ttk.Frame(self.tab_inv)
        btn_frame.pack(fill="x", padx=10)

        ttk.Button(btn_frame, text="Añadir Producto",
                   command=self.registrar_producto).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Eliminar Seleccionado",
                   command=self.eliminar_producto).pack(side="left", padx=5)

        # Tabla con Scrollbar
        self.tabla = ttk.Treeview(
            self.tab_inv, columns=campos, show="headings")
        for c in campos:
            self.tabla.heading(c, text=c)
            self.tabla.column(c, width=100)

        scrollbar = ttk.Scrollbar(
            self.tab_inv, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)

        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

    def crear_modulo_ventas(self):
        frame = ttk.Frame(self.tab_ventas)
        frame.pack(pady=50)

        ttk.Label(frame, text="Acciones de Venta",
                  font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Button(frame, text="🚀 Registrar Venta (por código)",
                   command=self.registrar_venta, width=30).pack(pady=10)
        ttk.Button(frame, text="📊 Ver Historial de Ventas",
                   command=self.ver_reporte, width=30).pack(pady=10)

    # --- LÓGICA DE NEGOCIO ---
    def registrar_producto(self):
        try:
            nuevo_p = {
                "codigo": self.entries['código'].get(),
                "nombre": self.entries['nombre'].get(),
                "precio": float(self.entries['precio'].get()),
                "cantidad": int(self.entries['cantidad'].get()),
                "categoria": self.entries['categoría'].get()
            }

            if not nuevo_p['codigo'] or not nuevo_p['nombre']:
                raise ValueError("Campos vacíos")

            self.productos.append(nuevo_p)
            self.guardar_y_refrescar()
            messagebox.showinfo("Éxito", "Producto añadido correctamente.")
            self.limpiar_formulario()
        except ValueError as e:
            messagebox.showerror("Error", f"Datos inválidos: {e}")

    def eliminar_producto(self):
        selected = self.tabla.selection()
        if not selected:
            messagebox.showwarning(
                "Atención", "Seleccione un producto de la tabla")
            return

        item = self.tabla.item(selected)
        codigo = item['values'][0]

        self.productos = [
            p for p in self.productos if p['codigo'] != str(codigo)]
        self.guardar_y_refrescar()

    def registrar_venta(self):
        # En un sistema pro, esto abriría un modal de búsqueda
        codigo = self.entries['código'].get()
        try:
            cantidad = int(self.entries['cantidad'].get())
            for p in self.productos:
                if p['codigo'] == codigo:
                    if p['cantidad'] >= cantidad:
                        p['cantidad'] -= cantidad
                        total = p['precio'] * cantidad
                        self.ventas.append({
                            "id": len(self.ventas) + 1,
                            "codigo": codigo,
                            "nombre": p['nombre'],
                            "cantidad": cantidad,
                            "total": total,
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        self.guardar_y_refrescar()
                        messagebox.showinfo(
                            "Venta", f"Venta exitosa\nTotal: S/ {total:.2f}")
                        return
                    else:
                        messagebox.showwarning(
                            "Stock", "No hay suficiente mercancía")
                        return
            messagebox.showerror("Error", "Código no encontrado en inventario")
        except ValueError:
            messagebox.showerror("Error", "Ingrese código y cantidad válida")

    def guardar_y_refrescar(self):
        DatabaseManager.guardar(DB_PRODUCTOS, self.productos)
        DatabaseManager.guardar(DB_VENTAS, self.ventas)
        self.actualizar_tabla()
        self.verificar_stock_critico()

    def actualizar_tabla(self):
        self.tabla.delete(*self.tabla.get_children())
        for p in self.productos:
            self.tabla.insert("", "end", values=(
                p['codigo'], p['nombre'], p['precio'], p['cantidad'], p['categoria']))

    def verificar_stock_critico(self):
        bajos = [p['nombre'] for p in self.productos if p['cantidad'] <= 5]
        if bajos:
            messagebox.showwarning(
                "Stock Crítico", f"Reponer los siguientes productos:\n{', '.join(bajos)}")

    def ver_reporte(self):
        win = tk.Toplevel(self.root)
        win.title("Historial de Ventas")
        win.geometry("600x400")

        tree = ttk.Treeview(win, columns=(
            "ID", "Nombre", "Total", "Fecha"), show="headings")
        for c in ("ID", "Nombre", "Total", "Fecha"):
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True)

        for v in self.ventas:
            tree.insert("", "end", values=(
                v['id'], v['nombre'], f"S/ {v['total']:.2f}", v['fecha']))

    def limpiar_formulario(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)


# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    root = tk.Tk()
    # Aquí podrías insertar la lógica de Login antes de iniciar SistemaInventario
    app = SistemaInventario(root)
    root.mainloop()

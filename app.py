from flask import Flask, render_template, request, redirect
from db import get_db_connection

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/editar-venta/<int:id>', methods=["GET", "POST"])
def editar_venta(id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Obtener la venta con el ID especificado
    cur.execute("""
        SELECT v.id, v.fecha, v.total, p.id, p.nombre, dv.cantidad, dv.precio_unitario
        FROM ventas v
        JOIN detalle_ventas dv ON v.id = dv.venta_id
        JOIN productos p ON p.id = dv.producto_id
        WHERE v.id = %s
    """, (id,))
    detalles_venta = cur.fetchall()

    if request.method == "POST":
        # Actualizar los detalles de la venta
        for item in detalles_venta:
            producto_id = item[3]
            cantidad_nueva = int(request.form[f'cantidad_{producto_id}'])
            precio_nuevo = float(request.form[f'precio_{producto_id}'])

            # Actualizar la cantidad y precio del producto en detalle_ventas
            cur.execute("""
                UPDATE detalle_ventas
                SET cantidad = %s, precio_unitario = %s
                WHERE venta_id = %s AND producto_id = %s
            """, (cantidad_nueva, precio_nuevo, id, producto_id))

            # Actualizar el total de la venta
            cur.execute("SELECT SUM(cantidad * precio_unitario) FROM detalle_ventas WHERE venta_id = %s", (id,))
            total_venta = cur.fetchone()[0]

            # Actualizar el total de la venta
            cur.execute("UPDATE ventas SET total = %s WHERE id = %s", (total_venta, id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect('/historial-ventas')

    cur.close()
    conn.close()

    return render_template('editar_venta.html', detalles_venta=detalles_venta)


@app.route('/nuevo-producto')
def nuevo_producto():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM categorias")
    categorias = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('registro_producto.html', categorias=categorias)

@app.route('/registrar-producto', methods=['POST'])
def registrar_producto():
    nombre = request.form['nombre']
    precio = request.form['precio']
    cantidad = request.form['cantidad']
    categoria_id = request.form['categoria_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO productos (nombre, precio, cantidad, categoria_id)
        VALUES (%s, %s, %s, %s)
    """, (nombre, precio, cantidad, categoria_id))
    conn.commit()
    cur.close()
    conn.close()

    return redirect('/nuevo-producto')

@app.route('/venta')
def venta():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, cantidad, precio FROM productos WHERE cantidad > 0")
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('venta.html', productos=productos)

@app.route('/registrar-venta', methods=['POST'])
def registrar_venta():
    producto_id = int(request.form['producto_id'])
    cantidad = int(request.form['cantidad'])

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT precio, cantidad FROM productos WHERE id = %s", (producto_id,))
    result = cur.fetchone()
    if not result:
        return "Producto no encontrado"
    
    precio_unitario, stock = result
    if cantidad > stock:
        return "No hay suficiente stock"

    total = cantidad * precio_unitario

    cur.execute("INSERT INTO ventas (total) VALUES (%s) RETURNING id", (total,))
    venta_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario)
        VALUES (%s, %s, %s, %s)
    """, (venta_id, producto_id, cantidad, precio_unitario))

    cur.execute("""
        UPDATE productos SET cantidad = cantidad - %s WHERE id = %s
    """, (cantidad, producto_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect('/venta')

@app.route('/historial-ventas')
def historial_ventas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT v.id, v.fecha, v.total,
               p.nombre, dv.cantidad, dv.precio_unitario
        FROM ventas v
        JOIN detalle_ventas dv ON v.id = dv.venta_id
        JOIN productos p ON p.id = dv.producto_id
        ORDER BY v.fecha DESC
    """)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    ventas_dict = {}
    for row in resultados:
        venta_id, fecha, total, producto, cantidad, precio = row
        if venta_id not in ventas_dict:
            ventas_dict[venta_id] = {
                'fecha': fecha,
                'total': total,
                'detalles': []
            }
        ventas_dict[venta_id]['detalles'].append({
            'producto': producto,
            'cantidad': cantidad,
            'precio_unitario': precio
        })

    return render_template('historial_ventas.html', ventas=ventas_dict)


@app.route('/nueva-categoria')
def nueva_categoria():
    return render_template('nueva_categoria.html')

@app.route('/registrar-categoria', methods=['POST'])
def registrar_categoria():
    nombre = request.form['nombre']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO categorias (nombre) VALUES (%s)", (nombre,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/nueva-categoria')


if __name__ == '__main__':
    app.run(debug=True)
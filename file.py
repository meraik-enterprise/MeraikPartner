# Helpers
def clean_float_string(s):
    if not s:
        return '0'
    s = s.lstrip('<> ').replace(',', '.')
    return ''.join(ch for ch in s if ch.isdigit() or ch == '.') or '0'


def safe_int(v, d=0):
    try:
        return int(v)
    except:
        return d


def safe_float(v, d=0.0):
    try:
        return float(clean_float_string(v))
    except:
        return d


def bool_flag(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ('1', 'true', 'si', 'yes')


# 1) Cliente
cust = env['res.partner'].search(
    [('email', '=', payload.get('email'))], limit=1)
if not cust:
    cust = env['res.partner'].create({
        'name':  payload.get('name'),
        'email': payload.get('email'),
        'phone': payload.get('phone'),
        'city':  payload.get('city'),
    })

# 2) Parámetros
model_names = [m.strip() for m in payload.get(
    'models', '').split(',') if m.strip()]
num_tramos = safe_int(payload.get('tramos', 0))

# 3) Búsqueda de vallas


def buscar_mejor_variante_valla(model_name, altura_m):
    _logger.info("Valla: modelo=%s, altura=%.3fm", model_name, altura_m)

    # 1) filtro en plantilla: "valla" + modelo exacto
    domain = [
        ('name', 'ilike', 'valla'),
        ('attribute_line_ids.value_ids.name', 'ilike', model_name),
    ]
    tpls = env['product.template'].search(domain)
    _logger.info("→ plantillas valla encontradas: %d", len(tpls))
    if not tpls:
        return None

    # 2) elegir variante más cercana
    best, dmin, best_av = None, float('inf'), None
    for var in tpls.mapped('product_variant_ids'):
        av = None
        # Buscar primero en la variante
        for a in var.product_template_variant_value_ids:
            _logger.info(
                f"Variante {var.id} - atributo: {a.attribute_id.name} = {a.name}")
            if a.attribute_id.name == 'Altura vallas (m)':
                try:
                    av = float(clean_float_string(a.name))
                    _logger.info(f"→ Altura vallas (m) leída: {a.name} → {av}")
                except Exception as e:
                    _logger.warning(
                        f"No se pudo convertir la altura '{a.name}' a float: {e}")
                break
        # Si no está en la variante, buscar en la plantilla
        if av is None:
            for a in var.product_tmpl_id.attribute_line_ids:
                _logger.info(
                    f"Plantilla {var.product_tmpl_id.id} - atributo: {a.attribute_id.name} = {[v.name for v in a.value_ids]}")
                if a.attribute_id.name == 'Altura vallas (m)':
                    try:
                        if len(a.value_ids) == 1:
                            av = float(clean_float_string(a.value_ids[0].name))
                            _logger.info(
                                f"→ Altura vallas (m) leída de plantilla: {a.value_ids[0].name} → {av}")
                    except Exception as e:
                        _logger.warning(
                            f"No se pudo convertir la altura de plantilla '{a.value_ids[0].name}' a float: {e}")
                    break
        if av is None:
            _logger.warning(
                f"Variante {var.id} descartada: no tiene atributo 'Altura vallas (m)' ni en variante ni en plantilla.")
            continue

        d = abs(av - altura_m)
        _logger.info(
            f"Variante {var.id} - altura {av}, distancia solicitada: {d}")
        # desempate: si igual distancia, elegimos la altura menor
        if d < dmin or (d == dmin and (best_av is None or av < best_av)):
            best, dmin, best_av = var, d, av

    _logger.info("→ mejor variante valla: %s (%.3fm, d=%.3f)",
                 best and best.name, best_av or 0.0, dmin)
    return best

# 4) Búsqueda de puertas


def buscar_variante_puerta(modelo, tipo_puerta, ancho_m, alto_m):
    # 1) descartar modelos sin puertas
    if modelo in ('Adonis', 'Cerbero', 'Ciclope - madera', 'Forest', 'Meridien'):
        return None

    # 2) dominio: tipo de puerta + modelo
    domain = [
        ('name', 'ilike', tipo_puerta),
        ('attribute_line_ids.value_ids.name', 'like', modelo),
    ]
    tpls = env['product.template'].search(domain)
    if not tpls:
        return None

    # 3) leer (h,w) de cada variante
    dims = []
    for tpl in tpls:
        for var in tpl.product_variant_ids:
            h_attr = '0'
            w_attr = '0'
            for a in var.product_template_variant_value_ids:
                if a.attribute_id.name == 'Altura (m)':
                    h_attr = clean_float_string(a.name)
                elif a.attribute_id.name == 'Ancho (m)':
                    w_attr = clean_float_string(a.name)
            try:
                h = float(h_attr)
                w = float(w_attr)
            except:
                continue
            dims.append({'var': var, 'h': h, 'w': w})

    if not dims:
        return None

    # 4) construir lista de anchuras únicas y ordenarla
    widths = []
    for d in dims:
        w = d['w']
        if w not in widths:
            widths.append(w)
    widths.sort()

    # 5) escoger target_w = primer w >= ancho_m, sino el mayor disponible
    target_w = None
    for w in widths:
        if w >= ancho_m:
            target_w = w
            break
    if target_w is None:
        target_w = widths[-1]

    # 6) filtrar variantes con ese ancho
    cands = []
    for d in dims:
        if d['w'] == target_w:
            cands.append(d)

    # 7) elegir la que tenga altura más cercana a alto_m,
    #    en empate, la de altura menor
    best = None
    dmin = float('inf')
    best_h = None
    for d in cands:
        dist = d['h'] - alto_m
        if dist < 0:
            dist = -dist
        if dist < dmin or (dist == dmin and (best_h is None or d['h'] < best_h)):
            best = d['var']
            dmin = dist
            best_h = d['h']

    return best

# 5) Procesar puertas (peatonal + corredera)


def procesar_puerta(order, payload, modelo):
    # Peatonal
    if bool_flag(payload.get('puerta_peatonal')):
        hojas = safe_int(payload.get('hoja_puerta_peatonal', 0))
        if hojas > 0:
            tipo = 'Puerta batiente' if hojas == 1 else 'Puerta doble batiente'
            ancho = safe_float(payload.get('puerta_peatonal_ancho', 0))
            alto = safe_float(payload.get('puerta_peatonal_alto', 0))
            var = buscar_variante_puerta(modelo, tipo, ancho, alto)
            if var:
                desc = f"{tipo} {modelo} — Altura {alto}m × Ancho {ancho}m"
                order.write({'order_line': [(0, 0, {
                    'product_id':      var.id,
                    'product_uom_qty': 1,
                    'name':            desc,
                })]})
    # Corredera
    if bool_flag(payload.get('puerta_corredera')):
        tipo = 'Puerta corredera'
        ancho = safe_float(payload.get('puerta_corredera_ancho', 0))
        alto = safe_float(payload.get('puerta_corredera_alto', 0))
        var = buscar_variante_puerta(modelo, tipo, ancho, alto)
        if var:
            desc = f"{tipo} {modelo} — Altura {alto}m × Ancho {ancho}m"
            order.write({'order_line': [(0, 0, {
                'product_id':      var.id,
                'product_uom_qty': 1,
                'name':            desc,
            })]})


# 6) Loop principal
for model_name in model_names:
    order = env['sale.order'].create({
        'partner_id':           cust.id,
        'x_studio_email':       payload.get('email'),
        'x_studio_telefono':    payload.get('phone'),
        'x_studio_provincia':   payload.get('city'),
        'x_studio_id_order':    payload.get('conversation_id'),
        'x_studio_conversacin': payload.get('conversation'),
    })
    # vallas
    for i in range(1, num_tramos+1):
        _logger.info("Payload tramo %d: longitud=%r, altura=%r",
                     i, payload.get(f'longitud_t{i}'), payload.get(f'altura_t{i}'))
        l_m = safe_float(payload.get(f'longitud_t{i}', 0))
        h_m = safe_float(payload.get(f'altura_t{i}',   0))
        _logger.info("Tramo %d → l=%.3fm, h=%.3fm", i, l_m, h_m)
        if l_m <= 0 or h_m <= 0:
            _logger.warning("  Ignorado tramo %d: l=%.3f, h=%.3f", i, l_m, h_m)
            continue

        var = buscar_mejor_variante_valla(model_name, h_m)
        if not var:
            _logger.warning(
                "  No variante VALLA para tramo %d @ %.3fm", i, h_m)
            continue

        qty = l_m
        desc = f"Tramo {i}: {model_name} — Altura {h_m:.2f}m × {qty:.2f}m"
        order.write({'order_line': [(0, 0, {
            'product_id':      var.id,
            'product_uom_qty': qty,
            'name':            desc,
        })]})

    _logger.info("→ procesando puertas para %s", model_name)
    procesar_puerta(order, payload, model_name)

    # Puertas de piscina
    num_puertas_piscina = safe_int(payload.get('num_puertas_piscina', 0))
    if num_puertas_piscina > 0:
        cerradura_seguridad = bool_flag(payload.get('cerradura_seguridad'))
        # Buscar el producto correcto según la cerradura
        nombre_producto = "Puerta piscina cerradura seguridad" if cerradura_seguridad else "Puerta piscina cerradura estándar"
        template = env['product.template'].search(
            [('name', 'ilike', nombre_producto)], limit=1)
        if template:
            prod = template.product_variant_id
            order.write({'order_line': [(0, 0, {
                'product_id':      prod.id,
                'product_uom_qty': num_puertas_piscina,
                'name':            prod.name,
            })]})
        else:
            _logger.warning(
                f"No se encontró el producto '{nombre_producto}' para puertas de piscina.")

    if bool_flag(payload.get('portero_electrico')):
        # Buscar en la plantilla de producto para mayor robustez
        template = env['product.template'].search(
            [('name', 'ilike', 'Apertura eléctrica')], limit=1)
        if template:
            # Obtener la variante de producto desde la plantilla
            prod = template.product_variant_id
            order.write({'order_line': [(0, 0, {
                'product_id':      prod.id,
                'product_uom_qty': 1,
                'name':            prod.name,
            })]})
        else:
            _logger.warning(
                "No se encontró la plantilla del producto 'Apertura eléctrica' y no se añadió al presupuesto.")


_logger.info("Todos los presupuestos generados.")

env.cr.flush()
for order in env['sale.order'].search([('x_studio_conversacin', '=', payload.get('conversation'))]):
    _logger.info(
        "🧩 Ejecutando corrección de postes para pedido %s", order.name)
    if order.x_studio_conversacin:
        lines = order.order_line.sorted('id')
        vallas = [l for l in lines if 'valla' in (
            l.product_id.name or '').lower()]
        postes = [l for l in lines if 'poste' in (
            l.product_id.name or '').lower()]
        _logger.info("Vallas encontradas: %d, Postes encontrados: %d",
                     len(vallas), len(postes))
        # Emparejar por posición: solo dejamos tantos postes como vallas, en el mismo orden
        postes_a_dejar = postes[:len(vallas)]
        postes_a_eliminar = postes[len(vallas):]
        for l in postes_a_eliminar:
            _logger.info("🗑️ Eliminando poste sobrante: %s | %.2f",
                         l.product_id.name, l.product_uom_qty)
            l.unlink()
        # Ajustar cantidad y precio de los postes restantes
        for l in postes_a_dejar:
            new_qty = l.product_uom_qty * 0.5
            new_price = l.price_unit * 1
            _logger.info("✅ Poste %s → cantidad %.2f + precio %.2f",
                         l.product_id.name, new_qty, new_price)
            l.write({
                'product_uom_qty': new_qty,
                'price_unit': new_price,
            })
        # Log final
        lines_final = order.order_line.sorted('id')
        _logger.info("Líneas después de la corrección:")
        for idx, l in enumerate(lines_final):
            _logger.info("  [%d] %s | %s | %.2f", idx,
                         l.product_id.name, l.name, l.product_uom_qty)
    else:
        _logger.info(
            "❌ Pedido ignorado: no contiene campo x_studio_conversacin")

from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from suppliers.models import Supplier
from materials.models import Material
from materials.models import Unit
from core.models import Currency
from .models import PurchaseOrder, PurchaseOrderLine, OrderStatus
from datetime import date
import json

# Vista del formulario de creación de pedido de compra
def purchase_order_form_view(request):
    """
    Vista que renderiza el formulario para crear una nueva orden de compra.
    
    URL: /purchases/create/
    Método: GET
    
    Retorna:
        - HTML con el formulario de creación de pedido
    """
    context = {
        'currencies': Currency.objects.all().order_by('code'),
        'today': date.today().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'purchases/purchase_order_create.html', context)

# API para obtener detalles de proveedor
def supplier_detail_api(request, supplier_id):
    """
    API endpoint que devuelve los datos de un proveedor en formato JSON.
    
    URL: /purchases/api/supplier/<supplier_id>/
    Método: GET
    Parámetro: supplier_id puede ser el ID numérico o el id_supplier (ej: SUP-001)
    
    Retorna:
        - 200: JSON con los datos del proveedor
        - 404: Si el proveedor no existe
    """
    try:
        # Intentar buscar por id_supplier primero (string como SUP-001)
        try:
            supplier = Supplier.objects.get(id_supplier=supplier_id)
        except Supplier.DoesNotExist:
            # Si falla, intentar por ID numérico
            supplier = Supplier.objects.get(id=int(supplier_id))
        
        data = {
            'supplier_id': supplier.id,
            'id_supplier': supplier.id_supplier,
            'name': supplier.name,
            'address': supplier.address,
            'city': supplier.city,
            'state_province': supplier.state_province,
            'country': supplier.country,
            'postal_code': supplier.zip_code,
            'phone': supplier.phone,
            'email': supplier.email,
            'contact_person': supplier.contact_name,
            'tax_id': supplier.tax_id,
            'payment_method': supplier.payment_method.name if supplier.payment_method else None,
        }
        
        return JsonResponse(data)
    
    except (Supplier.DoesNotExist, ValueError):
        raise Http404("Proveedor no encontrado")

# API para obtener detalles de material
def material_detail_api(request, material_id):
    """
    API endpoint que devuelve los datos de un material en formato JSON.
    
    URL: /purchases/api/material/<material_id>/
    Método: GET
    Parámetro: material_id puede ser el ID numérico o el material_code
    
    Retorna:
        - 200: JSON con los datos del material
        - 404: Si el material no existe
    """
    try:
        # Intentar buscar por id_material primero (ej: MP-105)
        try:
            material = Material.objects.get(id_material=material_id)
        except Material.DoesNotExist:
            # Si falla, intentar por ID numérico (PK)
            material = Material.objects.get(id=int(material_id))
        
        data = {
            'material_id': material.id,
            'id_material': material.id_material,
            'name': material.name,
            'description': material.description,
            'material_code': material.id_material,
            'default_unit': material.unit.name if material.unit else None,
            'default_unit_id': material.unit.id if material.unit else None,
            'material_type': material.material_type.name if material.material_type else None,
            'status': material.status.name if material.status else None,
        }
        
        return JsonResponse(data)
    
    except (Material.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Material not found'}, status=404)

# API para crear pedido de compra (POST JSON)
@csrf_exempt
@transaction.atomic
def create_purchase_order_api(request):
    """
    API endpoint que crea una orden de compra con sus líneas.
    
    URL: /purchases/api/create/
    Método: POST
    Content-Type: application/json
    
    Espera un JSON con:
    {
        "supplier_id": <int>,
        "estimated_delivery_date": "YYYY-MM-DD",
        "lines": [
            {
                "material_id": <int>,
                "quantity": <int>,
                "unit_id": <int>,
                "price": <decimal>,
                "currency_id": <int>
            },
            ...
        ]
    }
    
    Retorna:
        - 200: {"message": "Purchase order created successfully", "purchase_order_id": <id>}
        - 400: {"error": "mensaje de error"}
        - 405: {"error": "Method not allowed"}
        - 500: {"error": "mensaje de error interno"}
    """
    
    # Validar método
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Parsear el JSON del body
        data = json.loads(request.body)
        
        # Validar presencia de campos requeridos
        supplier_id = data.get('supplier_id')
        estimated_delivery_date = data.get('estimated_delivery_date')
        lines = data.get('lines', [])
        
        if not supplier_id:
            return JsonResponse({'error': 'supplier_id is required'}, status=400)
        
        if not estimated_delivery_date:
            return JsonResponse({'error': 'estimated_delivery_date is required'}, status=400)
        
        if not lines or len(lines) == 0:
            return JsonResponse({'error': 'At least one line item is required'}, status=400)
        
        # Validar que el proveedor exista
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return JsonResponse({'error': f'Supplier with id {supplier_id} does not exist'}, status=400)
        
        # Obtener el estado por defecto (buscar "Borrador" o usar el primero disponible)
        try:
            # Intentar obtener el estado "Borrador" primero
            default_status = OrderStatus.objects.get(symbol='BOR')
        except OrderStatus.DoesNotExist:
            try:
                # Si no existe "Borrador", intentar id=1 o el primer estado disponible
                default_status = OrderStatus.objects.get(id=1)
            except OrderStatus.DoesNotExist:
                default_status = OrderStatus.objects.first()
                if not default_status:
                    return JsonResponse({'error': 'No order status found in database'}, status=400)
        
        # Generar el siguiente id_purchase_order
        # Buscar el último pedido y sumar 1
        last_order = PurchaseOrder.objects.order_by('-id').first()
        if last_order and last_order.id_purchase_order:
            # Extraer el número del último ID (ej: "PO-0001" -> 1)
            try:
                last_number = int(last_order.id_purchase_order.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        new_purchase_order_id = f"PO-{next_number:04d}"
        
        # Crear el PurchaseOrder
        purchase_order = PurchaseOrder.objects.create(
            id_purchase_order=new_purchase_order_id,
            supplier=supplier,
            issue_date=date.today(),
            estimated_delivery_date=estimated_delivery_date,
            status=default_status,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Validar y crear las líneas
        for index, line_data in enumerate(lines, start=1):
            material_id = line_data.get('material_id')
            quantity = line_data.get('quantity')
            unit_id = line_data.get('unit_id')
            price = line_data.get('price')
            currency_id = line_data.get('currency_id')
            
            # Validar campos requeridos
            if not material_id:
                return JsonResponse({'error': f'Line {index}: material_id is required'}, status=400)
            
            if not quantity or quantity <= 0:
                return JsonResponse({'error': f'Line {index}: quantity must be greater than 0'}, status=400)
            
            if not unit_id:
                return JsonResponse({'error': f'Line {index}: unit_id is required'}, status=400)
            
            if price is None or price < 0:
                return JsonResponse({'error': f'Line {index}: price must be 0 or greater'}, status=400)
            
            if not currency_id:
                return JsonResponse({'error': f'Line {index}: currency_id is required'}, status=400)
            
            # Validar que los objetos relacionados existan
            try:
                # Intentar buscar por id_material (código ERP como MP-105)
                try:
                    material = Material.objects.get(id_material=material_id)
                except Material.DoesNotExist:
                    # Si falla, intentar por PK numérico
                    material = Material.objects.get(id=int(material_id))
            except (Material.DoesNotExist, ValueError):
                return JsonResponse({'error': f'Line {index}: Material not found ({material_id})'}, status=400)
            
            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return JsonResponse({'error': f'Line {index}: Unit with id {unit_id} does not exist'}, status=400)
            
            try:
                currency = Currency.objects.get(id=currency_id)
            except Currency.DoesNotExist:
                return JsonResponse({'error': f'Line {index}: Currency with id {currency_id} does not exist'}, status=400)
            
            # Generar id_purchase_order_line
            line_id = f"{new_purchase_order_id}-L{index:03d}"
            
            # Crear la línea del pedido
            PurchaseOrderLine.objects.create(
                id_purchase_order_line=line_id,
                purchase_order=purchase_order,
                material=material,
                position=index,
                quantity=quantity,
                unit_material=unit,
                price=price,
                currency_supplier=currency,
                received_quantity=0,
                created_by=request.user if request.user.is_authenticated else None
            )
        
        return JsonResponse({
            'message': 'Purchase order created successfully',
            'id_purchase_order': new_purchase_order_id,
            'purchase_order_id': new_purchase_order_id,
            'lines_created': len(lines)
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    
    except Exception as e:
        # Log the error for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

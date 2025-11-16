from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
import csv
import io
from .models import Supplier
from .forms import SupplierForm, CSVUploadForm
from suppliers.models import PaymentMethod

@login_required
def suppliers_list(request):
    suppliers = Supplier.objects.all()
    
    # Obtener filtros
    id_supplier = request.GET.get('id_supplier', '')
    legal_name = request.GET.get('legal_name', '')
    name = request.GET.get('name', '')
    tax_id = request.GET.get('tax_id', '')
    country = request.GET.get('country', '')
    state_province = request.GET.get('state_province', '')
    city = request.GET.get('city', '')
    address = request.GET.get('address', '')
    zip_code = request.GET.get('zip_code', '')
    phone = request.GET.get('phone', '')
    email = request.GET.get('email', '')
    contact_name = request.GET.get('contact_name', '')
    contact_role = request.GET.get('contact_role', '')
    category = request.GET.get('category', '')
    payment_terms = request.GET.get('payment_terms', '')
    currency = request.GET.get('currency', '')
    payment_method = request.GET.get('payment_method', '')
    bank_account = request.GET.get('bank_account', '')
    status = request.GET.get('status', '')
    created_at = request.GET.get('created_at', '')
    updated_at = request.GET.get('updated_at', '')
    created_by = request.GET.get('created_by', '')
    
    # Aplicar filtros
    if id_supplier:
        suppliers = suppliers.filter(id_supplier__icontains=id_supplier)
    if legal_name:
        suppliers = suppliers.filter(legal_name__icontains=legal_name)
    if name:
        suppliers = suppliers.filter(name__icontains=name)
    if tax_id:
        suppliers = suppliers.filter(tax_id__icontains=tax_id)
    if country:
        suppliers = suppliers.filter(country__icontains=country)
    if state_province:
        suppliers = suppliers.filter(state_province__icontains=state_province)
    if city:
        suppliers = suppliers.filter(city__icontains=city)
    if address:
        suppliers = suppliers.filter(address__icontains=address)
    if zip_code:
        suppliers = suppliers.filter(zip_code=zip_code)
    if phone:
        suppliers = suppliers.filter(phone=phone)
    if email:
        suppliers = suppliers.filter(email__icontains=email)
    if contact_name:
        suppliers = suppliers.filter(contact_name__icontains=contact_name)
    if contact_role:
        suppliers = suppliers.filter(contact_role__icontains=contact_role)
    if category:
        suppliers = suppliers.filter(category__icontains=category)
    if payment_terms:
        suppliers = suppliers.filter(payment_terms__icontains=payment_terms)
    if currency:
        suppliers = suppliers.filter(currency__icontains=currency)
    if payment_method:
        suppliers = suppliers.filter(payment_method__id=payment_method)
    if bank_account:
        suppliers = suppliers.filter(bank_account__icontains=bank_account)
    if status == 'active':
        suppliers = suppliers.filter(status=True)
    elif status == 'inactive':
        suppliers = suppliers.filter(status=False)
    if created_at:
        suppliers = suppliers.filter(created_at__date=created_at)
    if updated_at:
        suppliers = suppliers.filter(updated_at__date=updated_at)
    if created_by:
        suppliers = suppliers.filter(created_by__username__icontains=created_by)
    
    # Exportar a CSV si se solicita
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID Supplier', 'Legal Name', 'Name', 'Tax ID', 'Country', 'State/Province', 
            'City', 'Address', 'Zip Code', 'Phone', 'Email', 'Contact Name', 
            'Contact Role', 'Category', 'Payment Terms', 'Currency', 'Payment Method', 
            'Bank Account', 'Status', 'Created At', 'Updated At', 'Created By'
        ])
        
        for supplier in suppliers:
            writer.writerow([
                supplier.id_supplier,
                supplier.legal_name,
                supplier.name,
                supplier.tax_id,
                supplier.country,
                supplier.state_province,
                supplier.city,
                supplier.address,
                supplier.zip_code,
                supplier.phone,
                supplier.email,
                supplier.contact_name,
                supplier.contact_role,
                supplier.category,
                supplier.payment_terms,
                supplier.currency,
                supplier.payment_method,
                supplier.bank_account,
                'Activo' if supplier.status else 'Inactivo',
                supplier.created_at.strftime('%d/%m/%Y %H:%M'),
                supplier.updated_at.strftime('%d/%m/%Y %H:%M'),
                supplier.created_by.username if supplier.created_by else 'N/A'
            ])
        
        return response
    
    # Paginación
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Construir querystring sin page
    querystring = request.GET.copy()
    if 'page' in querystring:
        querystring.pop('page')
    
    filters = {
        'id_supplier': id_supplier,
        'legal_name': legal_name,
        'name': name,
        'tax_id': tax_id,
        'country': country,
        'state_province': state_province,
        'city': city,
        'address': address,
        'zip_code': zip_code,
        'phone': phone,
        'email': email,
        'contact_name': contact_name,
        'contact_role': contact_role,
        'category': category,
        'payment_terms': payment_terms,
        'currency': currency,
        'payment_method': payment_method,
        'bank_account': bank_account,
        'status': status,
        'created_at': created_at,
        'updated_at': updated_at,
        'created_by': created_by,
    }
    
    # Cargar opciones para los filtros
    payment_methods = PaymentMethod.objects.all()
    
    context = {
        'page_obj': page_obj,
        'filters': filters,
        'querystring': querystring.urlencode(),
        'payment_methods': payment_methods,
    }
    
    return render(request, 'suppliers/suppliers_list.html', context)

@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            return redirect('suppliers:supplier_create')
    else:
        form = SupplierForm()
    
    return render(request, 'suppliers/supplier_form.html', {'form': form})

@login_required
def supplier_edit(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('suppliers:suppliers_list')
    else:
        form = SupplierForm(instance=supplier)
    
    context = {
        'form': form,
        'supplier': supplier,
        'edit_mode': True
    }
    return render(request, 'suppliers/supplier_form.html', context)

@login_required
def supplier_delete(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    supplier.delete()
    return redirect('suppliers:suppliers_list')

@login_required
def supplier_bulk_upload(request):
    # Verificar permisos (permitir superusuarios)
    if not request.user.is_superuser:
        try:
            user_role = request.user.userrole_set.first()
            if not user_role or user_role.role.suppliers < 2:
                messages.error(request, 'You do not have permission to perform bulk uploads.')
                return redirect('suppliers:suppliers_list')
        except AttributeError:
            messages.error(request, 'You do not have permission to perform bulk uploads.')
            return redirect('suppliers:suppliers_list')
    
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Intentar decodificar el archivo
            try:
                decoded_file = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                try:
                    csv_file.seek(0)
                    decoded_file = csv_file.read().decode('iso-8859-1')
                except Exception as e:
                    messages.error(request, f'Error decoding file: {str(e)}')
                    return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form})
            
            # Procesar CSV
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string, delimiter=';')
            
            # Limpiar BOM y espacios en cabeceras
            reader.fieldnames = [field.strip().replace('\ufeff', '') for field in reader.fieldnames]
            
            valid_suppliers = []
            error_rows = []
            row_number = 1
            
            for row in reader:
                row_number += 1
                # Limpiar espacios en valores
                cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
                
                # Convertir status a booleano
                if 'status' in cleaned_row:
                    status_value = cleaned_row['status'].lower()
                    cleaned_row['status'] = status_value in ['true', '1', 'yes', 'active']
                
                # Crear formulario con los datos
                supplier_form = SupplierForm(cleaned_row)
                
                if supplier_form.is_valid():
                    supplier = supplier_form.save(commit=False)
                    supplier.created_by = request.user
                    valid_suppliers.append(supplier)
                else:
                    error_rows.append({
                        'row': row_number,
                        'data': cleaned_row,
                        'errors': supplier_form.errors
                    })
            
            # Guardar todos los registros válidos en una sola operación
            if valid_suppliers:
                Supplier.objects.bulk_create(valid_suppliers)
            
            # Preparar contexto con el informe
            context = {
                'form': form,
                'upload_complete': True,
                'total_rows': row_number - 1,
                'successful_rows': len(valid_suppliers),
                'error_count': len(error_rows),
                'error_rows': error_rows
            }
            
            if valid_suppliers:
                messages.success(request, f'Successfully uploaded {len(valid_suppliers)} suppliers.')
            if error_rows:
                messages.warning(request, f'{len(error_rows)} rows had errors and were not uploaded.')
            
            return render(request, 'suppliers/supplier_bulk_upload.html', context)
    else:
        form = CSVUploadForm()
    
    return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form})

@login_required
def download_template_suppliers(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers_template.csv"'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'id_supplier', 'legal_name', 'name', 'tax_id', 'country', 
        'state_province', 'city', 'address', 'zip_code', 'phone', 
        'email', 'contact_name', 'contact_role', 'category', 
        'payment_terms', 'currency', 'payment_method', 'bank_account', 
        'status'
    ])
    
    return response


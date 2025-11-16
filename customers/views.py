from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
import csv
import io
from .models import Customer
from .forms import CustomerForm, CSVUploadForm
from suppliers.models import PaymentMethod

@login_required
def customers_list(request):
    customers = Customer.objects.all()
    
    # Obtener filtros
    id_customer = request.GET.get('id_customer', '')
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
    if id_customer:
        customers = customers.filter(id_customer__icontains=id_customer)
    if legal_name:
        customers = customers.filter(legal_name__icontains=legal_name)
    if name:
        customers = customers.filter(name__icontains=name)
    if tax_id:
        customers = customers.filter(tax_id__icontains=tax_id)
    if country:
        customers = customers.filter(country__icontains=country)
    if state_province:
        customers = customers.filter(state_province__icontains=state_province)
    if city:
        customers = customers.filter(city__icontains=city)
    if address:
        customers = customers.filter(address__icontains=address)
    if zip_code:
        customers = customers.filter(zip_code=zip_code)
    if phone:
        customers = customers.filter(phone=phone)
    if email:
        customers = customers.filter(email__icontains=email)
    if contact_name:
        customers = customers.filter(contact_name__icontains=contact_name)
    if contact_role:
        customers = customers.filter(contact_role__icontains=contact_role)
    if category:
        customers = customers.filter(category__icontains=category)
    if payment_terms:
        customers = customers.filter(payment_terms__icontains=payment_terms)
    if currency:
        customers = customers.filter(currency__icontains=currency)
    if payment_method:
        customers = customers.filter(payment_method__id=payment_method)
    if bank_account:
        customers = customers.filter(bank_account__icontains=bank_account)
    if status == 'active':
        customers = customers.filter(status=True)
    elif status == 'inactive':
        customers = customers.filter(status=False)
    if created_at:
        customers = customers.filter(created_at__date=created_at)
    if updated_at:
        customers = customers.filter(updated_at__date=updated_at)
    if created_by:
        customers = customers.filter(created_by__username__icontains=created_by)
    
    # Exportar a CSV si se solicita
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customers.csv"'
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'ID Customer', 'Legal Name', 'Name', 'Tax ID', 'Country', 'State/Province', 
            'City', 'Address', 'Zip Code', 'Phone', 'Email', 'Contact Name', 
            'Contact Role', 'Category', 'Payment Terms', 'Currency', 'Payment Method', 
            'Bank Account', 'Status', 'Created At', 'Updated At', 'Created By'
        ])
        
        for customer in customers:
            writer.writerow([
                customer.id_customer,
                customer.legal_name,
                customer.name,
                customer.tax_id,
                customer.country,
                customer.state_province,
                customer.city,
                customer.address,
                customer.zip_code,
                customer.phone,
                customer.email,
                customer.contact_name,
                customer.contact_role,
                customer.category,
                customer.payment_terms,
                customer.currency,
                customer.payment_method,
                customer.bank_account,
                'Activo' if customer.status else 'Inactivo',
                customer.created_at.strftime('%d/%m/%Y %H:%M'),
                customer.updated_at.strftime('%d/%m/%Y %H:%M'),
                customer.created_by.username if customer.created_by else 'N/A'
            ])
        
        return response
    
    # Paginación
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Construir querystring sin page
    querystring = request.GET.copy()
    if 'page' in querystring:
        querystring.pop('page')
    
    filters = {
        'id_customer': id_customer,
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
    
    return render(request, 'customers/customers_list.html', context)

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            return redirect('customers:customer_create')
    else:
        form = CustomerForm()
    
    return render(request, 'customers/customer_form.html', {'form': form})

@login_required
def customer_edit(request, id):
    customer = get_object_or_404(Customer, id=id)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customers:customers_list')
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'edit_mode': True
    }
    return render(request, 'customers/customer_form.html', context)

@login_required
def customer_delete(request, id):
    customer = get_object_or_404(Customer, id=id)
    customer.delete()
    return redirect('customers:customers_list')

@login_required
def customer_bulk_upload(request):
    # Verificar permisos (permitir superusuarios)
    if not request.user.is_superuser:
        try:
            user_role = request.user.userrole_set.first()
            if not user_role or user_role.role.customers < 2:
                messages.error(request, 'You do not have permission to perform bulk uploads.')
                return redirect('customers:customers_list')
        except AttributeError:
            messages.error(request, 'You do not have permission to perform bulk uploads.')
            return redirect('customers:customers_list')
    
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
                    return render(request, 'customers/customer_bulk_upload.html', {'form': form})
            
            # Procesar CSV
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string, delimiter=';')
            
            # Limpiar BOM y espacios en cabeceras
            reader.fieldnames = [field.strip().replace('\ufeff', '') for field in reader.fieldnames]
            
            valid_customers = []
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
                customer_form = CustomerForm(cleaned_row)
                
                if customer_form.is_valid():
                    customer = customer_form.save(commit=False)
                    customer.created_by = request.user
                    valid_customers.append(customer)
                else:
                    error_rows.append({
                        'row': row_number,
                        'data': cleaned_row,
                        'errors': customer_form.errors
                    })
            
            # Guardar todos los registros válidos en una sola operación
            if valid_customers:
                Customer.objects.bulk_create(valid_customers)
            
            # Preparar contexto con el informe
            context = {
                'form': form,
                'upload_complete': True,
                'total_rows': row_number - 1,
                'successful_rows': len(valid_customers),
                'error_count': len(error_rows),
                'error_rows': error_rows
            }
            
            if valid_customers:
                messages.success(request, f'Successfully uploaded {len(valid_customers)} customers.')
            if error_rows:
                messages.warning(request, f'{len(error_rows)} rows had errors and were not uploaded.')
            
            return render(request, 'customers/customer_bulk_upload.html', context)
    else:
        form = CSVUploadForm()
    
    return render(request, 'customers/customer_bulk_upload.html', {'form': form})

@login_required
def download_template_customers(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers_template.csv"'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'id_customer', 'legal_name', 'name', 'tax_id', 'country', 
        'state_province', 'city', 'address', 'zip_code', 'phone', 
        'email', 'contact_name', 'contact_role', 'category', 
        'payment_terms', 'currency', 'payment_method', 'bank_account', 
        'status'
    ])
    
    return response

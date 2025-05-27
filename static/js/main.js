/**
 * Main JavaScript file for alabaranes-unei2
 */

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-messages .alert');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.transition = 'opacity 0.5s';
            message.style.opacity = '0';
            
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
});

// Confirm delete actions
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('button[onclick*="confirm"]');
    
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de que desea eliminar este elemento?')) {
                e.preventDefault();
                return false;
            }
        });
    });
});

// Dynamic form validation
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Por favor, complete todos los campos requeridos.');
            }
        });
    });
});

// Update total price in albaran items
function updateItemTotal(row) {
    const cantidad = parseFloat(row.querySelector('.cantidad').value) || 0;
    const precioUnitario = parseFloat(row.querySelector('.precio-unitario').value) || 0;
    const total = cantidad * precioUnitario;
    
    row.querySelector('.precio-total').textContent = '€' + total.toFixed(2);
    
    updateAlbaranTotal();
}

// Update albaran total
function updateAlbaranTotal() {
    const totals = document.querySelectorAll('.precio-total');
    let sum = 0;
    
    totals.forEach(function(total) {
        const value = parseFloat(total.textContent.replace('€', '')) || 0;
        sum += value;
    });
    
    const totalElement = document.querySelector('.albaran-total');
    if (totalElement) {
        totalElement.textContent = '€' + sum.toFixed(2);
    }
}

// Add ingredient to plato
function addIngredientToPlato(platoId, ingredienteId, cantidad) {
    fetch(`/platos/${platoId}/ingredientes`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            ingrediente_id: ingredienteId,
            cantidad: cantidad
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error al agregar ingrediente: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al agregar ingrediente');
    });
}

// Remove ingredient from plato
function removeIngredientFromPlato(platoId, ingredienteId) {
    if (!confirm('¿Está seguro de que desea quitar este ingrediente?')) {
        return;
    }
    
    fetch(`/platos/${platoId}/ingredientes/${ingredienteId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error al quitar ingrediente: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al quitar ingrediente');
    });
}
// Service Details Data
const serviceDetails = {
    'Traffic': {
        title: '🚦 Traffic Management System',
        body: `
            <p><strong>Overview:</strong> Our AI-driven traffic system monitors over 5,000 sensors across the city.</p>
            <ul>
                <li><strong>Real-time Routing:</strong> Dynamic adjustment of signal timings based on vehicle density.</li>
                <li><strong>Emergency Priority:</strong> Automated green paths for emergency vehicles (Ambulance, Fire).</li>
                <li><strong>Incident Detection:</strong> Instant alerts for road accidents and breakdowns.</li>
            </ul>
        `
    },
    'Water': {
        title: '💧 Water Supply & Quality',
        body: `
            <p><strong>Overview:</strong> Smart sensors monitor water pressure and quality in real-time.</p>
            <ul>
                <li><strong>Leak Detection:</strong> Acoustic sensors identify pipe bursts within seconds.</li>
                <li><strong>Quality Control:</strong> PH and chemical monitoring available via public API.</li>
                <li><strong>Consumption Analytics:</strong> View your household usage via the resident portal.</li>
            </ul>
        `
    },
    'Electricity': {
        title: '⚡️ Smart Grid & Energy',
        body: `
            <p><strong>Overview:</strong> A decentralized power grid integrating solar, wind, and traditional sources.</p>
            <ul>
                <li><strong>Outage Prevention:</strong> Self-healing grid technology reroutes power during failures.</li>
                <li><strong>Load Balancing:</strong> Incentives for off-peak electricity usage.</li>
                <li><strong>Storage:</strong> Integration with city-wide battery storage facilities.</li>
            </ul>
        `
    }
};

// --- Modal Functions ---

function showServiceDetails(service) {
    const details = serviceDetails[service];
    document.getElementById('modal-title').innerHTML = details.title;
    document.getElementById('modal-body').innerHTML = details.body;
    document.getElementById('serviceModal').style.display = 'block';
}

function confirmRequest(service) {
    document.getElementById('confirm-msg').innerText = `Do you want to request the ${service} service for your area?`;
    document.getElementById('confirmModal').style.display = 'block';
    
    // Set up confirm button action
    document.getElementById('confirm-btn').onclick = function() {
        submitRequest(service);
    };
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}

// --- AJAX Requests ---

function submitRequest(service) {
    fetch('/request_service', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ service_name: service }),
    })
    .then(response => response.json())
    .then(data => {
        closeModal('confirmModal');
        if (data.success) {
            alert('Success: ' + data.message);
            location.reload(); // Refresh to show new request in history
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
}

function updateStatus(requestId, newStatus) {
    if (!confirm(`Are you sure you want to mark this request as ${newStatus}?`)) return;

    fetch('/update_request_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            request_id: requestId,
            status: newStatus 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Status Updated!');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred.');
    });
}

function deleteUser(userId, username) {
    if (!confirm(`WARNING: Are you sure you want to delete user "${username}"? All their service requests will also be removed.`)) {
        return;
    }

    fetch('/delete_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            user_id: userId
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Success: ' + data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred.');
    });
}

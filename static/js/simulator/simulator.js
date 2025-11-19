// static/simulator/simulator.js

async function runSimulation() {
    // Get inputs
    const totalVisitors = parseInt(document.getElementById('totalVisitors').value);
    const dailyVisitors = parseInt(document.getElementById('dailyVisitors').value);
    
    // Get variants (manual or CSV)
    const variants = getVariants();
    
    if (variants.length < 2) {
        alert('Need at least 2 variants');
        return;
    }
    
    // Show loading
    document.getElementById('placeholder').classList.add('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    
    try {
        // Call API
        const response = await fetch('/api/v1/simulator/simulate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                total_visitors: totalVisitors,
                daily_visitors: dailyVisitors,
                variants: variants
            })
        });
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        alert('Simulation failed: ' + error.message);
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

function displayResults(data) {
    // Winner
    document.getElementById('winnerName').textContent = data.winner_variant || 'Still testing...';
    document.getElementById('winnerDay').textContent = 
        data.winner_detected_at_day 
        ? `Detected on day ${data.winner_detected_at_day} of ${data.days_run}`
        : `Needs more data (${data.days_run} days so far)`;
    
    // Benefit
    document.getElementById('benefit').textContent = 
        `+${data.benefit_analysis.additional_conversions} conversions`;
    document.getElementById('benefitPercent').textContent = 
        `${data.benefit_analysis.improvement_percentage}% improvement vs uniform split`;
    
    // Chart
    createChart(data);
    
    // Variant stats
    createVariantStats(data.variants_data);
    
    // Show results
    document.getElementById('results').classList.remove('hidden');
}

function createChart(data) {
    const ctx = document.getElementById('allocationChart');
    
    // Extract daily data
    const days = data.daily_stats.map(d => `Day ${d.day}`);
    const variantNames = Object.keys(data.daily_stats[0].cumulative_allocations);
    
    const datasets = variantNames.map((name, i) => ({
        label: name,
        data: data.daily_stats.map(d => d.cumulative_allocations[name]),
        borderColor: `hsl(${i * 360 / variantNames.length}, 70%, 50%)`,
        backgroundColor: `hsl(${i * 360 / variantNames.length}, 70%, 50%, 0.1)`,
        tension: 0.4
    }));
    
    new Chart(ctx, {
        type: 'line',
        data: { labels: days, datasets },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Traffic Allocation Over Time'
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function createVariantStats(variants) {
    const container = document.getElementById('variantStats');
    container.innerHTML = '<h3 class="font-bold mb-4">Variant Performance</h3>';
    
    variants.forEach(v => {
        const percentage = (v.final_probability * 100).toFixed(1);
        container.innerHTML += `
            <div class="border-l-4 border-blue-500 pl-4 py-2 mb-3">
                <div class="font-semibold">${v.name}</div>
                <div class="text-sm text-gray-600">
                    ${v.allocations} visitors • ${v.conversions} conversions • ${(v.observed_cr * 100).toFixed(2)}% CR
                </div>
                <div class="text-sm font-medium text-blue-600">
                    ${percentage}% probability of being best
                </div>
            </div>
        `;
    });
}

function getVariants() {
    // Parse manual inputs
    const inputs = document.querySelectorAll('#variantInputs > div');
    return Array.from(inputs).map(div => {
        const [nameInput, crInput] = div.querySelectorAll('input');
        return {
            name: nameInput.value || 'Unnamed',
            conversion_rate: parseFloat(crInput.value || 0) / 100
        };
    }).filter(v => v.name && v.conversion_rate > 0);
}

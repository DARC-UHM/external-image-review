import { depthColor } from './util.js';

const map = L.map('map', { worldCopyJump: false });
const bounds = L.latLngBounds();
const legend = L.control({ position: 'bottomright' });
const markers = [];

// esri ocean basemap & labels
L.esri.basemapLayer('Oceans').addTo(map);
L.esri.basemapLayer('OceansLabels').addTo(map);

legend.onAdd = function () {
    const div = L.DomUtil.create('div', 'legend');

    div.innerHTML = `
        <h4>Depth (m)</h4>

        <div><span class="legend-color" style="background:#fc0d1b"></span> 0–199</div>
        <div><span class="legend-color" style="background:#fffd38"></span> 200–399</div>
        <div><span class="legend-color" style="background:#19af54"></span> 400–599</div>
        <div><span class="legend-color" style="background:#0b24fb"></span> 600–799</div>
        <div><span class="legend-color" style="background:#ca1ec9"></span> 800–999</div>
        <div><span class="legend-color" style="background:#000000"></span> 1000+</div>
        
        <hr>
        <div class="legend-count">
            ${formatNumber(annotations.length)}
            ${annotations.length === 1 ? 'observation' : 'observations'}
        </div>

    `;

    return div;
};

legend.addTo(map);

map.on('popupopen', (e) => {
    const img = e.popup.getElement().querySelector('.popup-image img');
    if (!img) return;

    const spinner = e.popup.getElement().querySelector('.popup-spinner');

    const loaded = () => {
        img.classList.add('loaded');
        spinner.remove();
    };

    if (img.complete) {
        loaded();
    } else {
        img.addEventListener('load', loaded, { once: true });
    }
});

// plot points
annotations.forEach(annotation => {

    const lng = normalizeLng(annotation.lng);

    const latlng = [annotation.lat, lng];

    bounds.extend(latlng);

    const marker = L.circleMarker(latlng, {
        radius: 6,
        color: '#001f23',
        fillColor: depthColor(annotation.depth_m),
        fillOpacity: 1,
        weight: 1
    })
        .addTo(map)
        .bindPopup(getPopupHtml(annotation));

    markers.push(marker);
});


if (annotations.length === 0) {
    map.setView([20, 0], 2);
} else {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 6 });
}

map.on('moveend', updateObservationCount);
updateObservationCount();

function normalizeLng(lng) {
    return lng < 0 ? lng + 360 : lng;
}

function updateObservationCount() {
    const bounds = map.getBounds();

    const visible = markers.filter(marker =>
        bounds.contains(marker.getLatLng())
    );

    document.querySelector('.legend-count').innerHTML =
        `${formatNumber(visible.length)} ${visible.length === 1 ? 'observation' : 'observations'}`;
}


function getPopupHtml(annotation) {
    return `
        <div class="popup">
            ${annotation.image_url
                ? `<div class="popup-image">
                    <div class="popup-spinner"></div>   
                            <a href="${annotation.image_url}" target="_blank">
                                <img src="${annotation.image_url}?thumbnail=true" alt="${annotation.scientific_name}" />
                            </a>
                           </div>`
                : ""
            }
            <div class="popup-title">
                ${annotation.scientific_name}
            </div>
            

            <table class="popup-table">
                <tr>
                    <td>Depth</td>
                    <td>${annotation.depth_m ?? "—"} m</td>
                </tr>
                <tr>
                    <td>Expedition</td>
                    <td>${annotation.expedition_name}</td>
                </tr>
                <tr>
                    <td>Survey Type</td>
                    <td>${getFormattedSurveyType(annotation.survey_type)}</td>
                </tr>
                <tr>
                    <td>Count</td>
                    <td>${annotation.count ?? "—"}</td>
                </tr>
                <tr>
                    <td>Timestamp</td>
                    <td>${annotation.observation_timestamp}</td>
                </tr>
            </table>
        </div>
    `;
}

function getFormattedSurveyType(surveyType) {
    if (surveyType === 'exploratory') {
        return 'Sub Dive (Exploratory)';
    }
    if (surveyType === 'transect') {
        return 'Sub Dive (Transect)';
    }
    return 'Baited Dropcam';
}

function formatNumber(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

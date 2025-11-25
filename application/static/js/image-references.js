const slideshows = {}; // { fullName: { currentIndex, maxIndex, depths } }
const taxonRanks = ['phylum', 'class', 'order', 'family', 'genus'];
const phyla = {};

let filteredImageReferences = [...imageReferences];
let phylogenyFilter = {};
let keywordFilter = '';
let idTypeFilter = 'any';
let sortKey = 'default';

$(document).ready(() => {
    $('body').tooltip({ selector: '[data-toggle=tooltip]', trigger : 'hover' });
    window.addEventListener('popstate', function () {
        $('[data-toggle="tooltip"]').tooltip('dispose');
    });
    keywordFilter = $('#keywordFilterInput').val();
    populatePhyla();
    updatePhylogenyFilterSelects();
    updateImageGrid();
    $('#keywordFilterInput').on('input', (e) => {
        keywordFilter = e.target.value;
        $('[data-toggle="tooltip"]').tooltip('dispose');
        updateFilter();
    });
    $('#keywordFilterInput').on('focus', () => {
        $('#filterContainer').css('border', '1px solid #ffffff25');
    });
    $('#keywordFilterInput').on('blur', () => {
        $('#filterContainer').css('border', '1px solid var(--darc-bg)');
    });
    $('#sortSelect').on('change', (e) => {
        sortKey = e.target.value;
        updateImageGrid();
    });
    $('#sortSelectSmall').on('change', (e) => {
        sortKey = e.target.value;
        updateImageGrid();
    });
    $('#idTypeFilterSelect').on('change', (e) => {
        idTypeFilter = e.target.value;
        updateFilter();
    });
});

function updateFilter() {
    updatePhylogenyFilterSelects();
    updateImageGrid();
}

function updateIdTypeFilter(newFilter) {
    idTypeFilter = newFilter;
    updateFilter();
}

window.updateIdTypeFilter = updateIdTypeFilter;

function updateImageGrid() {
    $('#imageGrid').empty();
    filteredImageReferences = [...imageReferences];
    for (const key of Object.keys(phylogenyFilter)) {
        filteredImageReferences = filteredImageReferences.filter((imageRef) => {
            return imageRef[key === 'class' ? 'class_name' : key]?.toLowerCase().includes(phylogenyFilter[key].toLowerCase());
        });
    }
    if (keywordFilter) {
        const imageRefLevelFilteredImages = filteredImageReferences.filter((imageRef) => {
            const properties = [
                'scientific_name',
                'phylum',
                'class_name',
                'order',
                'family',
                'genus',
                'species',
                'tentative_id',
                'morphospecies',
            ];
            return properties.some((property) => imageRef[property]?.toLowerCase().includes(keywordFilter.toLowerCase()));
        });
        const photoRecordLevelFilteredImages = filteredImageReferences.filter((imageRef) => {
            return imageRef.photo_records.some((photoRecord) => {
                return photoRecord.location_short_name?.toLowerCase().includes(keywordFilter.toLowerCase())
                    || photoRecord.location_long_name?.toLowerCase().includes(keywordFilter.toLowerCase())
            });
        });
        filteredImageReferences = [...new Set([...imageRefLevelFilteredImages, ...photoRecordLevelFilteredImages])];
    }
    switch (idTypeFilter) {
        case 'morphoOrTentative':
            filteredImageReferences = filteredImageReferences.filter((imageRef) => imageRef.tentative_id || imageRef.morphospecies);
            break;
        case 'morphospecies':
            filteredImageReferences = filteredImageReferences.filter((imageRef) => imageRef.morphospecies);
            break;
        case 'tentativeId':
            filteredImageReferences = filteredImageReferences.filter((imageRef) => imageRef.tentative_id);
            break;
        default:
            break;
    }
    // move all records missing specified property to bottom
    const recordsMissingSortKey = filteredImageReferences.filter((anno) => anno[sortKey]);
    switch (sortKey) {
        case 'phylum':
            filteredImageReferences = filterAndSort(filteredImageReferences, 'species');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'genus');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'family');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'order');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'class');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'phylum');
            break;
        case 'class':
            filteredImageReferences = filterAndSort(filteredImageReferences, 'species');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'genus');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'family');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'order');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'class');
            break;
        case 'order':
            filteredImageReferences = filterAndSort(filteredImageReferences, 'species');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'genus');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'family');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'order');
            break;
        case 'family':
            filteredImageReferences = filterAndSort(filteredImageReferences, 'species');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'genus');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'family');
            break;
        case 'genus':
            filteredImageReferences = filterAndSort(filteredImageReferences, 'species');
            filteredImageReferences = filterAndSort(filteredImageReferences, 'genus');
            break;
        case 'species':
            filteredImageReferences = filterAndSort(filteredImageReferences, 'species');
            break;
        case 'depth':
            filteredImageReferences.sort((a, b) => a.photo_records[0].depth_m - b.photo_records[0].depth_m);
            break;
        default:
            break;
    }
    filteredImageReferences = recordsMissingSortKey.concat(filteredImageReferences.filter((record) => !record[sortKey]));
    filteredImageReferences.forEach((imageRef) => {
        const fullName = formattedName(imageRef);
        const photoKey = fullName.replaceAll(' ', '-');
        slideshows[photoKey] = { currentIndex: 0, maxIndex: imageRef.photo_records.length - 1, depths: [] };
        $('#imageGrid').append(`
            <div class="col-lg-3 col-md-4 col-sm-6 col-12 p-2">
                <div class="rounded-3 small" style="background: #1b1f26;">
                    <div class="py-2 rounded-top m-0" style="background: #171a1f;">
                        <div
                            class="mx-auto"
                            style="width: fit-content;"
                            data-toggle="tooltip"
                            data-bs-placement="right"
                            data-bs-html="true"
                            title="<div class='text-start' style='max-width: none; white-space: nowrap;'>
                                     Phylum: ${imageRef.phylum ?? 'N/A'}<br>
                                     Class: ${imageRef.class_name ?? 'N/A'}<br>
                                     Order: ${imageRef.order ?? 'N/A'}<br>
                                     Family: ${imageRef.family ?? 'N/A'}<br>
                                     Genus: ${imageRef.genus ? `<i>${imageRef.genus}</i>` : 'N/A'}<br>
                                     Species: ${imageRef.species ? `<i>${imageRef.species}</i>` : 'N/A'}
                                   </div>"
                        >
                            ${fullName}
                        </div>
                    </div>
                    <div
                        class="d-flex justify-content-center w-100 position-relative"
                    >
                        ${imageRef.photo_records.map((photoRecord, index) => {
                            const imageBaseUrl = 'https://hurlstor.soest.hawaii.edu:5000/image-reference/image/';
                            return `
                                <div id="${photoKey}-${index}" style="display: ${index > 0 ? 'none' : 'block'}; width: 100%">
                                    <div class="position-relative">
                                        <a href="${imageBaseUrl}${photoRecord.image_name}" target="_blank">
                                            <img
                                                src="${imageBaseUrl}${photoRecord.thumbnail_name}"
                                                class="w-100"
                                                alt="${fullName}"
                                            >
                                        </a>
                                        <div
                                            class="position-absolute"
                                            style="right: 0; bottom: -1.5rem; width: 1.5rem; height: 1.5rem; background: ${depthColor(photoRecord.depth_m)}; border-radius: 0 0 0.25rem 0;"
                                            data-toggle="tooltip"
                                            data-bs-placement="right"
                                            data-bs-html="true"
                                            title="${photoRecord.depth_m ? `Depth: ${photoRecord.depth_m}m` : 'Depth not available for this image'}"
                                        >
                                            ${photoRecord.depth_m >= 1000
                                                ? `
                                                    <div
                                                        style="width: 1.5rem; height: 0.4rem; background: #a6a6a6; margin-top: ${photoRecord.depth_m > 5000 ? '1.1rem' : photoRecord.depth_m > 3000 ? '0.55rem' : '0' }; border-radius: 0 0 ${photoRecord.depth_m > 5000 ? '0.25rem' : '0'} 0;"
                                                    ></div>
                                                ` : ''
                                            }
                                        </div>
                                        <div
                                            class="position-absolute d-flex align-items-center"
                                            style="height: 1.5rem; left: 0; bottom: -1.5rem; font-size: 0.75rem;"
                                        >
                                            <div
                                                class="ms-2 my-auto"
                                                data-toggle="tooltip"
                                                data-bs-placement="right"
                                                data-bs-html="true"
                                                title="${photoRecord.location_long_name}"
                                            >
                                                ${photoRecord.location_short_name}
                                            </div>
                                        </div>
                                        ${photoRecord.video_url
                                            ? `
                                                <div class="position-absolute" style="left: 0; top: 0;">
                                                    <a href="${photoRecord.video_url}" target="_blank" class="video-overlay-link px-2 py-1">
                                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                                            <path fill-rule="evenodd" d="M0 5a2 2 0 0 1 2-2h7.5a2 2 0 0 1 1.983 1.738l3.11-1.382A1 1 0 0 1 16 4.269v7.462a1 1 0 0 1-1.406.913l-3.111-1.382A2 2 0 0 1 9.5 13H2a2 2 0 0 1-2-2zm11.5 5.175 3.5 1.556V4.269l-3.5 1.556zM2 4a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h7.5a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1z"/>
                                                        </svg>
                                                    </a>
                                                </div>
                                            ` : ''
                                        }
                                        ${imageRef.photo_records.length > 1
                                            ? `
                                                <div
                                                    class="position-absolute d-flex align-items-center w-100 pe-none"
                                                    style="height: 1.5rem; bottom: -1.5rem; font-size: 0.75rem;"
                                                >
                                                    <div class="w-100 text-center">
                                                        ${index + 1} / ${imageRef.photo_records.length}
                                                    </div>
                                                </div>
                                            ` : ''
                                        }
                                    </div>
                                </div>
                            `;
                        }).join('')}
                        <a
                            class="photo-slideshow-arrows photo-slideshow-prev"
                            onclick="changeSlide('${photoKey}', -1)"
                            ${imageRef.photo_records.length < 2 ? "hidden" : ""}
                        >
                            &#10094;
                        </a>
                        <a
                            class="photo-slideshow-arrows photo-slideshow-next"
                            onclick="changeSlide('${photoKey}', 1)"
                            ${imageRef.photo_records.length < 2 ? "hidden" : ""}
                        >
                            &#10095;
                        </a>
                    </div>
                    <div style="height: 1.5rem;"></div>
                </div>
            </div>
        `);
    });
}

const filterAndSort = (list, key) => {
    let filtered = list.filter((anno) => anno[key]);
    filtered = filtered.sort((a, b) => (a[key] > b[key]) ? 1 : ((b[key] > a[key]) ? -1 : 0));
    return filtered.concat(list.filter((anno) => !anno[key]));
}

function populatePhyla() {
    // populate available phylogeny (probs should just save this info on the backend)
    imageReferences.forEach((imageRef) => {
        if (!phyla[imageRef.phylum]) {
            phyla[imageRef.phylum] = {};
        }
        if (imageRef.class_name && !phyla[imageRef.phylum][imageRef.class_name]) {
            phyla[imageRef.phylum][imageRef.class_name] = {};
        }
        if (imageRef.order && !phyla[imageRef.phylum][imageRef.class_name][imageRef.order]) {
            phyla[imageRef.phylum][imageRef.class_name][imageRef.order] = {};
        }
        if (imageRef.family && !phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family]) {
            phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family] = {};
        }
        if (imageRef.genus && !phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family][imageRef.genus]) {
            phyla[imageRef.phylum][imageRef.class_name][imageRef.order][imageRef.family][imageRef.genus] = {};
        }
    });
}

function addPhylogenyFilterSelect(taxonRank, selectedValue) {
    let rankOptions;
    switch (taxonRank) {
        case 'phylum':
            rankOptions = (Object.keys(phyla));
            break;
        case 'class':
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum]));
            break;
        case 'order':
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum][phylogenyFilter.class]));
            break;
        case 'family':
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum][phylogenyFilter.class][phylogenyFilter.order]));
            break;
        case 'genus':
            rankOptions = (Object.keys(phyla[phylogenyFilter.phylum][phylogenyFilter.class][phylogenyFilter.order][phylogenyFilter.family]));
            break;
        default:
            rankOptions = [];
    }
    $('#filterList').append(`
        <span id="${taxonRank}Filter">
            <span class="position-relative">
                <select
                    id="${taxonRank}FilterSelect"
                    onchange="updatePhylogenyFilter('${taxonRank}')"
                    style="background: var(--darc-input-bg); height: 2rem;"
                >
                    <option value="all">Any ${taxonRank}</option>
                    ${rankOptions.map((option) =>
        `<option value="${option}" ${selectedValue === option ? 'selected' : ''}>${option}</option>`
    )}
                </select>
                <span class="position-absolute dropdown-chev">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chevron-down" viewBox="0 0 16 16">
                      <path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/>
                    </svg>
                </span>
            </span>
        </span>
    `);
}

function updatePhylogenyFilter(taxonRank) {
    const selected = $(`#${taxonRank}FilterSelect`).val();
    if (selected === 'all') {
        delete phylogenyFilter[taxonRank];
    } else {
        phylogenyFilter[taxonRank] = selected;
    }
    // remove all lower ranks
    for (let i = taxonRanks.indexOf(taxonRank) + 1; i < taxonRanks.length; i++) {
        delete phylogenyFilter[taxonRanks[i]];
    }
    updateFilter();
}

window.updatePhylogenyFilter = updatePhylogenyFilter;

function updatePhylogenyFilterSelects() {
    $('#filterList').empty();
    for (const filterName of Object.keys(phylogenyFilter)) {
        addPhylogenyFilterSelect(filterName, phylogenyFilter[filterName]);
        if (filterName !== 'genus') {
            $('#filterList').append('→');
        }
    }
    for (const taxonRank of taxonRanks) {
        if (!phylogenyFilter[taxonRank]) {
            addPhylogenyFilterSelect(taxonRank, '');
            break;
        }
    }
}

function changeSlide(photoKey, slideMod) {
    const { currentIndex, maxIndex } = slideshows[photoKey];
    const slideIndex = (currentIndex + slideMod + maxIndex + 1) % (maxIndex + 1);
    slideshows[photoKey].currentIndex = slideIndex;
    // hide all slides except the current one
    for (let i = 0; i <= slideshows[photoKey].maxIndex; i++) {
        document.getElementById(`${photoKey}-${i}`).style.display = i === slideIndex ? 'block' : 'none';
    }
}

window.changeSlide = changeSlide;

const formattedName = (imageRef) => {
    const italicizeScientificName = imageRef.species || imageRef.genus;
    const italicizeSuffix = italicizeScientificName || imageRef.family;
    let nameSuffix = '';
    if (imageRef.tentative_id) {
        nameSuffix += ` (${italicizeSuffix || italicizeScientificName
            ? italicizedSuffix(imageRef.tentative_id) : imageRef.tentative_id}${
            imageRef.tentative_id.includes('cf.') ? '' : '?'
        })`;
    } else if (imageRef.morphospecies) {
        nameSuffix += ` (${italicizeSuffix || italicizeScientificName
            ? italicizedSuffix(imageRef.morphospecies) : imageRef.morphospecies})`;
    }
    if (italicizeScientificName) {
        return `<i>${imageRef.scientific_name}</i>${nameSuffix}`;
    }
    return `${imageRef.scientific_name}${nameSuffix}`;
}

const italicizedSuffix = (suffix) => {
    if (suffix.includes('cf.')) {
        const parts = suffix.split('cf.');
        return `<i>${parts[0]}</i>cf.<i>${parts[1]}</i>`;
    }
    return `<i>${suffix}</i>`;
};

const depthColor = (depthM) => {
    if (!depthM) {
        return '#00000000';
    }
    if (depthM >= 1000) {
        return '#000';
    } else if (depthM >= 800) {
        return '#ca1ec9';
    } else if (depthM >= 600) {
        return '#0b24fb';
    } else if (depthM >= 400) {
        return '#19af54';
    } else if (depthM >= 200) {
        return '#fffd38';
    }
    return '#fc0d1b';
}

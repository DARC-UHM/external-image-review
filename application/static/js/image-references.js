import { depthColor } from './util.js';

const BASE_URL = 'https://darc.soest.hawaii.edu/';
const slideshows = {}; // { fullName: { currentIndex, maxIndex, depths } }
const phyla = {};
const canEdit = window.canEdit ?? false;
const trashIconSvg = (dimensions) =>
    `<svg xmlns="http://www.w3.org/2000/svg" height="${dimensions}px" viewBox="0 -960 960 960" width="${dimensions}px" fill="currentColor"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"/></svg>`;
const refreshIconSvg = (dimensions) =>
    `<svg xmlns="http://www.w3.org/2000/svg" height="${dimensions}px" viewBox="0 -960 960 960" width="${dimensions}px" fill="currentColor"><path d="M480-160q-134 0-227-93t-93-227q0-134 93-227t227-93q69 0 132 28.5T720-690v-110h80v280H520v-80h168q-32-56-87.5-88T480-720q-100 0-170 70t-70 170q0 100 70 170t170 70q77 0 139-44t87-116h84q-28 106-114 173t-196 67Z"/></svg>`;
const mapIconSvg = (dimensions) =>
    `<svg xmlns="http://www.w3.org/2000/svg" height="${dimensions}px" viewBox="0 -960 960 960" width="${dimensions}px" fill="currentColor"><path d="M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q76 0 144 26.5T745-780q53 47 88 111t44 139q-20-11-42-18t-45-10q-19-75-68.5-132T600-776v16q0 33-23.5 56.5T520-680h-80v80q0 17-11.5 28.5T400-560h-80v80h260q-29 32-44.5 72T520-324q0 78 31 121t80 94q-36 14-74 21.5T480-80Zm-40-82v-78q-33 0-56.5-23.5T360-320v-40L168-552q-3 18-5.5 36t-2.5 36q0 121 79.5 212T440-162Zm362.5-115.5Q820-295 820-320t-17-42.5Q786-380 761-380q-26 0-43.5 17.5T700-320q0 25 17.5 42.5T760-260q25 0 42.5-17.5ZM760-80q-3 0-16-11l-4-7q-22-38-55.5-67.5T627-232q-14-20-20.5-43.5T600-324q0-66 47-111t113-45q66 0 113 45t47 111q0 25-6.5 48.5T893-232q-24 37-57.5 66.5T780-98l-4 7q-2 5-6.5 8t-9.5 3Z"/></svg>`;

window.refreshImageReference = window.refreshImageReference ?? ((imageRefId) => {});

let phylogenyFilter = 'any';
let keywordFilter = '';
let idTypeFilter = 'any';
let baitInteractionFilter = 'any';
let sortKey = 'default';

$(document).ready(() => {
    $('body').tooltip({ selector: '[data-toggle=tooltip]', trigger : 'hover' });
    window.addEventListener('popstate', function () {
        $('[data-toggle="tooltip"]').tooltip('dispose');
    });
    keywordFilter = $('#keywordFilterInput').val();
    populatePhyla();
    $("#phylogenyTree").append(renderTree(phyla));
    updateImageGrid();
    $('#keywordFilterInput').on('input', (e) => {
        keywordFilter = e.target.value;
        $('[data-toggle="tooltip"]').tooltip('dispose');
        updateImageGrid();
    });
    $('#keywordFilterInput').on('focus', () => {
        $('#searchAndFilterContainer').css('border', '1px solid #ffffff25');
    });
    $('#keywordFilterInput').on('blur', () => {
        $('#searchAndFilterContainer').css('border', '1px solid var(--darc-bg)');
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
        updateImageGrid();
    });
    $('#baitInteractionFilterSelect').on('change', (e) => {
        baitInteractionFilter = e.target.value;
        updateImageGrid();
    });
    $("#phylogenyTree").on("click", ".tree-toggle", function () {
        const $toggle = $(this);
        const $childUl = $toggle.closest("li").children("ul");
        $childUl.toggleClass("d-none");
        $toggle.toggleClass("tree-toggle-open");
    });
});

function toggleSidebar() {
    $('#filterSidebar').toggleClass('collapsed');
}

window.toggleSidebar = toggleSidebar;

function updatePhylogenyFilter(newFilter) {
    phylogenyFilter = newFilter;
    $('.phylo-label').removeClass('phylo-label-active');
    $(`.phylo-label[data-filter="${newFilter}"]`).addClass('phylo-label-active');
    updateImageGrid();
}

window.updatePhylogenyFilter = updatePhylogenyFilter;

function updateIdTypeFilter(newFilter) {
    idTypeFilter = newFilter;
    updateImageGrid();
}

window.updateIdTypeFilter = updateIdTypeFilter;

function updateImageGrid() {
    $('#imageGrid').empty();

    const filteredImageReferences = getFilteredImageRefs([...imageReferences]);
    const filterdAndSortedImageRefs = getSortedImageRefs(filteredImageReferences);

    const total = imageReferences.length;
    const filtered = filterdAndSortedImageRefs.length;
    $('#resultsCount').text(filtered === total ? `${total} taxa` : `${filtered} of ${total} taxa`);
    if (filterdAndSortedImageRefs.length === 0) {
        $('#imageGrid').html(`
            <div class="col-12 text-center py-5 text-muted">
                No taxa match your current filters.
            </div>
        `);
        return;
    }

    filterdAndSortedImageRefs.forEach((imageRef) => {
        addItemToGrid(imageRef);
    });
}

window.updateImageGrid = updateImageGrid;

function getFilteredImageRefs(imageRefs) {
    let filteredImageReferences = [...imageRefs];
    if (phylogenyFilter !== 'any') {
        filteredImageReferences = filteredImageReferences.filter((imageRef) => {
            const properties = [
                'phylum',
                'class_name',
                'order',
                'family',
                'genus',
                'species',
            ];
            return properties.some((property) => imageRef[property]?.toLowerCase().includes(phylogenyFilter.toLowerCase()));
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
                'attracted',
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
    switch (baitInteractionFilter) {
        case 'attracted':
            filteredImageReferences = filteredImageReferences.filter((imageRef) => {
                return imageRef.photo_records.some((photoRecord) => photoRecord.attracted);
            });
            break;
        case 'notAttracted':
            filteredImageReferences = filteredImageReferences.filter((imageRef) => {
                return imageRef.photo_records.some((photoRecord) => !photoRecord.attracted);
            });
            break;
        default:
            break;
    }

    const anyActive = phylogenyFilter !== 'any'
            || keywordFilter !== ''
            || idTypeFilter !== 'any'
            || baitInteractionFilter !== 'any';
    $('#filterActiveDot').toggleClass('d-none', !anyActive);

    return filteredImageReferences;
}

function getSortedImageRefs(imageRefs) {
    let sortedImageRefs = [...imageRefs];
    switch (sortKey) {
        case 'phylum':
            sortedImageRefs = filterAndSort(sortedImageRefs, 'species');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'genus');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'family');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'order');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'class');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'phylum');
            break;
        case 'class':
            sortedImageRefs = filterAndSort(sortedImageRefs, 'species');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'genus');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'family');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'order');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'class');
            break;
        case 'order':
            sortedImageRefs = filterAndSort(sortedImageRefs, 'species');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'genus');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'family');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'order');
            break;
        case 'family':
            sortedImageRefs = filterAndSort(sortedImageRefs, 'species');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'genus');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'family');
            break;
        case 'genus':
            sortedImageRefs = filterAndSort(sortedImageRefs, 'species');
            sortedImageRefs = filterAndSort(sortedImageRefs, 'genus');
            break;
        case 'species':
            sortedImageRefs = filterAndSort(sortedImageRefs, 'species');
            break;
        case 'depth':
            sortedImageRefs.sort((a, b) => {
                const aDepth = a.photo_records[0]?.depth_m;
                const bDepth = b.photo_records[0]?.depth_m;
                if (aDepth == null && bDepth == null) return 0;
                if (aDepth == null) return 1;
                if (bDepth == null) return -1;
                return aDepth - bDepth;
            });
            break;
        default:
            break;
    }
    return sortedImageRefs;
}

const filterAndSort = (list, key) => {
    let filtered = list.filter((anno) => anno[key]);
    filtered = filtered.sort((a, b) => (a[key] > b[key]) ? 1 : ((b[key] > a[key]) ? -1 : 0));
    return filtered.concat(list.filter((anno) => !anno[key]));
}

function addItemToGrid(imageRef) {
    const fullName = formattedName(imageRef);
    const photoKey = fullName.replaceAll(' ', '-');
    slideshows[photoKey] = { currentIndex: 0, maxIndex: imageRef.photo_records.length - 1, depths: [] };
    $('#imageGrid').append(`
        <div class="col-lg-3 col-md-4 col-sm-6 col-12 p-2">
            <div class="image-ref-card rounded-3 small">
                <div class="image-ref-card-header rounded-top m-0 position-relative">
                    ${cardTitle(imageRef, fullName)}
                    ${canEdit ? editButtons(imageRef) : ''}
                    ${observationsLink(imageRef.scientific_name)}
                </div>
                <div class="d-flex justify-content-center w-100 position-relative">
                    ${imageRef.photo_records.map((photoRecord, index) => 
                        getPhotoSlideshow(imageRef, photoRecord, fullName, photoKey, index)
                    ).join('')}
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
}

const cardTitle = (imageRef, fullName) => {
    return `
        <div
            class="mx-auto text-center px-2"
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
        </div>`;
}

const editButtons = (imageRef) => {
    return `
        <div class="position-absolute top-0 end-0 my-auto btn pe-2">
            <button
                onclick="refreshImageReference('${imageRef.id}');"
                class="header-link"
                style="background: none; border: none; outline: none; box-shadow: none;"
                data-toggle="tooltip"
                title="Refresh image reference details from Tator"
            >
                ${refreshIconSvg(18)}
            </button>
            <button
                class="header-link"
                style="background: none; border: none; outline: none; box-shadow: none;"
                data-bs-toggle="modal"
                data-bs-target="#deleteImageReferenceModal"
                data-anno='${JSON.stringify(imageRef)}'
                data-toggle="tooltip"
                title="Delete image reference"
            >
                ${trashIconSvg(18)}
            </button>
        </div>`;
}

const observationsLink = (scientificName) => {
    return `
        <div class="position-absolute top-0 start-0 btn">
            <a
                href="${BASE_URL}observations?name=${scientificName}"
                target="_blank"
                class="header-link"
                data-toggle="tooltip"
                title="View recorded observations of this animal on map"
             >
                ${mapIconSvg(18)}
            </a>
        </div>`;
}

function getPhotoSlideshow(imageRef, photoRecord, fullName, photoKey, index) {
    const imageUrl = `${BASE_URL}image-reference/image`;
    return `
        <div id="${photoKey}-${index}" style="display: ${index > 0 ? 'none' : 'block'}; width: 100%">
            <div class="position-relative">
                <a href="${imageUrl}/${photoRecord.image_name}" target="_blank">
                    <img
                        src="${imageUrl}/${photoRecord.thumbnail_name}"
                        class="w-100"
                        alt="${fullName}"
                    >
                </a>
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
                ${depthIndicator(photoRecord.depth_m)}
                ${locationIndicator(photoRecord.location_long_name, photoRecord.location_short_name)}
                ${imageRef.photo_records.length > 1
                    ? `
                        <div
                            class="position-absolute d-flex align-items-center w-100 image-ref-card-footer-text"
                            style="height: 1.5rem; bottom: -1.5rem; font-size: 0.75rem;"
                        >
                            <div class="w-100 text-center">
                            ${canEdit ? `
                                <button
                                    class="ms-1 my-auto p-0"
                                    style="background: none; border: none; outline: none; box-shadow: none; opacity: 0.5; line-height: 1;"
                                    data-bs-toggle="modal"
                                    data-bs-target="#deleteImageReferenceModal"
                                    data-anno='${JSON.stringify(imageRef)}'
                                    data-elemental-id='${photoRecord.tator_elemental_id}'
                                    data-bs-placement="right"
                                    data-toggle="tooltip"
                                    title="Delete this photo"
                                >
                                    ${trashIconSvg(14)}
                                </button>
                            ` : ''}
                                ${index + 1} / ${imageRef.photo_records.length}
                            </div>
                        </div>
                    ` : ''
                }
            </div>
        </div>
    `;
}

const depthIndicator = (depthM) => {
    return `
        <div
            class="position-absolute"
            style="right: 0; bottom: -1.5rem; width: 1.5rem; height: 1.5rem;  z-index: 5; background: ${depthColor(depthM)}; border-radius: 0 0 0.25rem 0;"
            data-toggle="tooltip"
            data-bs-placement="right"
            data-bs-html="true"
            title="${depthM ? `Depth: ${depthM}m` : 'Depth not available for this image'}"
        >
            ${depthM >= 1000
                ? `
                    <div
                        style="width: 1.5rem; height: 0.4rem; background: #a6a6a6; margin-top: ${depthM > 5000 ? '1.1rem' : depthM > 3000 ? '0.55rem' : '0' }; border-radius: 0 0 ${depthM > 5000 ? '0.25rem' : '0'} 0;"
                    ></div>
                ` : ''
            }
        </div>`;
}

const locationIndicator = (locationLongName, locationShortName) => {
    return `
        <div
            class="position-absolute d-flex align-items-center image-ref-card-footer-text"
            style="height: 1.5rem; left: 0; bottom: -1.5rem; font-size: 0.75rem;  z-index: 5;"
        >
            <div
                class="ms-2 my-auto"
                data-toggle="tooltip"
                data-bs-placement="right"
                data-bs-html="true"
                title="${locationLongName}"
            >
                ${locationShortName}
            </div>
        </div>`;
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

function renderTree(node, path = []) {
    let html = '';

    Object.entries(node).forEach(([name, children]) => {
        const hasChildren = Object.keys(children).length > 0;
        const childHtml = hasChildren
            ? `
                <ul class="list-unstyled ms-3 d-none">
                    ${renderTree(children, [...path, name])}
                </ul>
            ` : '';

        html += `
          <li class="mb-1">
            <div class="d-flex align-items-center gap-1">
              ${hasChildren
                    ? `<span class="tree-toggle" role="button">
                           <svg xmlns="http://www.w3.org/2000/svg" height="16px" viewBox="0 -960 960 960" width="16px" fill="#aaa"><path d="M504-480 320-664l56-56 240 240-240 240-56-56 184-184Z"/></svg>
                       </span>`
                    : `<span class="tree-spacer"></span>`
              }
              <span class="phylo-label" data-filter="${name}" onclick="updatePhylogenyFilter('${name}');">
                  ${name}
              </span>
            </div>
            ${childHtml}
          </li>
        `;
    });

    return html;
}

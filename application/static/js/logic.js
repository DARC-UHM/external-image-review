// array of the slideshow indices for records that have multiple id references: [[currentIndex, maxIndex, refId], ...]
const slideshowIndices = [];

let numSlideshows = 0;
let warningOn = false; // alert "are you sure you want to navigate away from this page?"

const tempSortedComments = comments.sort((a, b) => Date.parse(a.timestamp) > Date.parse(b.timestamp)); // sort by timestamp
const sortedComments = tempSortedComments.sort((a, b) => (a.concept > b.concept) ? 1 : (b.concept > a.concept) ? -1 : 0); // sort by concept

function turnOnWarning() {
    if (!warningOn) {
        window.onbeforeunload = () => true;
        warningOn = true;
    }
}
function turnOffWarning() {
    if (warningOn) {
        window.onbeforeunload = null;
        warningOn = false;
    }
}

function plusSlides(slideshowIndex, slideMod, uuid) {
    let slideIndex = slideshowIndices[slideshowIndex][0] + slideMod;
    if (slideIndex > slideshowIndices[slideshowIndex][1]) {
        slideIndex = 1;
    } else if (slideIndex < 1) {
        slideIndex = slideshowIndices[slideshowIndex][1];
    }
    slideshowIndices[slideshowIndex][0] = slideIndex;
    // hide all slides
    for (let i = 1; i <= slideshowIndices[slideshowIndex][1]; i++) {
        document.getElementById(`${uuid}-${i - 1}`).style.display = 'none';
    }
    // show one slide
    document.getElementById(`${uuid}-${slideIndex - 1}`).style.display = 'block';

}

function addViewAllParam() {
    const url = new URL(window.location.href);
    url.searchParams.set('all', 'true');
    window.location.href = url.href;
}

async function saveComments() {
    event.preventDefault();
    $('#load-overlay').removeClass('loader-bg-hidden');
    $('#load-overlay').addClass('loader-bg');
    const formData = new FormData($('#commentForm')[0]);
    const finalFormData = new FormData();
    const commentNums = []
    const finalComments = [];
    const commentedUuids = new Set();
    const annotators = new Set();
    const sequences = new Set();
    for (const comment of formData.entries()) {
        if (comment[0].includes('comment')) {
            commentNums.push(comment[0].split('_')[1]);
        }
    }
    for (const num of commentNums) {
        const comment = formData.get(`comment_${num}`);
        const uuids = formData.getAll(`uuid_${num}`);
        if (comment) {
            for (const uuid of uuids) {
                finalComments.push({uuid, comment});
                commentedUuids.add(uuid);
            }
        }
    }
    for (const comment of sortedComments) {
        if (commentedUuids.has(comment.uuid)) {
            annotators.add(comment.annotator);
            sequences.add(comment.sequence);
        }
    }
    finalFormData.append('reviewer', formData.get('reviewer'));
    finalFormData.append('annotators', JSON.stringify([...annotators]));
    finalFormData.append('sequences', JSON.stringify([...sequences]));
    finalFormData.append('comments', JSON.stringify(finalComments));
    const res = await fetch('/save-comments', {
        method: 'POST',
        body: finalFormData,
    });
    if (res.ok && res.redirected) {
        window.location.href = res.url;
    } else {
        $('#failedCommentFlash')[0].style.display = 'block';
    }
    $('#load-overlay').removeClass('loader-bg');
    $('#load-overlay').addClass('loader-bg-hidden');
}

$(document).ready(() => {
    $('textarea').on('input', () => turnOnWarning()); // when any textarea is modified, turn on warning

    // list of records that have id references, ie there is more than one photo of the same animal
    const multiples = [];

    // find records with the same id reference #
    for (let i = 0; i < sortedComments.length; i += 1) {
        const idRefUuids = [];
        const comment = sortedComments[i];
        const photos = [comment.image_url];
        const localizations = comment.all_localizations ? [comment.all_localizations] : [];
        const lat = comment.lat ? Number.parseFloat(comment.lat).toFixed(3) : null;
        const long = comment.long ? Number.parseFloat(comment.long).toFixed(3) : null;
        let videoLink = comment.video_url;
        let rovCruiseDive = '';
        let sampleReference = comment.sample_reference;

        if (comment.sequence?.includes('Hercules')) {
            const cruiseDive = comment.sequence.split('Hercules ')[1];
            rovCruiseDive = `Hercules-${cruiseDive.substring(0, 3)}-${cruiseDive.substring(3)}`;
        } else if (comment.sequence?.includes('Deep Discoverer')) {
            const cruiseDive = comment.sequence.split('Deep Discoverer ')[1];
            rovCruiseDive = `Deep Discoverer-${cruiseDive.substring(0, 4)}-${cruiseDive.substring(4)}`;
        } else {
            rovCruiseDive = comment.sequence;
        }

        if (videoLink?.includes('.mov')) {
            videoLink = `/video?link=${videoLink.split('#t=')[0]}&time=${videoLink.split('#t=')[1]}`;
        }

        if (comment.id_reference) {
            if (multiples.includes(comment.id_reference)) {
                // we already added this one to the list
                continue;
            }
            multiples.push(comment.id_reference); // add id ref to list
            slideshowIndices.push([1, 1, comment.id_reference]); // add the slideshow index for this record to the array
            idRefUuids.push(comment.uuid);
            numSlideshows += 1;
            // find other records with same id ref
            for (let j = i + 1; j < sortedComments.length; j += 1) {
                if (sortedComments[j].id_reference && sortedComments[j].id_reference === sortedComments[i].id_reference) {
                    photos.push(sortedComments[j].image_url); // add those photos to this comment
                    if (sortedComments[j].all_localizations) {
                        localizations.push(sortedComments[j].all_localizations);
                    }
                    slideshowIndices[numSlideshows - 1][1] += 1;
                    idRefUuids.push(sortedComments[j].uuid);
                    sampleReference = sortedComments[j].sample_reference || sampleReference;
                }
            }
        }

        let photoSlideshow = '';
        for (let j = 0; j < photos.length; j += 1) {
            photoSlideshow += `
                <div id="${comment.uuid}-${j}" class="${j > 0 ? 'slide' : ''}" style="position-relative">
                    ${photos.length > 1 ? `<div class="numbertext">${j + 1} / ${photos.length}</div>` : ''}
                    <a href="${photos[j].split('?')[0]}" target="_blank">
                        <img src="${photos[j]}" style="width:100%; border-radius: 10px;">
                    </a>
                    <div id="${comment.uuid}-${j}_overlay">
                        ${localizations[j] ? JSON.parse(localizations[j]).map((loco) => {
                            if (loco.type === 48) { // 48 is a box
                                return `<span
                                            class="position-absolute tator-box pe-none"
                                            style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%; width: ${loco.dimensions[0] * 100}%; height: ${loco.dimensions[1] * 100}%;"
                                        ></span>`;
                            }
                            return `<span class="position-absolute tator-dot" style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%;"></span>`;
                        }).join('')
                        : ''}
                    </div>
                </div>
            `;
        }

        $('#comments').append(`
            <div class="row flex-column-reverse flex-md-row my-3 small-md" style="background-color: #1d222a; border-radius: 20px;">
                <div class="col-md ps-3 ps-md-5 text-start d-flex align-items-center py-3">
                    <div class="w-100">
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Tentative ID:
                            </div>
                            <div class="col values">${comment.concept}${comment.id_certainty?.includes('maybe') ? '?' : ''}</div>
                        </div>
                        ${comment.id_certainty && comment.id_certainty !== 'maybe'
                            ? `<div class="row">
                                <div class="col-5 col-sm-4">
                                    ID Remarks:
                                </div>
                                <div class="col values">${comment.id_certainty.replaceAll('maybe', '').replace( /^; /i, '')}</div>
                            </div>`
                            : ''
                        }
                        ${comment.expedition_name
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Expedition:
                                    </div>
                                    <div class="col values">
                                        ${comment.expedition_name}
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Deployment:
                                    </div>
                                    <div class="col values">
                                        ${comment.sequence}
                                    </div>
                                </div>
                            ` : `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        ROV-Cruise-Dive:
                                    </div>
                                    <div class="col values">${rovCruiseDive}</div>
                                </div>
                            `
                        }
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Annotator:
                            </div>
                            <div class="col values">${comment.annotator}</div>
                        </div>
                        ${comment.timestamp
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Timestamp:
                                    </div>
                                    <div class="col values">${comment.timestamp}</div>
                                </div>
                            ` : ''
                        }
                        ${comment.lat
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Location:
                                    </div>
                                    <div class="col values"><a href="http://www.google.com/maps/place/${lat},${long}/@${lat},${long},5z/data=!3m1!1e3" target="_blank" class="mediaButton">${lat}, ${long}</a></div>
                                </div>
                            ` : ''
                        }
                        ${comment.depth
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Depth:
                                    </div>
                                    <div class="col values">${Math.round(comment.depth)} m</div>
                                </div>
                            ` : ''
                        }
                        ${comment.temperature
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Temperature:
                                    </div>
                                    <div class="col values">${comment.temperature.toFixed(2)} °C</div>
                                </div>
                            ` : ''
                        }
                        ${comment.oxygen_ml_l
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Oxygen:
                                    </div>
                                    <div class="col values">${comment.oxygen_ml_l.toFixed(2)} mL/L</div>
                                </div>
                            ` : ''
                        }
                        ${comment.bait_type
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Bait Type:
                                    </div>
                                    <div class="col values">${comment.bait_type[0].toUpperCase()}${comment.bait_type.slice(1)}</div>
                                </div>
                            ` : ''
                        }
                        <div class="mt-3">
                            Comments:
                        </div>
                        <textarea class="reviewer mt-2" name="comment_${i}" rows="3" placeholder="Enter comments">${
                            comment.reviewer_comments.find((comment) => comment.reviewer === reviewer)
                            ? comment.reviewer_comments.find((comment) => comment.reviewer === reviewer).comment
                            : ''
                        }</textarea>
                        ${idRefUuids.length
                            ? idRefUuids.map((uuid) => `<input type="hidden" name="uuid_${i}" value="${uuid}">`).join('')
                            : `<input type="hidden" name="uuid_${i}" value="${comment.uuid}">`
                        }
                        ${sampleReference
                            ? `<div class="row ps-1">
                                <div class="col align-items-center d-flex">
                                    <div class="position-relative" title="A sample of this specimen was collected">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" class="bi bi-basket-fill" viewBox="0 0 16 16">
                                          <path d="M5.071 1.243a.5.5 0 0 1 .858.514L3.383 6h9.234L10.07 1.757a.5.5 0 1 1 .858-.514L13.783 6H15.5a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H15v5a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V9H.5a.5.5 0 0 1-.5-.5v-2A.5.5 0 0 1 .5 6h1.717zM3.5 10.5a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0z"/>
                                        </svg>
                                        <div class="position-absolute top-0 left-0" style="margin-top: 12px; margin-left: 12px;">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="lightgreen" class="bi bi-check-circle-fill" viewBox="0 0 16 16">
                                              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                                            </svg>
                                        </div>
                                    </div>
                                    <div class="ms-3 mt-2" title="Wet-lab sample ID">
                                        ${sampleReference}
                                    </div>
                                </div>
                            </div>`
                            : ''
                        }
                    </div>
                </div>
                <div class="col-md text-center py-3 d-flex">
                    <div class="my-auto">
                        <div class="slideshow-container w-100">
                            ${photoSlideshow}
                            <a id="prev" onclick="plusSlides(${numSlideshows} - 1, -1, '${comment.uuid}')" ${photos.length < 2 ? "hidden" : ""}>&#10094;</a>
                            <a id="next" onclick="plusSlides(${numSlideshows} - 1, 1, '${comment.uuid}')" ${photos.length < 2 ? "hidden" : ""}>&#10095;</a>
                        </div>
                        <div class="row mt-2">
                            <div class="col">
                                ${videoLink
                                    ? (
                                        `<a href="${videoLink}" target="_blank" class="mediaButton mt-2">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi" viewBox="0 0 18 18">
                                                <path d="M0 12V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2m6.79-6.907A.5.5 0 0 0 6 5.5v5a.5.5 0 0 0 .79.407l3.5-2.5a.5.5 0 0 0 0-.814z"/>
                                            </svg>
                                            Play Video
                                        </a>`
                                    ) : '<span style="opacity: 60%;">Video not available</span>'
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);

        if (Object.keys(comment).includes('all_localizations') && comment.all_localizations) { // this is a tator localization
            for (let j = 0; j < photos.length; j += 1) {
                $(`#${comment.uuid}-${j}_overlay`).css('opacity', '0.5');
                $(`#${comment.uuid}-${j}`).hover((e) => {
                    if (e.type === 'mouseenter') {
                        $(`#${comment.uuid}-${j}_overlay`).css('opacity', '0.8');
                    } else if (e.type === 'mouseleave') {
                        $(`#${comment.uuid}-${j}_overlay`).css('opacity', '0.5');
                    }
                });
            }
        }
    }
});

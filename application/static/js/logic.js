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

function plusSlides(slideshowIndex, slideMod, idRef) {
    let slideIndex = slideshowIndices[slideshowIndex][0] + slideMod;
    if (slideIndex > slideshowIndices[slideshowIndex][1]) {
        slideIndex = 1;
    } else if (slideIndex < 1) {
        slideIndex = slideshowIndices[slideshowIndex][1];
    }
    slideshowIndices[slideshowIndex][0] = slideIndex;
    // hide all slides
    for (let i = 1; i <= slideshowIndices[slideshowIndex][1]; i++) {
        document.getElementById(`${idRef}-${i - 1}`).style.display = "none";
    }
    // show one slide
    document.getElementById(`${idRef}-${slideIndex - 1}`).style.display = "block";

}

function addViewAllParam() {
    const url = new URL(window.location.href);
    url.searchParams.set('all', 'true');
    window.location.href = url.href;
}

async function saveComments() {
    event.preventDefault();
    const formData = new FormData($('#commentForm')[0]);
    for (const comment of formData.entries()) {
        if (comment[0].includes(';')) {
            const uuids = comment[0].split(';');
            formData.delete(comment[0]);
            for (let i = 0; i < uuids.length; i += 1) {
                formData.append(uuids[i], comment[1]);
            }
        }
    }
    try {
        const res = await fetch('/save-comments', {
            method: 'POST',
            body: formData,
        });
        if (res.ok && res.redirected) {
            window.location.href = res.url;
        } else {
            console.log('Error saving comments');
        }
    } catch (err) {
        console.log(err);
    }
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
        let videoLink = comment.video_url;

        if (videoLink.includes('.mov')) {
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
                    slideshowIndices[numSlideshows - 1][1] += 1;
                    idRefUuids.push(sortedComments[j].uuid);
                }
            }
        }
        let photoSlideshow = `<div id="${comment.id_reference}-0">
                ${photos.length > 1 ? `<div class="numbertext">1 / ${photos.length}</div>` : ''}
                <a href="${photos[0]}" target="_blank">
                    <img src="${photos[0]}" style="width:100%; border-radius: 10px;">
                </a>
              </div>`;

        for (let j = 1; j < photos.length; j += 1) {
            photoSlideshow += `<div id="${comment.id_reference}-${j}" class="slide">
                ${photos.length > 1 ? `<div class="numbertext">${j + 1} / ${photos.length}</div>` : ''}
                <a href="${photos[j]}" target="_blank">
                    <img src="${photos[j]}" style="width:100%; border-radius: 10px;">
                </a>
              </div>`;
        }

        $('#comments').append(`
            <div class="row flex-column-reverse flex-md-row my-3 small-md" style="background-color: #1d222a; border-radius: 20px;">
                <div class="col-md ps-3 ps-md-5 text-start d-flex align-items-center py-3">
                    <div class="w-100">
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Tentative ID:
                            </div>
                            <div class="col values">${comment.concept}</div>
                        </div>
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Annotator:
                            </div>
                            <div class="col values">${comment.annotator}</div>
                        </div>
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Location:
                            </div>
                            <div class="col values"><a href="http://www.google.com/maps/place/${comment.lat},${comment.long}/@${comment.lat},${comment.long},5z/data=!3m1!1e3" target="_blank" class="mediaButton">${comment.lat}, ${comment.long}</a></div>
                        </div>
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Depth:
                            </div>
                            <div class="col values">${comment.depth} m</div>
                        </div>
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Timestamp:
                            </div>
                            <div class="col values">${comment.timestamp}</div>
                        </div>
                        <div class="mt-3">
                            Comments:
                        </div>
                        <textarea class="reviewer mt-2" name="${idRefUuids.length ? idRefUuids.join(';') : comment.uuid}" rows="3" placeholder="Enter comments">${
                            comment.reviewer_comments.find((comment) => comment.reviewer === reviewer)
                            ? comment.reviewer_comments.find((comment) => comment.reviewer === reviewer).comment
                            : ''
                        }</textarea>
                        <div class="row mt-3">
                            <div class="col">
                                <a href="${videoLink}" target="_blank" class="mediaButton mt-2">See video</a>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md text-center py-3">
                    <div class="slideshow-container w-100">
                        ${photoSlideshow}
                        <a id="prev" onclick="plusSlides(${numSlideshows} - 1, -1, '${comment.id_reference}')" ${photos.length < 2 ? "hidden" : ""}>&#10094;</a>
                        <a id="next" onclick="plusSlides(${numSlideshows} - 1, 1, '${comment.id_reference}')" ${photos.length < 2 ? "hidden" : ""}>&#10095;</a>
                    </div>
                </div>
            </div>
        `);
    }
});

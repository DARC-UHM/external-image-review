import {imageCard, imageCardStatus} from './image-card.js';

// list of records that have id references, i.e. there is more than one photo of the same animal
const recordsWithIdReference = [];

// object to store slideshow indices for records that have multiple id references
const slideshowIndices = {};

// object to store the status of each card (reviewed, pending)
const cardStatuses = {};

const tempSortedComments = comments.sort((a, b) => Date.parse(a.timestamp) > Date.parse(b.timestamp)); // sort by timestamp
const sortedComments = tempSortedComments.sort((a, b) => (a.concept > b.concept) ? 1 : (b.concept > a.concept) ? -1 : 0); // sort by concept

function changeSlide(uuid, slideMod) {
    const tempIndex = slideshowIndices[uuid].currentSlideIndex + slideMod;
    const updatedSlideIndex = (tempIndex + slideshowIndices[uuid].totalSlides) % slideshowIndices[uuid].totalSlides;
    slideshowIndices[uuid].currentSlideIndex = updatedSlideIndex;
    // hide all slides
    for (let i = 1; i <= slideshowIndices[uuid].totalSlides; i++) {
        document.getElementById(`${uuid}-${i - 1}`).style.display = 'none';
    }
    // show one slide
    document.getElementById(`${uuid}-${updatedSlideIndex}`).style.display = 'block';
}

document.prevSlide = (uuid) => {
    changeSlide(uuid, -1);
}

document.nextSlide = (uuid) => {
    changeSlide(uuid, 1);
}

function updateCard(idConsensus, index) {
    const commentTextArea = $(`#comment_${index}`);
    if (idConsensus === 'disagree') {
        commentTextArea.attr('placeholder', 'Add comments');
    } else { // agree or uncertain
        commentTextArea.attr('placeholder', 'Add comments (optional)');
    }
}

document.updateCard = updateCard;

async function saveComments(uuids, index, tentativeId, annotator, sequence, skip) {
    const uuidArray = uuids.split(',');
    const cardUuid = uuidArray[0];
    const idConsensus = $(`input[name='idConsensus_${index}']:checked`).val();
    const comment = $(`#comment_${index}`).val();

    const res = await fetch(`/save-comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            uuids: uuidArray,
            reviewer,
            idConsensus: skip ? null : idConsensus,
            comment: skip ? "Skipped" : comment,
            tentativeId,
            annotator,
            sequence,
        }),
    });

    if (res.ok) {
        cardStatuses[cardUuid] = 'reviewed';

        const cardsReviewed = Object.values(cardStatuses).filter((status) => status !== 'pending').length;

        $(`#container-${cardUuid}`).collapse('toggle');
        $('#cardsReviewed').html(cardsReviewed);
        $('#progressBarProgress').css('width', `${(cardsReviewed / Object.keys(cardStatuses).length) * 100}%`);
        $(`#status-${cardUuid}`).html(imageCardStatus('reviewed'));
    } else {
        $('#failedCommentFlash')[0].style.display = 'block';
    }
}

document.saveComments = saveComments;

async function toggleFavorite(uuids, isFavorite) {
    console.log(isFavorite);
    const uuidArray = uuids.split(',');

    let success = true;

    for (const uuid of uuidArray) {
        const res = await fetch(`/comment/${uuid}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reviewer,
                favorite: !isFavorite,
            }),
        });
        if (!res.ok) {
            success = false;
            break;
        }
    }

    // todo flash success/failure
}

document.toggleFavorite = toggleFavorite;

$(document).ready(() => {
    $('body').tooltip({ selector: '[data-toggle=tooltip]', trigger : 'hover' });
    window.addEventListener('popstate', function () {
        $('[data-toggle="tooltip"]').tooltip('dispose');
    });

    // go through each record, adding image cards to page. groups images with the same id reference together
    for (let i = 0; i < sortedComments.length; i += 1) {
        const comment = sortedComments[i];
        const idRefUuids = new Set(); // all the uuids for records with the same id reference as this record
        const photos = [comment.image_url];
        const localizations = comment.all_localizations ? [comment.all_localizations] : [];
        let sampleReference = comment.sample_reference;

        idRefUuids.add(comment.uuid);

        // if this comment has an id reference, we need to add it to the list of recordsWithIdReference
        if (comment.id_reference) {
            if (recordsWithIdReference.includes(comment.id_reference)) {
                continue; // we already added this one to the list
            }
            recordsWithIdReference.push(comment.id_reference); // add id ref to list
            slideshowIndices[comment.uuid] = { currentSlideIndex: 0, totalSlides: 1 };
            idRefUuids.add(comment.uuid);

            // find other records with same id ref, add them to the photos array
            for (let j = i + 1; j < sortedComments.length; j += 1) {
                if (sortedComments[j].id_reference && sortedComments[j].id_reference === sortedComments[i].id_reference) {
                    photos.push(sortedComments[j].image_url); // add those photos to this comment
                    if (sortedComments[j].all_localizations) {
                        localizations.push(sortedComments[j].all_localizations);
                    }
                    slideshowIndices[comment.uuid].totalSlides++;
                    idRefUuids.add(sortedComments[j].uuid);
                    sampleReference = sortedComments[j].sample_reference || sampleReference;
                }
            }
        }

        $('#comments').append(imageCard({
            comment,
            photos,
            index: i,
            idRefUuids,
            localizations,
            sampleReference,
        }));

        cardStatuses[comment.uuid] = 'pending';

        const reviewerComments = comment.reviewer_comments.find((comment) => comment.reviewer === reviewer);
        const idConsensus = reviewerComments?.id_consensus;

        if (idConsensus) {
            if (idConsensus === 'agree') {
                $(`#yes_${i}`).prop('checked', true);
            } else if (idConsensus === 'disagree') {
                $(`#no_${i}`).prop('checked', true);
            } else if (idConsensus.includes('uncertain')) {
                $(`#uncertain_${i}`).prop('checked', true);
            }
        }

        updateCard(idConsensus, i);

        if (Object.keys(comment).includes('all_localizations') && comment.all_localizations) {
            // this is a tator localization
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

    $('#totalCards').html(Object.keys(cardStatuses).length);
});

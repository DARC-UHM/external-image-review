import { imageCard } from './image-card.js';

// list of records that have id references, i.e. there is more than one photo of the same animal
const recordsWithIdReference = [];

// object to store slideshow indices for records that have multiple id references
const slideshowIndices = {};

const tempSortedComments = comments.sort((a, b) => Date.parse(a.timestamp) > Date.parse(b.timestamp)); // sort by timestamp
const sortedComments = tempSortedComments.sort((a, b) => (a.concept > b.concept) ? 1 : (b.concept > a.concept) ? -1 : 0); // sort by concept

document.prevSlide = (uuid) => {
    changeSlide(uuid, -1);
}

document.nextSlide = (uuid) => {
    changeSlide(uuid, 1);
}

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

function updateCard(idConsensus, index) {
    const commentTextArea = $(`#comment_${index}`);
    if (idConsensus === 'disagree') {
        commentTextArea.attr('placeholder', 'Add comments');
    } else { // agree or uncertain
        commentTextArea.attr('placeholder', 'Add comments (optional)');
    }
}

document.updateCard = updateCard;

$(document).ready(() => {
    $('body').tooltip({ selector: '[data-toggle=tooltip]', trigger : 'hover' });
    window.addEventListener('popstate', function () {
        $('[data-toggle="tooltip"]').tooltip('dispose');
    });

    // go through each record, adding image cards to page. groups images with the same id reference together
    for (let i = 0; i < sortedComments.length; i += 1) {
        const comment = sortedComments[i];
        const idRefUuids = []; // all the uuids for records with the same id reference as this record
        const photos = [comment.image_url];
        const localizations = comment.all_localizations ? [comment.all_localizations] : [];
        let sampleReference = comment.sample_reference;

        // if this comment has an id reference, we need to add it to the list of recordsWithIdReference
        if (comment.id_reference) {
            if (recordsWithIdReference.includes(comment.id_reference)) {
                continue; // we already added this one to the list
            }
            recordsWithIdReference.push(comment.id_reference); // add id ref to list
            slideshowIndices[comment.uuid] = { currentSlideIndex: 0, totalSlides: 1 };
            idRefUuids.push(comment.uuid);

            // find other records with same id ref, add them to the photos array
            for (let j = i + 1; j < sortedComments.length; j += 1) {
                if (sortedComments[j].id_reference && sortedComments[j].id_reference === sortedComments[i].id_reference) {
                    photos.push(sortedComments[j].image_url); // add those photos to this comment
                    if (sortedComments[j].all_localizations) {
                        localizations.push(sortedComments[j].all_localizations);
                    }
                    slideshowIndices[comment.uuid].totalSlides++;
                    idRefUuids.push(sortedComments[j].uuid);
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
});

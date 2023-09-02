const multiples = []; // list of records that have id references, ie there is more than one photo of the same animal
let warningOn = false;

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
$('textarea').on('input', () => turnOnWarning());

sortedComments = comments.sort((a, b) => a.timestamp.localeCompare(b.timestamp)); // sort by timestamp
console.log(sortedComments)

for (let i = 0; i < sortedComments.length; i += 1) {
    const comment = sortedComments[i];
    const photos = [comment.image_url];
    if (comment.id_reference) {
        if (multiples.includes(comment.id_reference)) {
            // we already added this one to the list
            break;
        }
        multiples.push(comment.id_reference); // add id ref to list
        // find other records with same id ref
        for (let j = i + 1; j < sortedComments.length; j += 1) {
            if (sortedComments[j].id_reference && sortedComments[j].id_reference === sortedComments[i].id_reference) {
                // add those photos to this comment
                photos.push(sortedComments[j].image_url);
            }
        }
    }
    let photoSlideshow = '';

    for (let j = 0; j < photos.length; j += 1) {
        photoSlideshow += `<div class="mySlides">
        <div class="numbertext">${j + 1} / ${photos.length}</div>
        <a href="${photos[j]}" target="_blank">
            <img src="${photos[j]}" style="width:100%">
        </a>
      </div>`;
    }

    $('#commentTable').find('tbody').append(`
        <tr>
            <td class="ps-5">
                <div class="row">
                    <div class="col-4">
                        Tentative ID:
                    </div>
                    <div class="col values">${comment.concept}</div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Annotator:
                    </div>
                    <div class="col values">${comment.annotator}</div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Location:
                    </div>
                    <div class="col values"><a href="http://www.google.com/maps/place/${comment.lat},${comment.long}/@${comment.lat},${comment.long},5z/data=!3m1!1e3" target="_blank" class="mediaButton">${comment.lat}, ${comment.long}</a></div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Depth:
                    </div>
                    <div class="col values">${comment.depth} m</div>
                </div>
                <div class="row">
                    <div class="col-4">
                        Timestamp:
                    </div>
                    <div class="col values">${comment.timestamp}</div>
                </div>
                <div class="mt-3">
                    Comments:
                </div>
                <textarea class="reviewer mt-2" name="${comment.uuid}" rows="3" placeholder="Enter comments">${comment.comment ? comment.comment : ''}</textarea>
                <div class="row mt-3">
                    <div class="col">
                        <a href="${comment.video_url}" target="_blank" class="mediaButton mt-2">See video</a>
                    </div>
                </div>
            </td>
            <td class="text-center">
                <div class="slideshow-container">
                    ${photoSlideshow}
                  <a class="prev" onclick="plusSlides(-1)">&#10094;</a>
                  <a class="next" onclick="plusSlides(1)">&#10095;</a>
                </div>
                <br>
            </td>
        </tr>
    `)
}

let slideIndex = 1;
showSlides(slideIndex);

// Next/previous controls
function plusSlides(n) {
  showSlides(slideIndex += n);
}

// Thumbnail image controls
function currentSlide(n) {
  showSlides(slideIndex = n);
}

function showSlides(n) {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");
  if (n > slides.length) {slideIndex = 1}
  if (n < 1) {slideIndex = slides.length}
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";
  dots[slideIndex-1].className += " active";
}
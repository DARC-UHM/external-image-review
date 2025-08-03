export const imageCard = ({ comment, photos, index, idRefUuids, localizations, sampleReference  }) => {
    const reviewerComments = comment.reviewer_comments.find((comment) => comment.reviewer === reviewer);
    const tentativeId = `${comment.concept}${comment.id_certainty?.includes('maybe') ? '?' : ''}`;
    const lat = comment.lat ? Number.parseFloat(comment.lat).toFixed(3) : null;
    const long = comment.long ? Number.parseFloat(comment.long).toFixed(3) : null;
    let videoLink = comment.video_url;
    let rovCruiseDive;

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

    let photoSlideshow = '';

    for (let j = 0; j < photos.length; j += 1) {
        photoSlideshow += `
            <div id="${comment.uuid}-${j}" class="${j > 0 ? 'slide' : ''}" style="position-relative">
                ${photos.length > 1 ? `<div class="numbertext">${j + 1} / ${photos.length}</div>` : ''}
                <a href="${photos[j].split('?')[0]}" target="_blank">
                    <img src="${photos[j]}" alt="${tentativeId}" style="width:100%; border-radius: 10px;">
                </a>
                <div id="${comment.uuid}-${j}_overlay">
                    ${localizations[j] 
                        ? JSON.parse(localizations[j]).map((loco) => {
                            if (loco.type === 48) { // 48 is a box
                                return `<span
                                    class="position-absolute tator-box pe-none"
                                    style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%; width: ${loco.dimensions[0] * 100}%; height: ${loco.dimensions[1] * 100}%;"
                                ></span>`;
                            }
                            return `<span class="position-absolute tator-dot" style="top: ${loco.points[1] * 100}%; left: ${loco.points[0] * 100}%;"></span>`;
                        }).join('') : ''
                    }
                </div>
            </div>
        `;
    }

    return `
        <div id="${comment.uuid}" class="my-3">
            <div
                id="${comment.uuid}-expanded"
                class="row flex-column-reverse flex-md-row small-md position-relative"
                style="background-color: var(--darc-bg-dark); border-radius: 20px;"
            >
                <div class="col ps-3 ps-md-5 text-start py-3 small">
                    <div class="w-100 py-3">
                        <div class="row">
                            <div class="col-5 col-sm-4">
                                Tentative ID:
                            </div>
                            <div class="col values">${tentativeId}</div>
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
                                    <div class="col values">${comment.temperature.toFixed(2)}°C</div>
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
                        ${comment.salinity
                            ? `
                                <div class="row">
                                    <div class="col-5 col-sm-4">
                                        Salinty:
                                    </div>
                                    <div class="col values">${comment.salinity.toFixed(2)} PSU</div>
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
                        ${idRefUuids.length
                            ? idRefUuids.map((uuid) => `<input type="hidden" name="uuid_${index}" value="${uuid}">`).join('')
                            : `<input type="hidden" name="uuid_${index}" value="${comment.uuid}">`
                        }
                        ${sampleReference
                            ? `<div class="row ps-1 mt-2">
                                <div class="col align-items-center d-flex">
                                    <div class="position-relative" data-toggle="tooltip" data-bs-placement="top" title="A sample of this specimen was collected">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" class="bi bi-basket-fill" viewBox="0 0 16 16">
                                          <path d="M5.071 1.243a.5.5 0 0 1 .858.514L3.383 6h9.234L10.07 1.757a.5.5 0 1 1 .858-.514L13.783 6H15.5a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H15v5a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V9H.5a.5.5 0 0 1-.5-.5v-2A.5.5 0 0 1 .5 6h1.717zM3.5 10.5a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm2.5 0a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0z"/>
                                        </svg>
                                        <div class="position-absolute top-0 left-0" style="margin-top: 12px; margin-left: 12px;">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="lightgreen" class="bi bi-check-circle-fill" viewBox="0 0 16 16">
                                              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                                            </svg>
                                        </div>
                                    </div>
                                    <div class="ms-3 mt-2" data-toggle="tooltip" data-bs-placement="top" title="Wet-lab sample ID">
                                        ${sampleReference}
                                    </div>
                                </div>
                            </div>`
                            : ''
                        }
                        <hr style="background: #575f6b;">
                        <div class="mt-3">
                            Agree with tentative ID?
                        </div>
                        <div
                            role="group"
                            aria-label="Answer button group"
                            class="d-flex gap-3 pt-2 pb-3"
                        >
                            <div>
                                <input
                                    id="yes_${index}"
                                    name="idConsensus_${index}"
                                    value="agree"
                                    type="radio"
                                    autocomplete="off"
                                    onclick="updateCard('agree', ${index});"
                                >
                                <label for="yes_${index}">
                                    Yes
                                </label>
                            </div>
                            
                            <div>
                                <input
                                    id="no_${index}"
                                    name="idConsensus_${index}"
                                    value="disagree"
                                    type="radio"
                                    autocomplete="off"
                                    onclick="updateCard('disagree', ${index});"
                                >
                                <label for="no_${index}">
                                    No
                                </label>
                            </div>
                            <div>
                                <input
                                    id="uncertain_${index}"
                                    name="idConsensus_${index}"
                                    value="uncertain"
                                    type="radio"
                                    autocomplete="off"
                                    onclick="updateCard('uncertain', ${index});"
                                >
                                <label for="uncertain_${index}">
                                    Uncertain
                                </label>
                            </div>
                        </div>
                        <textarea 
                            class="reviewer-textarea"
                            id="comment_${index}"
                            name="comment_${index}"
                            rows="3"
                            placeholder="Add comments"
                        >${
                            reviewerComments ? reviewerComments.comment || '' : ''
                        }</textarea>
                        <input hidden name="tentativeId_${index}" value="${tentativeId}">
                        <div class="mt-3">
                            <button class="btn btn-sm btn-success px-3 me-1">Save</button>
                            <button class="btn btn-sm btn-outline-info">No Comment</button>
                        </div>
                    </div>
                </div>
                <div class="col text-center py-3 d-flex">
                    <div class="my-auto">
                        <div class="slideshow-container w-100 position-relative">
                            <div
                                class="position-absolute px-2 py-1 ${reviewerComments?.favorite ? 'btn-favorite-favorited' : 'btn-favorite'}"
                                style="right: 0; cursor: pointer;"
                                data-toggle="tooltip"
                                data-bs-placement="left"
                                title="${reviewerComments?.favorite ? 'Remove from favorites' : 'Save to favorites'}"
                                onclick=""
                            >
                                ${reviewerComments?.favorite
                                    ? `
                                       <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-heart-fill" viewBox="-2 -2 24 24">
                                          <path fill-rule="evenodd" d="M8 1.314C12.438-3.248 23.534 4.735 8 15-7.534 4.736 3.562-3.248 8 1.314"/>
                                       </svg>
                                    ` : `
                                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-heart" viewBox="-2 -2 24 24" stroke="currentColor" stroke-width="1">
                                            <path d="m8 2.748-.717-.737C5.6.281 2.514.878 1.4 3.053c-.523 1.023-.641 2.5.314 4.385.92 1.815 2.834 3.989 6.286 6.357 3.452-2.368 5.365-4.542 6.286-6.357.955-1.886.838-3.362.314-4.385C13.486.878 10.4.28 8.717 2.01zM8 15C-7.333 4.868 3.279-3.04 7.824 1.143q.09.083.176.171a3 3 0 0 1 .176-.17C12.72-3.042 23.333 4.867 8 15"/>
                                        </svg>
                                    `
                                }
                            </div>
                            ${photoSlideshow}
                            <a id="prev" onclick="prevSlide('${comment.uuid}')" ${photos.length < 2 ? "hidden" : ""}>&#10094;</a>
                            <a id="next" onclick="nextSlide('${comment.uuid}')" ${photos.length < 2 ? "hidden" : ""}>&#10095;</a>
                        </div>
                        <div class="row mt-2">
                            <div class="col">
                                ${videoLink
                                    ? `
                                        <a href="${videoLink}" target="_blank" class="mediaButton mt-2">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi" viewBox="0 0 18 18">
                                                <path d="M0 12V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2m6.79-6.907A.5.5 0 0 0 6 5.5v5a.5.5 0 0 0 .79.407l3.5-2.5a.5.5 0 0 0 0-.814z"/>
                                            </svg>
                                            Play Video
                                        </a>
                                    ` : '<span style="opacity: 60%;">Video not available</span>'
                                }
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    class="position-absolute"
                    style="top: 0; right: 0; padding: 10px; cursor: pointer; width: min-content"
                    onclick="collapseCard('${comment.uuid}')"
                >
                    -
                </div>
            </div>
            <div
                id="${comment.uuid}-collapsed"
                class="justify-content-between position-relative"
                style="background-color: var(--darc-bg-dark); border-radius: 20px; display: none;"
            >
                <div class="small ps-4">${tentativeId}</div>
                <div
                    onclick="expandCard('${comment.uuid}')"
                    class="position-absolute"
                    style="top: 0; right: 0; padding: 10px; cursor: pointer;"
                >
                    +
                </div>
            </div>
        </div>
    `;
};

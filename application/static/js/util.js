export const depthColor = (depthM) => {
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
};

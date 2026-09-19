export const depthColor = (depthM) => {
    if (!depthM) {
        return '#00000000';
    }
    if (depthM >= 2400) {
        return DEPTH_COLOR['2400+'];
    } else if (depthM >= 1500) {
        return DEPTH_COLOR['1500–2399'];
    } else if (depthM >= 700) {
        return DEPTH_COLOR['700–1499'];
    } else if (depthM >= 300) {
        return DEPTH_COLOR['300–699'];
    }
    return DEPTH_COLOR['0–299'];
};

export const DEPTH_COLOR = {
    '0–299': '#fc0d1b',
    '300–699': '#fffd38',
    '700–1499': '#19af54',
    '1500–2399': '#0b24fb',
    '2400+': '#ca1ec9',
}

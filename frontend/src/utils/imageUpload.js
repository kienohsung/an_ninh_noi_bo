// File: frontend/src/utils/imageUpload.js
/**
 * Image upload utilities for guest registration
 * Handles EXIF orientation, resizing, and API upload
 */

import api from '../api'

/**
 * Get EXIF orientation from image file
 * @param {File} file - Image file
 * @returns {Promise<number>} Orientation value (-1 if not found)
 */
export async function getOrientation(file) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const view = new DataView(e.target.result);
                if (view.getUint16(0, false) !== 0xFFD8) return resolve(-1);
                const length = view.byteLength;
                let offset = 2;
                while (offset < length) {
                    if (view.getUint16(offset + 2, false) <= 8) return resolve(-1);
                    const marker = view.getUint16(offset, false);
                    offset += 2;
                    if (marker === 0xFFE1) {
                        if (view.getUint32(offset + 2, false) !== 0x45786966) return resolve(-1);
                        const little = view.getUint16(offset += 6, false) === 0x4949;
                        offset += view.getUint32(offset + 4, little);
                        const tags = view.getUint16(offset, little);
                        offset += 2;
                        for (let i = 0; i < tags; i++) {
                            if (view.getUint16(offset + (i * 12), little) === 0x0112) {
                                return resolve(view.getUint16(offset + (i * 12) + 8, little));
                            }
                        }
                    } else if ((marker & 0xFF00) !== 0xFF00) break;
                    else offset += view.getUint16(offset, false);
                }
                return resolve(-1);
            } catch (e) {
                console.error("Error reading EXIF data", e);
                return resolve(-1);
            }
        };
        reader.onerror = () => resolve(-1);
        reader.readAsArrayBuffer(file.slice(0, 64 * 1024));
    });
}

/**
 * Resize image with EXIF orientation correction
 * @param {File} file - Image file to resize
 * @param {number} maxSize - Maximum dimension (default: 1280)
 * @returns {Promise<Blob>} Resized image blob
 */
export async function resizeImage(file, maxSize = 1280) {
    const orientation = await getOrientation(file);
    const url = URL.createObjectURL(file);

    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            URL.revokeObjectURL(url);
            let width = img.width;
            let height = img.height;

            if (width > height) {
                if (width > maxSize) {
                    height *= maxSize / width;
                    width = maxSize;
                }
            } else {
                if (height > maxSize) {
                    width *= maxSize / height;
                    height = maxSize;
                }
            }

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            if (orientation > 4 && orientation < 9) {
                canvas.width = height;
                canvas.height = width;
            } else {
                canvas.width = width;
                canvas.height = height;
            }

            switch (orientation) {
                case 2: ctx.transform(-1, 0, 0, 1, width, 0); break;
                case 3: ctx.transform(-1, 0, 0, -1, width, height); break;
                case 4: ctx.transform(1, 0, 0, -1, 0, height); break;
                case 5: ctx.transform(0, 1, 1, 0, 0, 0); break;
                case 6: ctx.transform(0, 1, -1, 0, height, 0); break;
                case 7: ctx.transform(0, -1, -1, 0, height, width); break;
                case 8: ctx.transform(0, -1, 1, 0, 0, width); break;
                default: break;
            }

            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob((blob) => {
                if (blob) resolve(blob);
                else reject(new Error('Canvas to Blob conversion failed'));
            }, file.type || 'image/jpeg', 0.85);
        };
        img.onerror = (err) => {
            URL.revokeObjectURL(url);
            reject(err);
        };
        img.src = url;
    });
}

/**
 * Upload a single image for a guest
 * @param {number} guestId - Guest ID
 * @param {File} file - Image file
 * @returns {Promise} Upload response
 */
export async function uploadGuestImage(guestId, file) {
    const resizedBlob = await resizeImage(file);
    const formData = new FormData();
    formData.append('file', resizedBlob, file.name);

    return api.post(`/guests/${guestId}/upload-image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
}

/**
 * Upload multiple images for a guest with error handling
 * @param {number} guestId - Guest ID
 * @param {File[]} files - Array of image files
 * @param {Function} onError - Error callback (file, error) => void
 * @returns {Promise<Object[]>} Array of upload results
 */
export async function uploadMultipleImages(guestId, files, onError) {
    const results = [];

    for (const file of files) {
        try {
            const result = await uploadGuestImage(guestId, file);
            results.push({ success: true, file, result });
        } catch (error) {
            console.error(`Failed to upload ${file.name}`, error);
            if (onError) onError(file, error);
            results.push({ success: false, file, error });
        }
    }

    return results;
}

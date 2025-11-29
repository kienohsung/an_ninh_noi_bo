// File: frontend/src/utils/validators.js
/**
 * Validation utilities for form inputs
 */

import { date as quasarDate } from 'quasar'

/**
 * Validate estimated datetime string
 * @param {string} estimatedDt - Datetime string to validate
 * @returns {boolean} True if valid
 */
export function validateEstimatedDateTime(estimatedDt) {
    return estimatedDt
        && typeof estimatedDt === 'string'
        && estimatedDt.trim().length > 0
        && quasarDate.isValid(estimatedDt)
}

/**
 * Validate guest name
 * @param {string} name - Name to validate
 * @returns {boolean} True if valid
 */
export function validateGuestName(name) {
    return name && typeof name === 'string' && name.trim().length > 0
}

/**
 * Validate date range
 * @param {string} from - Start date
 * @param {string} to - End date
 * @returns {boolean} True if valid range
 */
export function validateDateRange(from, to) {
    if (!from || !to) return false

    try {
        const fromDate = new Date(from)
        const toDate = new Date(to)
        return fromDate <= toDate
    } catch {
        return false
    }
}

/**
 * Validate array of guests (for bulk registration)
 * @param {Array} guests - Array of guest objects
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateGuestArray(guests) {
    if (!Array.isArray(guests) || guests.length === 0) {
        return { valid: false, message: 'Danh sách khách không hợp lệ.' }
    }

    const invalidGuests = guests.filter(g => !validateGuestName(g.full_name))

    if (invalidGuests.length > 0) {
        return {
            valid: false,
            message: 'Vui lòng nhập đầy đủ họ tên cho tất cả khách.'
        }
    }

    return { valid: true, message: '' }
}

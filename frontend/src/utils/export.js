// File: security_mgmt_dev/frontend/src/utils/export.js
import { exportFile as qExportFile } from 'quasar'
import * as XLSX from 'xlsx'

/**
 * Converts a string to an ArrayBuffer.
 * @param {string} s The string to convert.
 * @returns {ArrayBuffer} The ArrayBuffer.
 */
function s2ab(s) {
  const buf = new ArrayBuffer(s.length)
  const view = new Uint8Array(buf)
  for (let i = 0; i < s.length; i++) {
    view[i] = s.charCodeAt(i) & 0xFF
  }
  return buf
}

/**
 * Exports an array of objects to an XLSX file.
 * @param {string} fileName The name of the file to export (e.g., 'users.xlsx').
 * @param {Array<Object>} data The array of data objects.
 * @param {Array<string>} columns An array of strings representing the columns to include.
 */
export function exportFile(fileName, data, columns) {
  try {
    // Create worksheet from JSON data, specifying the header order
    const ws = XLSX.utils.json_to_sheet(data, { header: columns })
    
    // Create a new workbook
    const wb = XLSX.utils.book_new()
    
    // Append the worksheet to the workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Data')
    
    // Write the workbook to a binary string
    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'binary' })
    
    // Use Quasar's exportFile utility to trigger the download
    qExportFile(
      fileName,
      new Blob([s2ab(wbout)], { type: 'application/octet-stream' }),
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    return true
  } catch (error) {
    console.error('Export failed:', error)
    return false
  }
}

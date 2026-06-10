/** base64 字符串转 Blob */
export function base64ToBlob(b64: string, type: string): Blob {
  const byteCharacters = atob(b64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  return new Blob([new Uint8Array(byteNumbers)], { type })
}

/** 触发浏览器下载 */
export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export const WORD_MIME =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

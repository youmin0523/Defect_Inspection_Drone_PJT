/**
 * api/reportApi.js
 * 역할: LLM 하자 점검 보고서 생성 API 래퍼
 *       - generateReportStream: 스트리밍 방식 (fetch + ReadableStream)
 *       - generateReportPreview: 비스트리밍 방식 (Axios)
 *
 * 스트리밍 방식:
 *   fetch API의 response.body.getReader()를 사용하여
 *   청크 단위로 텍스트를 수신 → onChunk 콜백으로 전달
 */

import axios from 'axios'

const BASE = '/api/v1/report'

/**
 * LLM 보고서 스트리밍 생성.
 * 청크를 받을 때마다 onChunk(text) 콜백 호출.
 * 완료 시 onDone() 콜백 호출.
 *
 * @param {Object} request - ReportRequest 스키마
 * @param {Function} onChunk - 청크 텍스트 수신 콜백
 * @param {Function} onDone - 완료 콜백
 * @param {Function} onError - 오류 콜백
 */
export async function generateReportStream(request, onChunk, onDone, onError) {
  try {
    const response = await fetch(`${BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`보고서 생성 실패: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      onChunk(chunk)
    }

    onDone?.()
  } catch (err) {
    onError?.(err)
  }
}

/**
 * LLM 보고서 비스트리밍 미리보기 (전체 내용 한 번에)
 * @param {Object} request - ReportRequest 스키마
 * @returns {Object} { content, metadata }
 */
export async function generateReportPreview(request) {
  const { data } = await axios.post(`${BASE}/preview`, request)
  return data
}

/**
 * 通用格式化函数 composable
 *
 * 纯函数工具集，无响应式状态。供 Dashboard / Budget / KeyIndicators 共享，
 * 消除三处 formatNum / formatPercent / formatDelta / formatHistoryDateOnly 重复。
 * formatHistoryTime / formatFileDate 已在 useGlobalData 提供，此处不重复定义。
 */

/**
 * 数值格式化
 * @param {number|null|undefined} v - 数值
 * @param {object} [opts]
 * @param {string} [opts.nullText='-'] - 空值占位符
 * @param {number} [opts.min=2] - 最小小数位
 * @param {number} [opts.max=2] - 最大小数位
 */
function formatNum(v, { nullText = '-', min = 2, max = 2 } = {}) {
  if (v === null || v === undefined || isNaN(v)) return nullText
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: min, maximumFractionDigits: max })
}

/** 比率转百分比字符串（0.123 → "12.3%"） */
function formatPercent(value) {
  return (value * 100).toFixed(1) + '%'
}

/** 增量格式化（正数带 +，pct 单位走 1 位小数，其余 2 位） */
function formatDelta(value, unit = '') {
  const numeric = Number(value || 0)
  const sign = numeric > 0 ? '+' : ''
  if (unit === 'pct') return `${sign}${numeric.toFixed(1)} pct`
  return `${sign}${numeric.toFixed(2)} ${unit}`.trim()
}

/** 日期仅日期部分（2024/01/02 → "2024-01-02"） */
function formatHistoryDateOnly(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

export function useFormatters() {
  return {
    // ── 格式化 ──
    formatNum,
    formatPercent,
    formatDelta,
    formatHistoryDateOnly,
  }
}

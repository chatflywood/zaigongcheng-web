/**
 * Archive.vue 核心交互单元测试
 *
 * 覆盖：
 *   - 初始状态（空数据、分类列表）
 *   - 上传弹窗（打开、年份选择、文件选择、拖拽）
 *   - 文件列表渲染
 *   - 预览面板（Excel/Word/不支持格式）
 *   - 删除确认
 *   - 工具函数（formatSize / formatDate / isExcel / isWord / extClass）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

// ── Mock API ──
vi.mock('../../api', () => ({
  listArchives: vi.fn(() => Promise.resolve([])),
  uploadArchive: vi.fn(() => Promise.resolve({})),
  deleteArchive: vi.fn(() => Promise.resolve({})),
  getArchiveFileUrl: vi.fn((id) => `http://localhost:8000/api/archive/file/${id}`),
}))

// ── Mock XLSX ──
vi.mock('xlsx', () => ({
  read: vi.fn(() => ({ SheetNames: ['Sheet1'], Sheets: { Sheet1: {} } })),
  utils: { sheet_to_html: vi.fn(() => '<table><tr><td>test</td></tr></table>') },
}))

// ── Mock mammoth ──
vi.mock('mammoth', () => ({
  default: { convertToHtml: vi.fn(() => Promise.resolve({ value: '<p>Hello</p>' })) },
}))

const api = await import('../../api')

let Archive
beforeEach(async () => {
  Archive = (await import('../Archive.vue')).default
  vi.clearAllMocks()
  api.listArchives.mockResolvedValue([])
})

// ── 辅助函数 ──

function makeRecord(overrides = {}) {
  return {
    id: 1,
    category: '年度建设情况',
    original_filename: '2025年建设情况.xlsx',
    ext: '.xlsx',
    year: '2025',
    file_size: 102400,
    uploaded_at: '2026-06-20T10:00:00',
    note: '',
    ...overrides,
  }
}

function mountArchive() {
  return mount(Archive)
}


// ──────────────────────────────────────────────────────────────
// 1. 初始状态
// ──────────────────────────────────────────────────────────────

describe('初始状态', () => {
  it('渲染页面标题', () => {
    const wrapper = mountArchive()
    expect(wrapper.text()).toContain('数据档案库')
  })

  it('渲染 3 个分类卡片', () => {
    const wrapper = mountArchive()
    const cards = wrapper.findAll('.archive-cat-card')
    expect(cards).toHaveLength(3)
  })

  it('每个分类有上传按钮', () => {
    const wrapper = mountArchive()
    const btns = wrapper.findAll('.cat-upload-btn')
    expect(btns).toHaveLength(3)
  })

  it('空数据显示占位文字', () => {
    const wrapper = mountArchive()
    expect(wrapper.text()).toContain('暂无档案')
  })

  it('allRecords 初始为空数组', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.allRecords).toEqual([])
  })

  it('showUpload 初始为 false', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.showUpload).toBe(false)
  })

  it('previewRecord 初始为 null', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.previewRecord).toBeNull()
  })

  it('deleteTarget 初始为 null', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.deleteTarget).toBeNull()
  })
})


// ──────────────────────────────────────────────────────────────
// 2. 文件列表渲染
// ──────────────────────────────────────────────────────────────

describe('文件列表渲染', () => {
  it('有数据时渲染文件行', async () => {
    api.listArchives.mockResolvedValue([makeRecord()])
    const wrapper = mountArchive()
    await nextTick()
    await nextTick()
    expect(wrapper.text()).toContain('2025年建设情况.xlsx')
  })

  it('文件行显示年份和大小', async () => {
    api.listArchives.mockResolvedValue([makeRecord()])
    const wrapper = mountArchive()
    await nextTick()
    await nextTick()
    expect(wrapper.text()).toContain('2025年')
    expect(wrapper.text()).toContain('100.0 KB')
  })

  it('filesByCategory 按分类分组', async () => {
    api.listArchives.mockResolvedValue([
      makeRecord({ id: 1, category: '年度建设情况' }),
      makeRecord({ id: 2, category: '多年趋势汇总', original_filename: '趋势.xlsx' }),
    ])
    const wrapper = mountArchive()
    await nextTick()
    await nextTick()
    const grouped = wrapper.vm.filesByCategory
    expect(grouped['年度建设情况']).toHaveLength(1)
    expect(grouped['多年趋势汇总']).toHaveLength(1)
    expect(grouped['投资预算报告']).toHaveLength(0)
  })

  it('文件行有下载和删除按钮', async () => {
    api.listArchives.mockResolvedValue([makeRecord()])
    const wrapper = mountArchive()
    await nextTick()
    await nextTick()
    const actions = wrapper.findAll('.file-btn')
    expect(actions.length).toBeGreaterThanOrEqual(2)
  })
})


// ──────────────────────────────────────────────────────────────
// 3. 上传弹窗
// ──────────────────────────────────────────────────────────────

describe('上传弹窗', () => {
  it('点击上传按钮打开弹窗', async () => {
    const wrapper = mountArchive()
    const btn = wrapper.findAll('.cat-upload-btn')[0]
    await btn.trigger('click')
    expect(wrapper.vm.showUpload).toBe(true)
    expect(wrapper.vm.uploadCategory).toBe('年度建设情况')
  })

  it('弹窗显示分类名称', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    expect(wrapper.text()).toContain('年度建设情况')
  })

  it('年份选择器有 6 个选项', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    const options = wrapper.findAll('.field-select option')
    expect(options).toHaveLength(6)
  })

  it('uploadYear 默认为当前年', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    const curYear = String(new Date().getFullYear())
    expect(wrapper.vm.uploadYear).toBe(curYear)
  })

  it('点击关闭按钮关闭弹窗', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    expect(wrapper.vm.showUpload).toBe(true)
    await wrapper.find('.arc-modal-close').trigger('click')
    expect(wrapper.vm.showUpload).toBe(false)
  })

  it('确认上传按钮初始禁用（无文件）', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    const btn = wrapper.find('.upload-confirm-btn')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('选择文件后确认按钮启用', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    wrapper.vm.uploadFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    await nextTick()
    const btn = wrapper.find('.upload-confirm-btn')
    expect(btn.attributes('disabled')).toBeUndefined()
  })

  it('拖拽状态 class 切换', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    const dz = wrapper.find('.upload-dropzone')
    await dz.trigger('dragover')
    expect(wrapper.vm.isDragging).toBe(true)
    await dz.trigger('dragleave')
    expect(wrapper.vm.isDragging).toBe(false)
  })

  it('onFilePick 设置 uploadFile', async () => {
    const wrapper = mountArchive()
    await wrapper.findAll('.cat-upload-btn')[0].trigger('click')
    const file = new File(['data'], 'test.xlsx')
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')
    expect(wrapper.vm.uploadFile).toBe(file)
  })
})


// ──────────────────────────────────────────────────────────────
// 4. 预览面板
// ──────────────────────────────────────────────────────────────

describe('预览面板', () => {
  it('点击文件行打开预览', async () => {
    api.listArchives.mockResolvedValue([makeRecord()])
    // Mock fetch for preview
    global.fetch = vi.fn(() => Promise.resolve({
      ok: true,
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
    }))
    const wrapper = mountArchive()
    await nextTick()
    await nextTick()
    const row = wrapper.find('.file-row')
    await row.trigger('click')
    expect(wrapper.vm.previewRecord).not.toBeNull()
    global.fetch = undefined
  })

  it('closePreview 清空 previewRecord', async () => {
    const wrapper = mountArchive()
    wrapper.vm.previewRecord = makeRecord()
    await nextTick()
    wrapper.vm.closePreview()
    await nextTick()
    expect(wrapper.vm.previewRecord).toBeNull()
  })

  it('isExcel 识别 .xlsx 和 .xls', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.isExcel('.xlsx')).toBe(true)
    expect(wrapper.vm.isExcel('.xls')).toBe(true)
    expect(wrapper.vm.isExcel('.docx')).toBe(false)
  })

  it('isWord 识别 .docx', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.isWord('.docx')).toBe(true)
    expect(wrapper.vm.isWord('.xlsx')).toBe(false)
  })

  it('extClass 返回正确的类名', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.extClass('.xlsx')).toBe('ext-xlsx')
    expect(wrapper.vm.extClass('.docx')).toBe('ext-docx')
    expect(wrapper.vm.extClass('.pdf')).toBe('ext-other')
  })

  it('不支持的格式显示提示', async () => {
    const rec = makeRecord({ ext: '.pdf', original_filename: 'report.pdf' })
    api.listArchives.mockResolvedValue([rec])
    global.fetch = vi.fn(() => Promise.resolve({
      ok: true,
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
    }))
    const wrapper = mountArchive()
    await nextTick()
    await nextTick()
    await wrapper.find('.file-row').trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('该格式暂不支持在线预览')
    global.fetch = undefined
  })
})


// ──────────────────────────────────────────────────────────────
// 5. 删除确认
// ──────────────────────────────────────────────────────────────

describe('删除确认', () => {
  it('confirmDelete 设置 deleteTarget', async () => {
    const wrapper = mountArchive()
    const rec = makeRecord()
    wrapper.vm.confirmDelete(rec)
    await nextTick()
    expect(wrapper.vm.deleteTarget).toStrictEqual(rec)
  })

  it('删除弹窗显示文件名', async () => {
    const wrapper = mountArchive()
    wrapper.vm.confirmDelete(makeRecord())
    await nextTick()
    expect(wrapper.text()).toContain('2025年建设情况.xlsx')
    expect(wrapper.text()).toContain('此操作不可恢复')
  })

  it('点击取消关闭弹窗', async () => {
    const wrapper = mountArchive()
    wrapper.vm.confirmDelete(makeRecord())
    await nextTick()
    await wrapper.find('.cancel-btn').trigger('click')
    expect(wrapper.vm.deleteTarget).toBeNull()
  })

  it('点击删除调用 deleteArchive', async () => {
    const wrapper = mountArchive()
    wrapper.vm.confirmDelete(makeRecord())
    await nextTick()
    await wrapper.find('.danger-btn').trigger('click')
    expect(api.deleteArchive).toHaveBeenCalledWith(1)
  })

  it('删除后关闭弹窗并刷新列表', async () => {
    api.listArchives.mockResolvedValueOnce([makeRecord()])
    api.listArchives.mockResolvedValueOnce([])
    const wrapper = mountArchive()
    wrapper.vm.confirmDelete(makeRecord())
    await nextTick()
    await wrapper.find('.danger-btn').trigger('click')
    await nextTick()
    expect(wrapper.vm.deleteTarget).toBeNull()
    expect(api.listArchives).toHaveBeenCalledTimes(2) // onMounted + after delete
  })
})


// ──────────────────────────────────────────────────────────────
// 6. 工具函数
// ──────────────────────────────────────────────────────────────

describe('工具函数', () => {
  it('formatSize 格式化字节', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.formatSize(500)).toBe('500 B')
    expect(wrapper.vm.formatSize(1024)).toBe('1.0 KB')
    expect(wrapper.vm.formatSize(1048576)).toBe('1.00 MB')
    expect(wrapper.vm.formatSize(0)).toBe('-')
    expect(wrapper.vm.formatSize(null)).toBe('-')
  })

  it('formatDate 格式化 ISO 日期', () => {
    const wrapper = mountArchive()
    expect(wrapper.vm.formatDate('2026-06-20T10:00:00')).toBe('2026-06-20')
    expect(wrapper.vm.formatDate(null)).toBe('')
  })

  it('yearOptions 返回 6 个年份', () => {
    const wrapper = mountArchive()
    const years = wrapper.vm.yearOptions
    expect(years).toHaveLength(6)
    const curYear = new Date().getFullYear()
    expect(years[0]).toBe(String(curYear + 3)) // 最大年份在前（reverse）
  })

  it('currentSheetHtml 从 sheetHtmlMap 获取', async () => {
    const wrapper = mountArchive()
    wrapper.vm.sheetHtmlMap = { Sheet1: '<table>data</table>' }
    wrapper.vm.activeSheet = 'Sheet1'
    await nextTick()
    expect(wrapper.vm.currentSheetHtml).toBe('<table>data</table>')
  })

  it('currentSheetHtml activeSheet 不存在时返回空', () => {
    const wrapper = mountArchive()
    wrapper.vm.sheetHtmlMap = {}
    wrapper.vm.activeSheet = 'NotExist'
    expect(wrapper.vm.currentSheetHtml).toBe('')
  })
})

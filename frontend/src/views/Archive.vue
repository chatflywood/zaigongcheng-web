<template>
  <div class="archive-page">
    <div class="archive-header">
      <div class="archive-title-row">
        <span class="archive-icon">🗄</span>
        <div>
          <h2 class="archive-title">数据档案库</h2>
          <p class="archive-sub">仙桃分公司工程建设历年数据存储 · 支持 .xlsx / .docx 格式</p>
        </div>
      </div>
    </div>

    <div class="archive-body">
      <!-- 三个分类卡片 -->
      <div
        v-for="cat in CATEGORIES"
        :key="cat.key"
        class="archive-cat-card"
      >
        <div class="cat-head">
          <div class="cat-icon">{{ cat.icon }}</div>
          <div>
            <div class="cat-name">{{ cat.label }}</div>
            <div class="cat-desc">{{ cat.desc }}</div>
          </div>
          <button class="cat-upload-btn" @click="openUpload(cat.key)">+ 上传</button>
        </div>

        <!-- 文件列表 -->
        <div class="cat-files" v-if="filesByCategory[cat.key]?.length">
          <div
            v-for="rec in filesByCategory[cat.key]"
            :key="rec.id"
            class="file-row"
            :class="{ active: previewRecord?.id === rec.id }"
            @click="openPreview(rec)"
          >
            <span class="file-ext-badge" :class="extClass(rec.ext)">{{ rec.ext.replace('.','').toUpperCase() }}</span>
            <div class="file-info">
              <span class="file-name">{{ rec.original_filename }}</span>
              <span class="file-meta">{{ rec.year }}年 · {{ formatSize(rec.file_size) }} · {{ formatDate(rec.uploaded_at) }}</span>
            </div>
            <div class="file-actions" @click.stop>
              <a :href="getArchiveFileUrl(rec.id)" :download="rec.original_filename" class="file-btn" title="下载">↓</a>
              <button class="file-btn danger" @click="confirmDelete(rec)" title="删除">×</button>
            </div>
          </div>
        </div>
        <div class="cat-empty" v-else>
          暂无档案，点击「+ 上传」添加
        </div>
      </div>
    </div>

    <!-- 上传弹窗 -->
    <div class="arc-modal-mask" v-if="showUpload" @click.self="showUpload = false">
      <div class="arc-modal">
        <div class="arc-modal-head">
          <span>上传档案 · {{ uploadCatLabel }}</span>
          <button class="arc-modal-close" @click="showUpload = false">×</button>
        </div>
        <div class="arc-modal-body">
          <div class="upload-field">
            <label class="field-label">年份</label>
            <select v-model="uploadYear" class="field-select">
              <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>
          <div class="upload-field">
            <label class="field-label">备注（可选）</label>
            <input v-model="uploadNote" class="field-input" placeholder="如：第三季度更新版" />
          </div>
          <div
            class="upload-dropzone"
            :class="{ dragging: isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="onDrop"
            @click="fileInput?.click()"
          >
            <input ref="fileInput" type="file" accept=".xlsx,.xls,.docx,.pdf" style="display:none" @change="onFilePick" />
            <div v-if="!uploadFile">
              <div class="dz-icon">📂</div>
              <div class="dz-text">拖拽文件到此处，或点击选择</div>
              <div class="dz-hint">支持 .xlsx · .xls · .docx · .pdf</div>
            </div>
            <div v-else class="dz-selected">
              <span class="dz-file-icon">📄</span>
              <span class="dz-file-name">{{ uploadFile.name }}</span>
              <span class="dz-file-size">{{ formatSize(uploadFile.size) }}</span>
            </div>
          </div>
          <div v-if="uploadMsg" class="upload-msg" :class="uploadMsgType">{{ uploadMsg }}</div>
          <button class="upload-confirm-btn" :disabled="!uploadFile || uploading" @click="doUpload">
            {{ uploading ? '上传中…' : '确认上传' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 预览面板 -->
    <div class="preview-mask" v-if="previewRecord" @click.self="closePreview">
      <div class="preview-panel">
        <div class="preview-head">
          <div class="preview-title-group">
            <span class="preview-cat-tag">{{ previewRecord.category }}</span>
            <span class="preview-filename">{{ previewRecord.original_filename }}</span>
          </div>
          <div class="preview-head-actions">
            <a :href="getArchiveFileUrl(previewRecord.id)" :download="previewRecord.original_filename" class="preview-dl-btn">↓ 下载</a>
            <button class="preview-close" @click="closePreview">×</button>
          </div>
        </div>

        <!-- Excel 预览 -->
        <div v-if="isExcel(previewRecord.ext)" class="preview-body">
          <div v-if="previewLoading" class="preview-loading">加载中…</div>
          <div v-else-if="previewError" class="preview-error">{{ previewError }}</div>
          <div v-else class="excel-preview">
            <div class="sheet-tabs" v-if="sheets.length > 1">
              <button
                v-for="s in sheets"
                :key="s.name"
                class="sheet-tab"
                :class="{ active: activeSheet === s.name }"
                @click="activeSheet = s.name"
              >{{ s.name }}</button>
            </div>
            <div class="sheet-content" v-if="currentSheetHtml" v-html="currentSheetHtml"></div>
          </div>
        </div>

        <!-- Word 预览 -->
        <div v-else-if="isWord(previewRecord.ext)" class="preview-body">
          <div v-if="previewLoading" class="preview-loading">加载中…</div>
          <div v-else-if="previewError" class="preview-error">{{ previewError }}</div>
          <div v-else class="docx-preview" v-html="docxHtml"></div>
        </div>

        <!-- 不支持预览 -->
        <div v-else class="preview-body preview-unsupported">
          <div>该格式暂不支持在线预览</div>
          <a :href="getArchiveFileUrl(previewRecord.id)" :download="previewRecord.original_filename" class="preview-dl-btn large">↓ 下载文件</a>
        </div>
      </div>
    </div>

    <!-- 删除确认 -->
    <div class="arc-modal-mask" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="arc-modal small">
        <div class="arc-modal-head">
          <span>删除确认</span>
          <button class="arc-modal-close" @click="deleteTarget = null">×</button>
        </div>
        <div class="arc-modal-body">
          <p class="delete-warn">确定删除「{{ deleteTarget.original_filename }}」？此操作不可恢复。</p>
          <div class="delete-actions">
            <button class="cancel-btn" @click="deleteTarget = null">取消</button>
            <button class="danger-btn" @click="doDelete">删除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import mammoth from 'mammoth'
import { listArchives, uploadArchive, deleteArchive, getArchiveFileUrl } from '../api'

const CATEGORIES = [
  { key: '年度建设情况', label: '年度建设情况', icon: '📊', desc: '全年工程建设汇总、评分排名、专业指标' },
  { key: '多年趋势汇总', label: '多年趋势汇总', icon: '📈', desc: '多年投资趋势、专业结构、省内排名对比' },
  { key: '投资预算报告', label: '投资预算报告', icon: '📋', desc: '立项执行、招标结果、资本支出分析报告' },
]

const yearOptions = computed(() => {
  const cur = new Date().getFullYear()
  return Array.from({ length: 6 }, (_, i) => String(cur - 2 + i)).reverse()
})

// ── 数据 ──────────────────────────────────────────────────────
const allRecords = ref([])
const filesByCategory = computed(() => {
  const map = {}
  for (const cat of CATEGORIES) map[cat.key] = []
  for (const r of allRecords.value) {
    if (map[r.category]) map[r.category].push(r)
  }
  return map
})

async function loadList() {
  try {
    allRecords.value = await listArchives()
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadList)

// ── 上传 ─────────────────────────────────────────────────────
const showUpload = ref(false)
const uploadCategory = ref('')
const uploadYear = ref(String(new Date().getFullYear()))
const uploadNote = ref('')
const uploadFile = ref(null)
const uploading = ref(false)
const uploadMsg = ref('')
const uploadMsgType = ref('info')
const isDragging = ref(false)
const fileInput = ref(null)

const uploadCatLabel = computed(() => uploadCategory.value)

function openUpload(cat) {
  uploadCategory.value = cat
  uploadFile.value = null
  uploadMsg.value = ''
  uploading.value = false
  showUpload.value = true
}

function onFilePick(e) {
  const f = e.target.files[0]
  if (f) { uploadFile.value = f; uploadMsg.value = '' }
}

function onDrop(e) {
  isDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) { uploadFile.value = f; uploadMsg.value = '' }
}

async function doUpload() {
  if (!uploadFile.value) return
  uploading.value = true
  uploadMsg.value = ''
  try {
    await uploadArchive(uploadFile.value, uploadCategory.value, uploadYear.value, uploadNote.value)
    uploadMsg.value = '上传成功'
    uploadMsgType.value = 'success'
    await loadList()
    setTimeout(() => { showUpload.value = false }, 800)
  } catch (e) {
    uploadMsg.value = '上传失败：' + (e?.response?.data?.detail || e.message)
    uploadMsgType.value = 'error'
  } finally {
    uploading.value = false
  }
}

// ── 预览 ─────────────────────────────────────────────────────
const previewRecord = ref(null)
const previewLoading = ref(false)
const previewError = ref('')
const sheets = ref([])
const activeSheet = ref('')
const sheetHtmlMap = ref({})
const docxHtml = ref('')

const currentSheetHtml = computed(() => sheetHtmlMap.value[activeSheet.value] || '')

function isExcel(ext) { return ['.xlsx', '.xls'].includes(ext) }
function isWord(ext) { return ext === '.docx' }

function extClass(ext) {
  if (isExcel(ext)) return 'ext-xlsx'
  if (isWord(ext)) return 'ext-docx'
  return 'ext-other'
}

async function openPreview(rec) {
  previewRecord.value = rec
  previewLoading.value = true
  previewError.value = ''
  sheets.value = []
  sheetHtmlMap.value = {}
  docxHtml.value = ''

  try {
    const url = getArchiveFileUrl(rec.id)
    const res = await fetch(url)
    if (!res.ok) throw new Error('文件获取失败')
    const buf = await res.arrayBuffer()

    if (isExcel(rec.ext)) {
      const wb = XLSX.read(buf, { type: 'array' })
      const htmlMap = {}
      for (const name of wb.SheetNames) {
        htmlMap[name] = XLSX.utils.sheet_to_html(wb.Sheets[name], { editable: false })
      }
      sheetHtmlMap.value = htmlMap
      sheets.value = wb.SheetNames.map(n => ({ name: n }))
      activeSheet.value = wb.SheetNames[0]
    } else if (isWord(rec.ext)) {
      const result = await mammoth.convertToHtml({ arrayBuffer: buf })
      docxHtml.value = result.value
    }
  } catch (e) {
    previewError.value = '预览失败：' + e.message
  } finally {
    previewLoading.value = false
  }
}

function closePreview() {
  previewRecord.value = null
}

// ── 删除 ─────────────────────────────────────────────────────
const deleteTarget = ref(null)

function confirmDelete(rec) { deleteTarget.value = rec }

async function doDelete() {
  if (!deleteTarget.value) return
  try {
    await deleteArchive(deleteTarget.value.id)
    if (previewRecord.value?.id === deleteTarget.value.id) closePreview()
    deleteTarget.value = null
    await loadList()
  } catch (e) {
    console.error(e)
  }
}

// ── 工具 ─────────────────────────────────────────────────────
function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
</script>

<style scoped>
.archive-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 24px 64px;
  font-family: var(--font, 'PingFang SC', sans-serif);
}

.archive-header { margin-bottom: 32px; }
.archive-title-row { display: flex; align-items: center; gap: 16px; }
.archive-icon { font-size: 32px; line-height: 1; }
.archive-title { margin: 0; font-size: 22px; font-weight: 700; color: var(--ink, #1a1a2e); }
.archive-sub { margin: 4px 0 0; font-size: 13px; color: var(--muted, #888); }

/* Category cards */
.archive-body { display: flex; flex-direction: column; gap: 20px; }

.archive-cat-card {
  background: var(--paper, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 12px;
  overflow: hidden;
}

.cat-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border, #e5e7eb);
  background: var(--surface, #fafafa);
}
.cat-icon { font-size: 24px; flex-shrink: 0; }
.cat-name { font-size: 15px; font-weight: 600; color: var(--ink, #1a1a2e); }
.cat-desc { font-size: 12px; color: var(--muted, #888); margin-top: 2px; }
.cat-upload-btn {
  margin-left: auto;
  padding: 6px 16px;
  background: var(--accent, #2563eb);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  flex-shrink: 0;
}
.cat-upload-btn:hover { opacity: 0.88; }

.cat-files { padding: 8px 0; }
.cat-empty { padding: 24px 20px; color: var(--muted, #aaa); font-size: 13px; text-align: center; }

.file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.15s;
}
.file-row:hover { background: var(--hover, #f5f7ff); }
.file-row.active { background: #eff6ff; }

.file-ext-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  flex-shrink: 0;
}
.ext-xlsx { background: #d1fae5; color: #065f46; }
.ext-docx { background: #dbeafe; color: #1e40af; }
.ext-other { background: #f3f4f6; color: #6b7280; }

.file-info { flex: 1; min-width: 0; }
.file-name { display: block; font-size: 14px; color: var(--ink, #1a1a2e); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-meta { font-size: 12px; color: var(--muted, #888); margin-top: 2px; display: block; }

.file-actions { display: flex; gap: 6px; flex-shrink: 0; }
.file-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px;
  border: 1px solid var(--border, #e5e7eb);
  background: var(--paper, #fff);
  color: var(--ink, #555);
  font-size: 15px;
  cursor: pointer;
  text-decoration: none;
  line-height: 1;
}
.file-btn:hover { background: var(--surface, #f5f5f5); }
.file-btn.danger:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

/* Upload modal */
.arc-modal-mask {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
}
.arc-modal {
  background: var(--paper, #fff);
  border-radius: 14px;
  width: 480px;
  max-width: 95vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.arc-modal.small { width: 360px; }
.arc-modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 20px;
  font-size: 15px; font-weight: 600;
  border-bottom: 1px solid var(--border, #e5e7eb);
}
.arc-modal-close {
  background: none; border: none; font-size: 20px;
  color: var(--muted, #aaa); cursor: pointer; line-height: 1;
}
.arc-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }

.upload-field { display: flex; flex-direction: column; gap: 5px; }
.field-label { font-size: 13px; color: var(--muted, #888); }
.field-select, .field-input {
  padding: 8px 12px;
  border: 1px solid var(--border, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  background: var(--paper, #fff);
  color: var(--ink, #1a1a2e);
  outline: none;
}
.field-select:focus, .field-input:focus { border-color: var(--accent, #2563eb); }

.upload-dropzone {
  border: 2px dashed var(--border, #d1d5db);
  border-radius: 10px;
  padding: 28px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.upload-dropzone:hover, .upload-dropzone.dragging {
  border-color: var(--accent, #2563eb);
  background: #eff6ff;
}
.dz-icon { font-size: 28px; margin-bottom: 8px; }
.dz-text { font-size: 14px; color: var(--ink, #555); }
.dz-hint { font-size: 12px; color: var(--muted, #aaa); margin-top: 4px; }
.dz-selected { display: flex; align-items: center; gap: 10px; justify-content: center; flex-wrap: wrap; }
.dz-file-icon { font-size: 22px; }
.dz-file-name { font-size: 14px; color: var(--ink, #1a1a2e); word-break: break-all; }
.dz-file-size { font-size: 12px; color: var(--muted, #888); }

.upload-msg { font-size: 13px; padding: 8px 12px; border-radius: 6px; }
.upload-msg.success { background: #d1fae5; color: #065f46; }
.upload-msg.error { background: #fee2e2; color: #dc2626; }
.upload-msg.info { background: #eff6ff; color: #1e40af; }

.upload-confirm-btn {
  padding: 10px;
  background: var(--accent, #2563eb);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.upload-confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.upload-confirm-btn:not(:disabled):hover { opacity: 0.88; }

/* Preview panel */
.preview-mask {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex; align-items: stretch; justify-content: flex-end;
}
.preview-panel {
  width: min(860px, 92vw);
  background: var(--paper, #fff);
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 40px rgba(0,0,0,0.2);
}
.preview-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border, #e5e7eb);
  flex-shrink: 0;
  gap: 12px;
}
.preview-title-group { display: flex; align-items: center; gap: 10px; min-width: 0; }
.preview-cat-tag {
  font-size: 11px; font-weight: 600;
  padding: 2px 8px; border-radius: 4px;
  background: #eff6ff; color: #1e40af;
  flex-shrink: 0;
}
.preview-filename { font-size: 14px; color: var(--ink, #1a1a2e); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.preview-head-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.preview-dl-btn {
  padding: 6px 14px;
  background: var(--surface, #f5f7ff);
  border: 1px solid var(--border, #d1d5db);
  border-radius: 6px;
  font-size: 13px;
  color: var(--ink, #1a1a2e);
  text-decoration: none;
  cursor: pointer;
}
.preview-dl-btn.large { padding: 10px 24px; font-size: 15px; margin-top: 16px; display: inline-block; }
.preview-close {
  width: 32px; height: 32px;
  background: none; border: none;
  font-size: 22px; color: var(--muted, #aaa);
  cursor: pointer; line-height: 1;
  display: flex; align-items: center; justify-content: center;
}

.preview-body { flex: 1; overflow: auto; padding: 0; }
.preview-loading, .preview-error { padding: 60px; text-align: center; color: var(--muted, #888); font-size: 14px; }
.preview-error { color: #dc2626; }
.preview-unsupported { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--muted, #888); font-size: 15px; }

/* Excel preview */
.excel-preview { display: flex; flex-direction: column; height: 100%; }
.sheet-tabs { display: flex; gap: 4px; padding: 10px 16px 0; flex-wrap: wrap; border-bottom: 1px solid var(--border, #e5e7eb); flex-shrink: 0; }
.sheet-tab {
  padding: 6px 14px;
  border: 1px solid var(--border, #e5e7eb);
  border-bottom: none;
  border-radius: 6px 6px 0 0;
  background: var(--surface, #f5f5f5);
  font-size: 12px; cursor: pointer; color: var(--muted, #666);
}
.sheet-tab.active { background: var(--paper, #fff); color: var(--ink, #1a1a2e); font-weight: 600; border-color: var(--border, #e5e7eb); }
.sheet-content { flex: 1; overflow: auto; padding: 16px; }
.sheet-content :deep(table) {
  border-collapse: collapse;
  font-size: 12px;
  white-space: nowrap;
  width: 100%;
}
.sheet-content :deep(td), .sheet-content :deep(th) {
  border: 1px solid #e5e7eb;
  padding: 5px 10px;
  color: var(--ink, #1a1a2e);
}
.sheet-content :deep(tr:nth-child(even)) { background: var(--surface, #fafafa); }

/* Word preview */
.docx-preview {
  padding: 32px 40px;
  max-width: 720px;
  margin: 0 auto;
  font-size: 14px;
  line-height: 1.8;
  color: var(--ink, #1a1a2e);
}
.docx-preview :deep(h1) { font-size: 20px; font-weight: 700; margin: 20px 0 10px; }
.docx-preview :deep(h2) { font-size: 17px; font-weight: 600; margin: 16px 0 8px; }
.docx-preview :deep(h3) { font-size: 15px; font-weight: 600; margin: 12px 0 6px; }
.docx-preview :deep(p) { margin: 6px 0; }
.docx-preview :deep(table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
.docx-preview :deep(td), .docx-preview :deep(th) { border: 1px solid #d1d5db; padding: 6px 12px; }

/* Delete modal */
.delete-warn { font-size: 14px; color: var(--ink, #1a1a2e); margin: 0 0 20px; line-height: 1.6; }
.delete-actions { display: flex; gap: 10px; justify-content: flex-end; }
.cancel-btn {
  padding: 8px 18px; border: 1px solid var(--border, #d1d5db);
  border-radius: 7px; background: var(--paper, #fff);
  font-size: 13px; cursor: pointer; color: var(--ink, #555);
}
.danger-btn {
  padding: 8px 18px; border: none;
  border-radius: 7px; background: #dc2626;
  color: #fff; font-size: 13px; cursor: pointer; font-weight: 600;
}
.danger-btn:hover { background: #b91c1c; }
</style>

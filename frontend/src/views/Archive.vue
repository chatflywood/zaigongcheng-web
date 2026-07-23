<template>
  <div class="archive-page page">
    <header class="page-head">
      <div class="page-head-l">
        <span class="eyebrow">数据档案 / Archive</span>
        <h1 class="page-title-h1">数据档案库</h1>
        <div class="page-meta">
          <span>仙桃分公司工程建设历年数据存储</span>
          <span class="ph-sep"></span>
          <span>支持 .xlsx / .docx / .pdf</span>
          <span class="ph-sep"></span>
          <span>{{ allRecords.length }} 份档案</span>
        </div>
      </div>
    </header>

    <div class="archive-body">
      <section
        v-for="cat in CATEGORIES"
        :key="cat.key"
        class="archive-cat-card ds-card"
      >
        <div class="cat-head">
          <div class="cat-icon" :class="'icn-' + cat.icon">
            <!-- chart -->
            <svg v-if="cat.icon === 'chart'" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M2 13h12M4 10v3M7 6v7M10 8v5M13 4v9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
            <!-- trend -->
            <svg v-else-if="cat.icon === 'trend'" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M2 11l4-4 3 3 5-6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M11 4h3v3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <!-- report -->
            <svg v-else viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M4 2h6l2 2v10H4V2zM10 2v2h2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M6 7h4M6 10h3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="cat-copy">
            <div class="cat-name">{{ cat.label }}</div>
            <div class="cat-desc">{{ cat.desc }}</div>
          </div>
          <div class="cat-meta mono" v-if="filesByCategory[cat.key]?.length">
            {{ filesByCategory[cat.key].length }}
            <span>FILES</span>
          </div>
          <button class="cat-upload-btn btn" @click="openUpload(cat.key)">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            上传
          </button>
        </div>

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
              <span class="file-meta">
                <span>{{ rec.year }}年</span>
                <span class="dot"></span>
                <span class="mono">{{ formatSize(rec.file_size) }}</span>
                <span class="dot"></span>
                <span class="mono">{{ formatDate(rec.uploaded_at) }}</span>
                <template v-if="rec.note">
                  <span class="dot"></span>
                  <span class="file-note">{{ rec.note }}</span>
                </template>
              </span>
            </div>
            <div class="file-actions" @click.stop>
              <a :href="getArchiveFileUrl(rec.id)" :download="rec.original_filename" class="file-btn" title="下载" aria-label="下载">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M3 12v1.5h10V12M5 8l3 3 3-3M8 3v8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </a>
              <button class="file-btn danger" @click="confirmDelete(rec)" title="删除" aria-label="删除">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
              </button>
            </div>
          </div>
        </div>
        <div class="cat-empty" v-else>
          <span class="cat-empty-mark">—</span>
          <span>暂无档案，点击「上传」添加</span>
        </div>
      </section>
    </div>

    <!-- 上传弹窗 -->
    <div class="arc-modal-mask" v-if="showUpload" @click.self="showUpload = false">
      <div class="arc-modal">
        <div class="arc-modal-head">
          <div>
            <div class="arc-modal-eyebrow">Upload</div>
            <div class="arc-modal-title">上传档案 · {{ uploadCatLabel }}</div>
          </div>
          <button class="arc-modal-close" @click="showUpload = false" aria-label="关闭">×</button>
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
            :class="{ dragging: isDragging, selected: !!uploadFile }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="onDrop"
            @click="fileInput?.click()"
          >
            <input ref="fileInput" type="file" accept=".xlsx,.xls,.docx,.pdf" class="dz-input" @change="onFilePick" />
            <div v-if="!uploadFile" class="dz-idle">
              <div class="dz-icon">
                <svg width="22" height="22" viewBox="0 0 34 34" fill="none" aria-hidden="true">
                  <rect x="4" y="7" width="26" height="22" rx="3" stroke="currentColor" stroke-width="1.4"/>
                  <path d="M11 14h12M11 18.5h8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                  <path d="M21.5 3v7M18 6l3.5-3.5L25 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="dz-text">拖拽文件到此处，或<span class="dz-link">点击选择</span></div>
              <div class="dz-hint mono">.xlsx · .xls · .docx · .pdf</div>
            </div>
            <div v-else class="dz-selected">
              <span class="file-ext-badge" :class="extClass('.' + (uploadFile.name.split('.').pop() || '').toLowerCase())">
                {{ (uploadFile.name.split('.').pop() || '').toUpperCase() }}
              </span>
              <span class="dz-file-name">{{ uploadFile.name }}</span>
              <span class="dz-file-size mono">{{ formatSize(uploadFile.size) }}</span>
            </div>
          </div>
          <div v-if="uploadMsg" class="upload-msg" :class="uploadMsgType">{{ uploadMsg }}</div>
          <button class="upload-confirm-btn btn primary" :disabled="!uploadFile || uploading" @click="doUpload">
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
            <a :href="getArchiveFileUrl(previewRecord.id)" :download="previewRecord.original_filename" class="btn">下载</a>
            <button class="preview-close" @click="closePreview" aria-label="关闭">×</button>
          </div>
        </div>

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

        <div v-else-if="isWord(previewRecord.ext)" class="preview-body">
          <div v-if="previewLoading" class="preview-loading">加载中…</div>
          <div v-else-if="previewError" class="preview-error">{{ previewError }}</div>
          <div v-else class="docx-preview" v-html="docxHtml"></div>
        </div>

        <div v-else class="preview-body preview-unsupported">
          <div class="unsupported-copy">该格式暂不支持在线预览</div>
          <a :href="getArchiveFileUrl(previewRecord.id)" :download="previewRecord.original_filename" class="btn primary">下载文件</a>
        </div>
      </div>
    </div>

    <!-- 删除确认 -->
    <div class="arc-modal-mask" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="arc-modal small">
        <div class="arc-modal-head">
          <div>
            <div class="arc-modal-eyebrow">Confirm</div>
            <div class="arc-modal-title">删除确认</div>
          </div>
          <button class="arc-modal-close" @click="deleteTarget = null" aria-label="关闭">×</button>
        </div>
        <div class="arc-modal-body">
          <p class="delete-warn">确定删除「{{ deleteTarget.original_filename }}」？此操作不可恢复。</p>
          <div class="delete-actions">
            <button class="btn ghost cancel-btn" @click="deleteTarget = null">取消</button>
            <button class="btn danger-btn" @click="doDelete">删除</button>
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
  { key: '年度建设情况', label: '年度建设情况', icon: 'chart', desc: '全年工程建设汇总、评分排名、专业指标' },
  { key: '多年趋势汇总', label: '多年趋势汇总', icon: 'trend', desc: '多年投资趋势、专业结构、省内排名对比' },
  { key: '投资预算报告', label: '投资预算报告', icon: 'report', desc: '立项执行、招标结果、资本支出分析报告' },
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
/* 页壳：叠 .page 走全局 max-width/padding；档案内容略收窄 */
.archive-page.page {
  max-width: 960px;
  padding-bottom: 64px;
}

.archive-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Category card ───────────────────────────────── */
.archive-cat-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.cat-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  background: var(--surface-2);
}

.cat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--accent-soft);
  color: var(--accent);
}
.cat-icon svg { width: 18px; height: 18px; }
.cat-icon.icn-trend { background: var(--info-soft); color: var(--info); }
.cat-icon.icn-report { background: var(--warn-soft); color: var(--warn); }

.cat-copy { min-width: 0; flex: 1; }
.cat-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  letter-spacing: -0.005em;
}
.cat-desc {
  font-size: 12px;
  color: var(--ink-3);
  margin-top: 3px;
  line-height: 1.4;
}

.cat-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  line-height: 1.1;
  flex-shrink: 0;
}
.cat-meta span {
  font-size: 10px;
  font-weight: 500;
  color: var(--ink-4);
  letter-spacing: 0.06em;
}

/* 保留 .cat-upload-btn 给测试；视觉对齐全局 .btn */
.cat-upload-btn.btn {
  margin-left: 4px;
  flex-shrink: 0;
}

.cat-files { padding: 6px 0; }
.cat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 28px 20px;
  color: var(--ink-4);
  font-size: 12.5px;
}
.cat-empty-mark {
  color: var(--ink-4);
  opacity: 0.7;
  font-family: var(--font-mono);
}

/* ── File row ────────────────────────────────────── */
.file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 120ms;
  border-left: 2px solid transparent;
}
.file-row:hover { background: var(--surface-2); }
.file-row.active {
  background: var(--accent-soft);
  border-left-color: var(--accent);
}

.file-ext-badge {
  font-size: 10px;
  font-weight: 600;
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  padding: 3px 7px;
  border-radius: 999px;
  flex-shrink: 0;
  line-height: 1.2;
}
.ext-xlsx { background: var(--ok-soft); color: var(--ok); }
.ext-docx { background: var(--info-soft); color: var(--info); }
.ext-other { background: var(--paper-2); color: var(--ink-3); border: 1px solid var(--line); }

.file-info { flex: 1; min-width: 0; }
.file-name {
  display: block;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 8px;
  font-size: 11.5px;
  color: var(--ink-3);
  margin-top: 3px;
}
.file-meta .dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--ink-4);
  flex-shrink: 0;
}
.file-note {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ink-2);
}

.file-actions { display: flex; gap: 6px; flex-shrink: 0; }
.file-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--r-md);
  border: 1px solid var(--line-2);
  background: var(--surface);
  color: var(--ink-2);
  cursor: pointer;
  text-decoration: none;
  transition: all 120ms;
}
.file-btn:hover {
  background: var(--paper-2);
  color: var(--ink);
  border-color: var(--ink-4);
}
.file-btn.danger:hover {
  background: var(--bad-soft);
  color: var(--bad);
  border-color: transparent;
}

/* ── Modal ───────────────────────────────────────── */
.arc-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(31, 29, 24, 0.36);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.arc-modal {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  width: 480px;
  max-width: 100%;
  box-shadow: var(--shadow-pop);
}
.arc-modal.small { width: 380px; }
.arc-modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--line);
}
.arc-modal-eyebrow {
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent);
  font-weight: 500;
  margin-bottom: 4px;
}
.arc-modal-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--ink);
  letter-spacing: -0.01em;
}
.arc-modal-close {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: var(--r-md);
  font-size: 20px;
  line-height: 1;
  color: var(--ink-3);
  cursor: pointer;
}
.arc-modal-close:hover {
  background: var(--paper-2);
  color: var(--ink);
}
.arc-modal-body {
  padding: 18px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.upload-field { display: flex; flex-direction: column; gap: 6px; }
.field-label {
  font-size: 11.5px;
  color: var(--ink-3);
  letter-spacing: 0.02em;
}
.field-select,
.field-input {
  padding: 9px 12px;
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  font-size: 13px;
  background: var(--surface);
  color: var(--ink);
  outline: none;
  font-family: inherit;
  transition: border-color 120ms, box-shadow 120ms;
}
.field-select:focus,
.field-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.upload-dropzone {
  border: 1.5px dashed var(--line-2);
  border-radius: var(--r-lg);
  padding: 28px 18px;
  text-align: center;
  cursor: pointer;
  background: var(--surface-2);
  transition: border-color 120ms, background 120ms;
}
.upload-dropzone:hover,
.upload-dropzone.dragging {
  border-color: var(--accent);
  background: var(--accent-soft);
}
.upload-dropzone.selected {
  border-style: solid;
  border-color: var(--line);
  background: var(--surface);
}
.dz-input { display: none; }
.dz-icon {
  width: 44px;
  height: 44px;
  margin: 0 auto 10px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--accent);
}
.dz-text {
  font-size: 13.5px;
  color: var(--ink-2);
}
.dz-link {
  color: var(--accent);
  font-weight: 500;
}
.dz-hint {
  font-size: 11px;
  color: var(--ink-4);
  margin-top: 6px;
}
.dz-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}
.dz-file-name {
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink);
  word-break: break-all;
}
.dz-file-size {
  font-size: 11.5px;
  color: var(--ink-3);
}

.upload-msg {
  font-size: 12.5px;
  padding: 8px 12px;
  border-radius: var(--r-md);
}
.upload-msg.success { background: var(--ok-soft); color: var(--ok); }
.upload-msg.error { background: var(--bad-soft); color: var(--bad); }
.upload-msg.info { background: var(--info-soft); color: var(--info); }

.upload-confirm-btn.btn {
  width: 100%;
  justify-content: center;
  padding: 10px 14px;
  font-size: 13.5px;
}

/* ── Preview drawer ──────────────────────────────── */
.preview-mask {
  position: fixed;
  inset: 0;
  background: rgba(31, 29, 24, 0.4);
  z-index: 1000;
  display: flex;
  align-items: stretch;
  justify-content: flex-end;
}
.preview-panel {
  width: min(860px, 94vw);
  background: var(--surface);
  border-left: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-pop);
}
.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
  background: var(--surface-2);
  gap: 12px;
  flex-shrink: 0;
}
.preview-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.preview-cat-tag {
  font-size: 10.5px;
  font-weight: 500;
  font-family: var(--font-mono);
  letter-spacing: 0.02em;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-ink);
  flex-shrink: 0;
}
.preview-filename {
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.preview-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.preview-close {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--r-md);
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: var(--ink-3);
  cursor: pointer;
}
.preview-close:hover {
  background: var(--paper-2);
  color: var(--ink);
}

.preview-body { flex: 1; overflow: auto; min-height: 0; }
.preview-loading,
.preview-error {
  padding: 64px 24px;
  text-align: center;
  color: var(--ink-3);
  font-size: 13.5px;
}
.preview-error { color: var(--bad); }
.preview-unsupported {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 280px;
  color: var(--ink-3);
  font-size: 14px;
}
.unsupported-copy { color: var(--ink-3); }

/* Excel */
.excel-preview { display: flex; flex-direction: column; height: 100%; min-height: 0; }
.sheet-tabs {
  display: flex;
  gap: 4px;
  padding: 10px 16px 0;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--line);
  background: var(--surface-2);
  flex-shrink: 0;
}
.sheet-tab {
  padding: 7px 12px;
  border: 1px solid transparent;
  border-bottom: none;
  border-radius: var(--r-md) var(--r-md) 0 0;
  background: transparent;
  font-size: 12px;
  color: var(--ink-3);
  cursor: pointer;
  font-family: inherit;
}
.sheet-tab:hover { color: var(--ink); background: var(--paper-2); }
.sheet-tab.active {
  background: var(--surface);
  color: var(--ink);
  font-weight: 500;
  border-color: var(--line);
}
.sheet-content { flex: 1; overflow: auto; padding: 16px; }
.sheet-content :deep(table) {
  border-collapse: collapse;
  font-size: 12px;
  white-space: nowrap;
  width: 100%;
  font-variant-numeric: tabular-nums;
}
.sheet-content :deep(td),
.sheet-content :deep(th) {
  border: 1px solid var(--line);
  padding: 6px 10px;
  color: var(--ink);
}
.sheet-content :deep(tr:nth-child(even)) { background: var(--surface-2); }
.sheet-content :deep(th) {
  background: var(--paper-2);
  font-weight: 500;
  color: var(--ink-2);
}

/* Word */
.docx-preview {
  padding: 32px 40px 48px;
  max-width: 720px;
  margin: 0 auto;
  font-size: 14px;
  line-height: 1.8;
  color: var(--ink);
}
.docx-preview :deep(h1) { font-size: 20px; font-weight: 500; margin: 20px 0 10px; letter-spacing: -0.02em; }
.docx-preview :deep(h2) { font-size: 17px; font-weight: 500; margin: 16px 0 8px; }
.docx-preview :deep(h3) { font-size: 15px; font-weight: 500; margin: 12px 0 6px; }
.docx-preview :deep(p) { margin: 6px 0; }
.docx-preview :deep(table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
.docx-preview :deep(td),
.docx-preview :deep(th) {
  border: 1px solid var(--line);
  padding: 6px 12px;
}

/* Delete */
.delete-warn {
  font-size: 13.5px;
  color: var(--ink-2);
  margin: 0;
  line-height: 1.6;
}
.delete-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.btn.danger-btn,
.danger-btn {
  background: var(--bad);
  color: #fff;
  border-color: var(--bad);
}
.btn.danger-btn:hover,
.danger-btn:hover {
  filter: brightness(0.95);
  background: var(--bad);
  border-color: var(--bad);
  color: #fff;
}
</style>

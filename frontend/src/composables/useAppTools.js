/**
 * 应用工具 composable
 *
 * 管理通知设置、简报生成、推送播报等全局工具功能。
 */
import { ref } from 'vue'
import { getNotifyConfig, saveNotifyConfig, clearNotifyConfig, testNotifyWebhook, pushNotify, generateBriefImage, getBackupStatus, exportBackup, restoreBackup } from '../api'
import { useGlobalData } from './useGlobalData'

// ── 数据管理面板 ──

const showDataManager = ref(false)
const dmZaigongFile = ref(null)
const dmZaigongFileName = ref('')
const dmZaigongMsg = ref('')
const dmZaigongMsgType = ref('info')
const dmZaigongLoading = ref(false)
const dmBudgetFile = ref(null)
const dmBudgetFileName = ref('')
const dmBudgetMsg = ref('')
const dmBudgetMsgType = ref('info')
const dmBudgetLoading = ref(false)
const dmZaigongBusinessDate = ref('')
const dmBudgetBusinessDate = ref('')
const dmTargetValue = ref(null)
const dmRateTarget = ref(null) // 当期转固率目标（%），与 Dashboard 共用 localStorage
const dmZaigongInput = ref(null)
const dmBudgetInput = ref(null)

// ── 通知设置 ──

const notifyModalVisible = ref(false)
const notifyProvider = ref('wework')
const notifyWebhookInput = ref('')
const notifyAutoPush = ref(false)
const notifyConfigured = ref(false)
const notifyMaskedUrl = ref('')
const notifySaving = ref(false)
const notifyTesting = ref(false)
const notifyMsg = ref('')
const notifyMsgType = ref('')

// ── 工具栏 ──

const moreMenuOpen = ref(false)
const briefGenerating = ref(false)
const navPushing = ref(false)
const presentationMode = ref(false)

// ── 数据备份 / 恢复 ──
const backupStatus = ref(null)
const backupLoading = ref(false)
const backupMsg = ref('')
const backupMsgType = ref('info')
const backupFileInput = ref(null)

export function useAppTools() {
  const {
    zaigongData, budgetData, zaigongLatestData, budgetLatestData,
    zaigongLatestRecordId, budgetLatestRecordId,
    zaigongLatestDate, budgetLatestDate,
    zaigongFourClassWarnings, zaigongLatestFourClassWarnings,
    onZaigongDataUpdate, onBudgetDataUpdate,
    uploadExcel, uploadBudget,
  } = useGlobalData()

  // ── 数据管理面板 ──

  function openDataManager() {
    dmTargetValue.value = Number(localStorage.getItem('zaigong_target_value')) || null
    const savedRate = Number(localStorage.getItem('zaigong_rate_target'))
    dmRateTarget.value = (savedRate > 0 && savedRate <= 100) ? savedRate : null
    dmZaigongFileName.value = ''
    dmZaigongMsg.value = ''
    dmZaigongMsgType.value = 'info'
    dmBudgetFileName.value = ''
    dmBudgetMsg.value = ''
    dmBudgetMsgType.value = 'info'
    backupMsg.value = ''
    backupMsgType.value = 'info'
    showDataManager.value = true
    refreshBackupStatus()
  }

  function persistDmRateTarget() {
    try {
      const val = Number(dmRateTarget.value)
      if (val > 0 && val <= 100) {
        localStorage.setItem('zaigong_rate_target', String(val))
        window.dispatchEvent(new CustomEvent('zaigong-rate-target-changed', { detail: val }))
      } else {
        localStorage.removeItem('zaigong_rate_target')
        if (dmRateTarget.value !== null && dmRateTarget.value !== '') {
          dmRateTarget.value = null
        }
        window.dispatchEvent(new CustomEvent('zaigong-rate-target-changed', { detail: null }))
      }
    } catch { /* ignore quota / private mode */ }
  }

  function daysSince(dateStr) {
    if (!dateStr) return null
    const d = new Date(dateStr)
    if (isNaN(d)) return null
    return Math.floor((Date.now() - d.getTime()) / 86400000)
  }

  function dmFreshClass(days) {
    if (days === null) return ''
    if (days > 60) return 'stale-bad'
    if (days > 30) return 'stale-warn'
    return 'stale-ok'
  }

  function dmPickZaigong() { dmZaigongInput.value?.click() }
  function dmPickBudget() { dmBudgetInput.value?.click() }

  function dmOnZaigongFile(e) {
    const f = e.target.files[0]; if (!f) return
    dmZaigongFile.value = f; dmZaigongFileName.value = f.name; dmZaigongMsg.value = ''
  }
  function dmOnBudgetFile(e) {
    const f = e.target.files[0]; if (!f) return
    dmBudgetFile.value = f; dmBudgetFileName.value = f.name; dmBudgetMsg.value = ''
  }
  function dmDropZaigong(e) {
    const f = e.dataTransfer.files[0]; if (!f) return
    dmZaigongFile.value = f; dmZaigongFileName.value = f.name; dmZaigongMsg.value = ''
  }
  function dmDropBudget(e) {
    const f = e.dataTransfer.files[0]; if (!f) return
    dmBudgetFile.value = f; dmBudgetFileName.value = f.name; dmBudgetMsg.value = ''
  }

  async function dmUploadZaigong() {
    if (!dmZaigongFile.value) { dmZaigongMsg.value = '请先选择文件'; dmZaigongMsgType.value = 'error'; return }
    if (!dmTargetValue.value) { dmZaigongMsg.value = '请先设置目标金额'; dmZaigongMsgType.value = 'error'; return }
    dmZaigongLoading.value = true
    dmZaigongMsg.value = '上传中…'
    try {
      const { uploadExcel } = await import('../api')
      const result = await uploadExcel(dmZaigongFile.value, dmTargetValue.value, dmZaigongBusinessDate.value)
      if (result.success) {
        localStorage.setItem('zaigong_target_value', dmTargetValue.value)
        const dashData = result.data?.dashboard || result.data
        zaigongFourClassWarnings.value = result.data?.four_class_warnings || null
        zaigongLatestFourClassWarnings.value = result.data?.four_class_warnings || null
        await onZaigongDataUpdate(dashData)
        dmZaigongFileName.value = ''
        dmZaigongFile.value = null
        dmZaigongMsg.value = result.message || result.validation?.summary_text || '上传成功'
        dmZaigongMsgType.value = 'success'
      } else {
        dmZaigongMsg.value = result.message || '上传失败'
        dmZaigongMsgType.value = 'error'
      }
    } catch (e) {
      dmZaigongMsg.value = '上传失败：' + (e.message || '未知错误')
      dmZaigongMsgType.value = 'error'
    } finally {
      dmZaigongLoading.value = false
    }
  }

  async function dmUploadBudget() {
    if (!dmBudgetFile.value) { dmBudgetMsg.value = '请先选择文件'; dmBudgetMsgType.value = 'error'; return }
    dmBudgetLoading.value = true
    dmBudgetMsg.value = '上传中…'
    try {
      const { uploadBudget } = await import('../api')
      const result = await uploadBudget(dmBudgetFile.value, dmBudgetBusinessDate.value)
      if (result.success) {
        await onBudgetDataUpdate(result.data)
        dmBudgetFileName.value = ''
        dmBudgetFile.value = null
        dmBudgetMsg.value = result.message || result.validation?.summary_text || '上传成功'
        dmBudgetMsgType.value = 'success'
      } else {
        dmBudgetMsg.value = result.message || '上传失败'
        dmBudgetMsgType.value = 'error'
      }
    } catch (e) {
      dmBudgetMsg.value = '上传失败：' + (e.message || '未知错误')
      dmBudgetMsgType.value = 'error'
    } finally {
      dmBudgetLoading.value = false
    }
  }

  // ── 通知设置 ──

  async function openNotifyModal() {
    notifyMsg.value = ''
    notifyWebhookInput.value = ''
    notifyModalVisible.value = true
    try {
      const res = await getNotifyConfig()
      if (res.success) {
        notifyProvider.value = res.provider || 'wework'
        notifyConfigured.value = res.configured
        notifyMaskedUrl.value = res.masked_url
        notifyAutoPush.value = res.auto_push
      }
    } catch (e) {
      console.error('获取通知配置失败', e)
    }
  }

  async function saveNotify() {
    if (!notifyWebhookInput.value.trim() && !notifyMaskedUrl.value) {
      notifyMsg.value = '请输入 Webhook URL'; notifyMsgType.value = 'error'; return
    }
    notifySaving.value = true; notifyMsg.value = ''
    try {
      const payload = {
        provider: notifyProvider.value,
        auto_push: notifyAutoPush.value,
        webhook_url: notifyWebhookInput.value.trim(),
      }
      const res = await saveNotifyConfig(payload)
      if (res.success) {
        notifyMsg.value = '配置已保存'; notifyMsgType.value = 'success'; notifyConfigured.value = true
        const cfg = await getNotifyConfig()
        if (cfg.success) {
          notifyMaskedUrl.value = cfg.masked_url
        }
        notifyWebhookInput.value = ''
      } else {
        notifyMsg.value = res.message || '保存失败'; notifyMsgType.value = 'error'
      }
    } catch (e) {
      notifyMsg.value = e?.response?.data?.message || e?.message || '保存失败'; notifyMsgType.value = 'error'
    } finally { notifySaving.value = false }
  }

  async function testNotify() {
    const url = notifyWebhookInput.value.trim()
    if (!url && !notifyMaskedUrl.value) {
      notifyMsg.value = '请先输入 Webhook URL 再测试'; notifyMsgType.value = 'error'; return
    }
    notifyTesting.value = true; notifyMsg.value = ''
    try {
      const payload = { provider: notifyProvider.value, webhook_url: url }
      const res = await testNotifyWebhook(payload)
      if (res.success) {
        notifyMsg.value = '✅ 测试消息已发送，请在所选平台中查看'; notifyMsgType.value = 'success'
      } else {
        notifyMsg.value = res.message || '发送失败'; notifyMsgType.value = 'error'
      }
    } catch (e) {
      notifyMsg.value = e?.response?.data?.message || e?.message || '请求失败'; notifyMsgType.value = 'error'
    } finally { notifyTesting.value = false }
  }

  async function clearNotify() {
    if (!confirm('确认清除通知配置？')) return
    try {
      await clearNotifyConfig()
      notifyConfigured.value = false; notifyMaskedUrl.value = ''
      notifyWebhookInput.value = ''; notifyAutoPush.value = false
      notifyProvider.value = 'wework'
      notifyMsg.value = '已清除'; notifyMsgType.value = 'success'
    } catch (e) {
      notifyMsg.value = '清除失败'; notifyMsgType.value = 'error'
    }
  }

  // ── 工具栏 ──

  function toggleMoreMenu() { moreMenuOpen.value = !moreMenuOpen.value }
  function closeMoreMenu() { moreMenuOpen.value = false }

  async function handleGenerateBrief() {
    if (!zaigongLatestRecordId.value || briefGenerating.value) return
    briefGenerating.value = true
    try {
      const blob = await generateBriefImage(zaigongLatestRecordId.value, budgetLatestRecordId.value || null)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = '在建工程简报.png'
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      alert(e?.response?.data?.message || e?.message || '简报生成失败')
    } finally { briefGenerating.value = false }
  }

  async function handleNavPush() {
    if (!zaigongLatestRecordId.value || navPushing.value) return
    navPushing.value = true
    try {
      const res = await pushNotify(zaigongLatestRecordId.value)
      if (res.success) alert('推送成功，请在已配置的通知平台中查看')
      else alert(res.message || '推送失败')
    } catch (e) {
      alert(e?.response?.data?.message || e?.message || '推送失败')
    } finally { navPushing.value = false }
  }

  function togglePresentationMode() {
    presentationMode.value = !presentationMode.value
  }

  function formatBytes(n) {
    const v = Number(n) || 0
    if (v < 1024) return `${v} B`
    if (v < 1024 * 1024) return `${(v / 1024).toFixed(1)} KB`
    return `${(v / 1024 / 1024).toFixed(2)} MB`
  }

  async function refreshBackupStatus() {
    try {
      const res = await getBackupStatus()
      if (res.success) backupStatus.value = res.data
    } catch (e) {
      console.error('读取备份状态失败', e)
    }
  }

  async function handleExportBackup() {
    if (backupLoading.value) return
    backupLoading.value = true
    backupMsg.value = '正在打包备份…'
    backupMsgType.value = 'info'
    try {
      const response = await exportBackup()
      const blob = response.data
      const dispo = response.headers?.['content-disposition'] || ''
      const m = /filename="?([^";]+)"?/i.exec(dispo)
      const filename = m?.[1] || `zaigongcheng_backup_${new Date().toISOString().slice(0, 10)}.zip`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      backupMsg.value = '备份已下载'
      backupMsgType.value = 'success'
      await refreshBackupStatus()
    } catch (e) {
      backupMsg.value = e?.response?.data?.message || e?.message || '备份导出失败'
      backupMsgType.value = 'error'
    } finally {
      backupLoading.value = false
    }
  }

  function triggerRestorePicker() {
    backupFileInput.value?.click?.()
  }

  async function handleRestoreBackupFile(event) {
    const file = event?.target?.files?.[0]
    if (event?.target) event.target.value = ''
    if (!file) return
    const ok = window.confirm(
      `恢复备份将覆盖当前全部分析数据与档案文件，且不可撤销。

建议先导出一份当前备份。是否继续恢复？`
    )
    if (!ok) return
    backupLoading.value = true
    backupMsg.value = '正在恢复备份…'
    backupMsgType.value = 'info'
    try {
      const res = await restoreBackup(file)
      if (res.success) {
        backupMsg.value = `恢复完成（档案 ${res.restored_archive_count || 0} 个）。请刷新页面加载最新数据。`
        backupMsgType.value = 'success'
        await refreshBackupStatus()
        // 重新拉最新快照
        const { loadLatestDataOnMount } = useGlobalData()
        await loadLatestDataOnMount()
      } else {
        backupMsg.value = res.message || '恢复失败'
        backupMsgType.value = 'error'
      }
    } catch (e) {
      backupMsg.value = e?.response?.data?.message || e?.message || '恢复失败'
      backupMsgType.value = 'error'
    } finally {
      backupLoading.value = false
    }
  }

  return {
    // 数据管理
    showDataManager, dmZaigongFile, dmZaigongFileName, dmZaigongMsg, dmZaigongMsgType, dmZaigongLoading,
    dmBudgetFile, dmBudgetFileName, dmBudgetMsg, dmBudgetMsgType, dmBudgetLoading,
    dmZaigongBusinessDate, dmBudgetBusinessDate, dmTargetValue, dmRateTarget, dmZaigongInput, dmBudgetInput,
    openDataManager, persistDmRateTarget, dmPickZaigong, dmPickBudget,
    dmOnZaigongFile, dmOnBudgetFile, dmDropZaigong, dmDropBudget,
    dmUploadZaigong, dmUploadBudget,
    daysSince, dmFreshClass,
    // 通知
    notifyModalVisible, notifyProvider, notifyWebhookInput, notifyAutoPush, notifyConfigured, notifyMaskedUrl,
    notifySaving, notifyTesting, notifyMsg, notifyMsgType,
    openNotifyModal, saveNotify, testNotify, clearNotify,
    // 工具栏
    moreMenuOpen, briefGenerating, navPushing, presentationMode,
    toggleMoreMenu, closeMoreMenu, handleGenerateBrief, handleNavPush, togglePresentationMode,
    // 备份
    backupStatus, backupLoading, backupMsg, backupMsgType, backupFileInput,
    refreshBackupStatus, handleExportBackup, triggerRestorePicker, handleRestoreBackupFile, formatBytes,
  }
}

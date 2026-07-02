/**
 * 文件上传交互 composable
 *
 * 管理 Dashboard / Budget 共享的上传 UI 状态与交互（选文件、拖拽、清空）。
 * 采用工厂模式（per-instance）。processFile 业务编排逻辑差异大，由各页面注入。
 *
 * @param {object} opts
 * @param {boolean} [opts.requireTarget=false] - 是否要求先设置目标值（Dashboard 需要）
 * @param {() => any} [opts.getTargetValue] - 读取目标值的回调（requireTarget 时用于前置校验）
 * @param {() => boolean} [opts.isReady=()=>true] - 是否满足自动上传条件
 * @param {(file: File) => Promise<void>} opts.processFile - 满足条件时调用的上传处理函数（各页面提供）
 */
import { ref } from 'vue'

export function useFileUpload({
  requireTarget = false,
  getTargetValue = () => null,
  isReady = () => true,
  processFile,
} = {}) {
  // ── 状态（per-instance） ──
  const fileInput = ref(null)
  const selectedFile = ref(null)
  const selectedFileName = ref('')
  const uploadMessage = ref('')
  const uploadMessageType = ref('info')

  // ── 操作 ──

  function triggerFileInput() {
    if (requireTarget && !getTargetValue()) {
      uploadMessage.value = '请先输入目标金额'
      uploadMessageType.value = 'error'
      return
    }
    uploadMessage.value = ''
    fileInput.value?.click()
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      selectedFile.value = file
      selectedFileName.value = file.name
      uploadMessage.value = `已选择文件：${file.name}`
      uploadMessageType.value = 'info'
      if (isReady()) await processFile(file)
    }
  }

  async function handleDrop(e) {
    const file = e.dataTransfer.files?.[0]
    if (file) {
      selectedFile.value = file
      selectedFileName.value = file.name
      uploadMessage.value = `已选择文件：${file.name}`
      uploadMessageType.value = 'info'
      if (isReady()) await processFile(file)
    }
  }

  function clearSelectedFile() {
    selectedFile.value = null
    selectedFileName.value = ''
    uploadMessage.value = ''
    if (fileInput.value) fileInput.value.value = ''
  }

  return {
    // 状态
    fileInput,
    selectedFile,
    selectedFileName,
    uploadMessage,
    uploadMessageType,
    // 操作
    triggerFileInput,
    handleFileChange,
    handleDrop,
    clearSelectedFile,
  }
}

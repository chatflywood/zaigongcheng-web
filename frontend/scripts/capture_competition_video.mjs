import { copyFile, mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendDir = path.resolve(scriptDir, '..')
const projectDir = path.resolve(frontendDir, '..')
const baseUrl = process.env.DEMO_FRONTEND_URL || 'http://127.0.0.1:5174/zaigongcheng-web/'
const outputDir = path.resolve(
  process.env.CAPTURE_OUTPUT_DIR
    || path.join(frontendDir, 'output/playwright/video-v2-sanitized'),
)
const demoExcel = path.resolve(
  process.env.DEMO_EXCEL
    || path.join(projectDir, 'competition/demo-data/在建工程演示数据.xlsx'),
)

await mkdir(outputDir, { recursive: true })

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
})

page.on('console', message => {
  if (message.type() === 'error') {
    console.error(`[browser] ${message.text()}`)
  }
})

async function openRoute(hash) {
  await page.goto(`${baseUrl}${hash}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1400)
}

async function capture(name) {
  const destination = path.join(outputDir, name)
  await page.screenshot({ path: destination })
  return destination
}

async function copy(sourceName, ...targetNames) {
  for (const targetName of targetNames) {
    await copyFile(
      path.join(outputDir, sourceName),
      path.join(outputDir, targetName),
    )
  }
}

try {
  await openRoute('#/')
  await capture('key-indicators.png')
  await copy(
    'key-indicators.png',
    'key-indicators-intro.png',
    'key-indicators-upload.png',
    'key-indicators-history.png',
    'key-indicators-notify.png',
  )

  const dataManagerLink = page.locator('.side-link').filter({ hasText: '数据管理' })
  await dataManagerLink.click()
  await page.locator('.dm-panel').waitFor({ state: 'visible' })
  await page.waitForTimeout(350)
  await capture('data-manager.png')
  await page.locator('.dm-panel input[type="file"]').first().setInputFiles(demoExcel)
  await page.waitForTimeout(350)
  await capture('data-manager-selected.png')
  await page.locator('.dm-panel .modal-close').click()

  const historyLink = page.locator('.side-link').filter({ hasText: '上传历史' })
  await historyLink.click()
  await page.locator('.gh-panel').waitFor({ state: 'visible' })
  await page.waitForTimeout(650)
  await capture('upload-history.png')
  await page.locator('.gh-close').click()

  const notifyLink = page.locator('.side-link').filter({ hasText: '通知设置' })
  await notifyLink.click()
  await page.locator('.notify-modal').waitFor({ state: 'visible' })
  await page.waitForTimeout(350)
  await capture('notify-settings.png')
  await page.locator('.notify-modal .modal-close').click()

  await openRoute('#/zaigong')
  const warningManagerGrid = page.locator('.warning-manager-grid')
  await warningManagerGrid.waitFor({ state: 'visible' })
  await warningManagerGrid.scrollIntoViewIfNeeded()
  await page.waitForTimeout(500)
  await capture('zaigong-warning-manager.png')
  await copy(
    'zaigong-warning-manager.png',
    'zaigong-intro.png',
    'zaigong-manager.png',
  )

  const warningCard = warningManagerGrid.locator('.card').first()
  await warningCard.getByText('查看全部', { exact: true }).click()
  await page.locator('.four-class-modal').waitFor({ state: 'visible' })
  await page.waitForTimeout(400)
  await capture('warning-modal.png')
  await page.locator('.four-class-modal .modal-close').click()

  const managerCard = warningManagerGrid.locator('.card').nth(1)
  await managerCard.locator('tbody tr').nth(1).click()
  const managerDrawer = page.locator('.mgr-drawer')
  await managerDrawer.waitFor({ state: 'visible' })
  await page.waitForTimeout(650)
  await capture('manager-drawer.png')
  const pendingHeader = managerDrawer
    .locator('th.sortable')
    .filter({ hasText: '已下单待收货' })
  await pendingHeader.click()
  await page.waitForTimeout(500)
  await capture('manager-drawer-sorted.png')

  await openRoute('#/budget')
  await page.waitForTimeout(600)
  await capture('budget.png')
  await copy('budget.png', 'budget-intro.png')

  await openRoute('#/archive')
  await page.waitForTimeout(600)
  await capture('archive.png')
} finally {
  await browser.close()
}

console.log(`Sanitized video captures written to ${outputDir}`)

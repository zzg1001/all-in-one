<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{ source: any; rawOcrText?: string }>()

// 基础信息字段定义（顺序与下载的 Word 文档保持一致）
const BASIC_FIELDS: { key: string; label: string }[] = [
  { key: '企业名称', label: '企业名称' },
  { key: '统一社会信用代码', label: '统一社会信用代码' },
  { key: '法定代表人', label: '法定代表人' },
  { key: '注册时间', label: '注册时间' },
  { key: '成立时间', label: '成立时间' },
  { key: '注册资本', label: '注册资本' },
  { key: '注册地址', label: '注册地址' },
  { key: '办公地址', label: '办公地址' },
  { key: '企业性质', label: '企业性质' },
  { key: '单位规模', label: '单位规模' },
  { key: '所属行业', label: '所属行业' },
  { key: '经营范围', label: '经营范围' },
  { key: '核心技术', label: '核心技术' },
  { key: '官网', label: '官网' },
  { key: '联系人', label: '联系人' },
  { key: '联系电话', label: '联系电话' },
  { key: '简介', label: '简介' },
]

const editBasic = ref<Record<string, string>>({})
const editExtra = ref<Record<string, string>>({
  核心产品: '', 解决方案: '', 成功案例: '', AI能力: '', 生态伙伴: '',
  能力标签核心技术: '', 能力标签服务能力: '',
})

const rootRef = ref<HTMLElement | null>(null)

// 数组 <-> 多行文本 互转
function arrToLines(v: any): string {
  if (Array.isArray(v)) return v.filter((x) => x != null && String(x).trim()).join('\n')
  return v == null ? '' : String(v)
}
function linesToArr(s: string): string[] {
  return (s || '').split('\n').map((x) => x.trim()).filter(Boolean)
}

function initFromSource(data: any) {
  if (!data) { editBasic.value = {}; return }
  const tech = data.核心技术 ?? data.能力标签?.核心技术
  const techStr = Array.isArray(tech) ? tech.join('、') : (tech || '')
  editBasic.value = {
    '企业名称': data.企业名称 || '',
    '统一社会信用代码': data.统一社会信用码 || data.统一社会信用代码 || '',
    '法定代表人': data.法定代表人 || '',
    '注册时间': data.注册时间 || data.核准日期 || '',
    '成立时间': data.成立时间 || data.成立日期 || '',
    '注册资本': data.注册资本 || '',
    '注册地址': data.注册地址 || data.住所 || '',
    '办公地址': data.办公地址 || '',
    '企业性质': data.企业性质 || data.企业类型 || '',
    '单位规模': data.单位规模 || '',
    '所属行业': data.所属行业 || '',
    '经营范围': data.经营范围 || '',
    '核心技术': techStr,
    '官网': data.官网 || '',
    '联系人': data.联系人 || '',
    '联系电话': data.联系电话 || '',
    '简介': data.简介 || '',
  }

  let tagTech = '', tagService = ''
  const tags = data.能力标签
  if (tags && typeof tags === 'object' && !Array.isArray(tags)) {
    tagTech = arrToLines(tags.核心技术)
    tagService = arrToLines(tags.服务能力)
  } else if (Array.isArray(tags)) {
    tagTech = arrToLines(tags)
  }

  editExtra.value = {
    核心产品: arrToLines(data.核心产品),
    解决方案: arrToLines(data.解决方案),
    成功案例: arrToLines(data.成功案例),
    AI能力: typeof data.AI能力 === 'string' ? data.AI能力 : arrToLines(data.AI能力),
    生态伙伴: typeof data.生态伙伴 === 'string' ? data.生态伙伴 : arrToLines(data.生态伙伴),
    能力标签核心技术: tagTech,
    能力标签服务能力: tagService,
  }
}

// 合并编辑后的所有内容 + 原始数据
function buildEditedData(): Record<string, any> {
  const base: Record<string, any> = { ...(props.source || {}) }
  Object.assign(base, editBasic.value)
  base['统一社会信用码'] = editBasic.value['统一社会信用代码'] || ''
  base['核心产品'] = linesToArr(editExtra.value.核心产品)
  base['解决方案'] = linesToArr(editExtra.value.解决方案)
  base['成功案例'] = linesToArr(editExtra.value.成功案例)
  base['AI能力'] = editExtra.value.AI能力
  base['生态伙伴'] = editExtra.value.生态伙伴
  base['能力标签'] = {
    核心技术: linesToArr(editExtra.value.能力标签核心技术),
    服务能力: linesToArr(editExtra.value.能力标签服务能力),
  }
  return base
}

// 自动撑高指令：textarea 高度随内容增长，保证内容全部可见、不被截断
const vAutoGrow = {
  mounted(el: HTMLTextAreaElement) {
    const resize = () => { el.style.height = 'auto'; el.style.height = el.scrollHeight + 'px' }
    ;(el as any).__resize = resize
    el.addEventListener('input', resize)
    resize()
  },
  updated(el: HTMLTextAreaElement) {
    const r = (el as any).__resize
    if (r) r()
  },
  unmounted(el: HTMLTextAreaElement) {
    const r = (el as any).__resize
    if (r) el.removeEventListener('input', r)
  },
}

function resizeAll() {
  rootRef.value?.querySelectorAll<HTMLTextAreaElement>('textarea.info-input').forEach((el) => {
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  })
}

watch(() => props.source, (v) => {
  initFromSource(v)
  nextTick(resizeAll)
}, { immediate: true })

defineExpose({ buildEditedData })
</script>

<template>
  <div class="enterprise-info-form" ref="rootRef">
    <!-- 基础信息（可编辑） -->
    <div class="result-card">
      <div class="card-header">
        基础信息
        <span class="card-header-hint">内容可编辑，下载内容以编辑后为准</span>
      </div>
      <div class="card-body">
        <div class="info-row" v-for="field in BASIC_FIELDS" :key="field.key">
          <span class="info-label">{{ field.label }}</span>
          <textarea
            class="info-input"
            v-auto-grow
            v-model="editBasic[field.key]"
            rows="1"
            :placeholder="'请输入' + field.label"
          ></textarea>
        </div>
      </div>
    </div>

    <!-- 核心产品 -->
    <div class="result-card">
      <div class="card-header">核心产品<span class="card-header-hint">每行一项</span></div>
      <div class="card-body">
        <textarea class="info-input block-input" v-auto-grow v-model="editExtra.核心产品" rows="2" placeholder="每行一个产品"></textarea>
      </div>
    </div>

    <!-- 解决方案 -->
    <div class="result-card">
      <div class="card-header">解决方案<span class="card-header-hint">每行一项</span></div>
      <div class="card-body">
        <textarea class="info-input block-input" v-auto-grow v-model="editExtra.解决方案" rows="2" placeholder="每行一个解决方案"></textarea>
      </div>
    </div>

    <!-- 成功案例 -->
    <div class="result-card">
      <div class="card-header">成功案例<span class="card-header-hint">每行一项</span></div>
      <div class="card-body">
        <textarea class="info-input block-input" v-auto-grow v-model="editExtra.成功案例" rows="2" placeholder="每行一个案例"></textarea>
      </div>
    </div>

    <!-- AI能力 -->
    <div class="result-card">
      <div class="card-header">AI能力</div>
      <div class="card-body">
        <textarea class="info-input block-input" v-auto-grow v-model="editExtra.AI能力" rows="2" placeholder="请输入 AI 能力描述"></textarea>
      </div>
    </div>

    <!-- 生态伙伴 -->
    <div class="result-card">
      <div class="card-header">生态伙伴</div>
      <div class="card-body">
        <textarea class="info-input block-input" v-auto-grow v-model="editExtra.生态伙伴" rows="2" placeholder="请输入生态伙伴"></textarea>
      </div>
    </div>

    <!-- 能力标签 -->
    <div class="result-card">
      <div class="card-header">能力标签<span class="card-header-hint">每行一项</span></div>
      <div class="card-body">
        <div class="info-row">
          <span class="info-label">核心技术</span>
          <textarea class="info-input" v-auto-grow v-model="editExtra.能力标签核心技术" rows="1" placeholder="每行一个标签"></textarea>
        </div>
        <div class="info-row">
          <span class="info-label">服务能力</span>
          <textarea class="info-input" v-auto-grow v-model="editExtra.能力标签服务能力" rows="1" placeholder="每行一个标签"></textarea>
        </div>
      </div>
    </div>

    <!-- 原始 OCR 文本（调试用） -->
    <div class="result-card" v-if="rawOcrText">
      <div class="card-header" style="background: #64748b;">原始 OCR 识别文本</div>
      <div class="card-body">
        <pre class="raw-ocr-text">{{ rawOcrText }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-card {
  background: white;
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--border, #e5e7eb);
}

.card-header {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  padding: 12px 16px;
  font-size: 15px;
  font-weight: 600;
}

.card-header-hint {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.85);
}

.card-body {
  padding: 16px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  font-size: 14px;
  border-bottom: 1px solid #f3f4f6;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  width: 120px;
  color: #6b7280;
  flex-shrink: 0;
  font-weight: 500;
  padding-top: 7px;
  line-height: 1.5;
}

/* 可编辑输入框（textarea，自动撑高、自动换行、不截断） */
.info-input {
  flex: 1;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  color: var(--text, #1f2937);
  background: #f8fafc;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 6px 8px;
  resize: none;
  overflow: hidden;
  white-space: pre-wrap;
  word-break: break-word;
  transition: border-color 0.18s ease, background 0.18s ease;
}
.info-input:hover {
  background: #f1f5f9;
}
.info-input:focus {
  outline: none;
  background: #fff;
  border-color: var(--primary, #1677FF);
}

.block-input {
  display: block;
  width: 100%;
}

.raw-ocr-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text, #1f2937);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  font-family: 'Noto Sans SC', monospace;
}
</style>

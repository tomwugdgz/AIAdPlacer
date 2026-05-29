"""
一键生成 BMN Vue 前端所有文件
运行：D:/Mirofish/AIAdPlacer/backend/venv/Scripts/python.exe create_bmn_vue.py
"""
import os

BASE = r"D:\Mirofish\AIAdPlacer\bmn-frontend"

files = {

    # ── main.js ──
    "src/main.js": '''
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.mount('#app')
''',

    # ── App.vue ──
    "src/App.vue": '''
<template>
  <el-container style="height:100vh">
    <el-header style="background:#2B6CB2;padding:0 20px;display:flex;align-items:center">
      <span style="color:white;font-size:18px;font-weight:600">BMN 品牌智能增长操作系统</span>
      <el-menu :default-active="activeMenu" mode="horizontal" style="margin-left:40px;background:transparent" text-color="#ffffffcc" active-text-color="#ffffff">
        <el-menu-item index="brand" @click="$router.push('/brand')">品牌引擎</el-menu-item>
        <el-menu-item index="assets" @click="$router.push('/assets')">资产金库</el-menu-item>
        <el-menu-item index="workflow" @click="$router.push('/workflow')">案例工作流</el-menu-item>
      </el-menu>
    </el-header>
    <el-main style="background:#f5f5f5;padding:20px">
      <router-view/>
    </el-main>
  </el-container>
</template>

<script>
import { useRoute } from 'vue-router'
export default {
  computed: {
    activeMenu() { return this.$route.path.split('/')[1] || 'brand' }
  }
}
</script>
''',

    # ── router/index.js ──
    "src/router/index.js": '''
import { createRouter, createWebHashHistory } from 'vue-router'
import BrandEngine from '../views/BrandEngine.vue'
import AssetVault from '../views/AssetVault.vue'
import CaseWorkflow from '../views/CaseWorkflow.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/brand' },
    { path: '/brand', name: 'brand', component: BrandEngine },
    { path: '/assets', name: 'assets', component: AssetVault },
    { path: '/workflow', name: 'workflow', component: CaseWorkflow },
  ]
})
''',

    # ── api/bmn.js ──
    "src/api/bmn.js": '''
import axios from 'axios'

const request = axios.create({ baseURL: '/api', timeout: 30000 })

request.interceptors.response.use(
  r => r.data,
  e => Promise.reject(e.response?.data || e)
)

export const getBrandConfig = (name='XX传媒') =>
  request.get(`/v2/bmn/brand/config?brand_name=${encodeURIComponent(name)}`)

export const upsertBrandConfig = (data) =>
  request.put('/v2/bmn/brand/config', data)

export const getMasterPrompt = (name='XX传媒') =>
  request.get(`/v2/bmn/brand/master_prompt?brand_name=${encodeURIComponent(name)}`)

export const listAssets = (params) =>
  request.get('/v2/bmn/assets', { params })

export const searchAssets = (data) =>
  request.post('/v2/bmn/assets/search', data)

export const addAsset = (data) =>
  request.post('/v2/bmn/assets', data)

export const deleteAsset = (id) =>
  request.delete(`/v2/bmn/assets/${id}`)

export const runCaseStudy = (data) =>
  request.post('/v2/bmn/workflows/case_study/run', data)
''',

    # ── views/BrandEngine.vue ──
    "src/views/BrandEngine.vue": '''
<template>
  <div style="max-width:900px;margin:0 auto">
    <el-card>
      <template #header><b>L1 品牌逻辑引擎</b></template>
      <el-form :model="form" label-width="100px" style="padding:10px">
        <el-form-item label="品牌名称"><el-input v-model="form.brand_name"/></el-form-item>
        <el-form-item label="身份定位"><el-input v-model="form.identity" type="textarea":rows="2"/></el-form-item>
        <el-form-item label="价值定位"><el-input v-model="form.value_proposition" type="textarea":rows="2"/></el-form-item>
        <el-form-item label="信任背书">
          <div v-for="(t,i) in form.trust_proof" :key="i" style="display:flex;gap:8px;margin-bottom:8px">
            <el-input v-model="form.trust_proof[i]" style="flex:1"/>
            <el-button type="danger" :icon="Delete" @click="form.trust_proof.splice(i,1)"/>
          </div>
          <el-button :icon="Plus" @click="form.trust_proof.push('')">添加</el-button>
        </el-form-item>
        <el-form-item label="差异化"><el-input v-model="form.differentiation" type="textarea":rows="2"/></el-form-item>
        <el-form-item>
          <el-button type="primary" @click="save" :loading="saving">保存并生成母指令</el-button>
          <el-button @click="load">重新加载</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top:16px" v-if="masterPrompt">
      <template #header><b>母指令（Master Prompt）</b></template>
      <el-input type="textarea" :rows="10" v-model="masterPrompt" readonly/>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import * as api from '../api/bmn'

const form = ref({ brand_name:'XX传媒', identity:'', value_proposition:'', trust_proof:[], differentiation:'' })
const masterPrompt = ref('')
const saving = ref(false)

const load = async () => {
  try {
    const r = await api.getBrandConfig(form.value.brand_name)
    form.value = { ...form.value, ...r, trust_proof: r.trust_proof || [] }
    const p = await api.getMasterPrompt(form.value.brand_name)
    masterPrompt.value = p.master_prompt || ''
  } catch(e) { console.warn(e) }
}
const save = async () => {
  saving.value = true
  try {
    await api.upsertBrandConfig(form.value)
    await load()
    ElMessage.success('保存成功，母指令已更新')
  } finally { saving.value = false }
}
onMounted(load)
</script>
''',

    # ── views/AssetVault.vue ──
    "src/views/AssetVault.vue": '''
<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <b>L2 资产金库</b>
          <div>
            <el-input v-model="searchQ" placeholder="搜索资产..." style="width:200px" clearable @clear="load" @keyup.enter="search"/>
            <el-button type="primary" @click="search" style="margin-left:8px">搜索</el-button>
            <el-button type="success" @click="showAdd=true">+ 新增资产</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeType" @tab-change="load">
        <el-tab-pane label="全部" name=""/>
        <el-tab-pane label="品牌诉求" name="brand_appeal"/>
        <el-tab-pane label="产品卖点" name="product_selling"/>
        <el-tab-pane label="用户场景" name="user_scenario"/>
        <el-tab-pane label="客户案例" name="customer_case"/>
        <el-tab-pane label="行业知识" name="industry_knowledge"/>
        <el-tab-pane label="视觉资产" name="visual_asset"/>
        <el-tab-pane label="问答口径" name="qa_script"/>
        <el-tab-pane label="风险边界" name="risk_boundary"/>
      </el-tabs>

      <el-table :data="assets" style="width:100%" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="200"/>
        <el-table-column prop="asset_type" label="类型" width="120"/>
        <el-table-column prop="source" label="来源" width="120"/>
        <el-table-column prop="usage_count" label="使用次数" width="90" align="center"/>
        <el-table-column label="操作" width="160" align="center">
          <template #default="{row}">
            <el-button size="small" @click="view(row)">查看</el-button>
            <el-button size="small" type="danger" @click="del(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:16px;text-align:center" v-model:current-page="page" :total="total" :page-size="pageSize" @current-change="load"/>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showAdd" :title="editing?'编辑资产':'新增资产'" width="700px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="form.asset_type">
            <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value"/>
          </el-select>
        </el-form-item>
        <el-form-item label="标题"><el-input v-model="form.title"/></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="8"/></el-form-item>
        <el-form-item label="标签"><el-input v-model="form.tagsStr" placeholder="逗号分隔"/></el-form-item>
        <el-form-item label="来源"><el-input v-model="form.source"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd=false">取消</el-button>
        <el-button type="primary" @click="saveAsset">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog v-model="showView" title="资产详情" width="800px">
      <pre style="white-space:pre-wrap;max-height:60vh;overflow:auto">{{viewContent}}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as api from '../api/bmn'

const assets = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const searchQ = ref('')
const activeType = ref('')
const showAdd = ref(false)
const showView = ref(false)
const editing = ref(false)
const viewContent = ref('')
const form = ref({ asset_type:'brand_appeal', title:'', content:'', tagsStr:'', source:'', tags:[] })
const typeOptions = [
  { label:'品牌诉求', value:'brand_appeal' },
  { label:'产品卖点', value:'product_selling' },
  { label:'用户场景', value:'user_scenario' },
  { label:'客户案例', value:'customer_case' },
  { label:'行业知识', value:'industry_knowledge' },
  { label:'视觉资产', value:'visual_asset' },
  { label:'问答口径', value:'qa_script' },
  { label:'风险边界', value:'risk_boundary' },
]

const load = async () => {
  loading.value = true
  try {
    const r = await api.listAssets({
      asset_type: activeType.value || undefined,
      keyword: searchQ.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    assets.value = r.items || []
    total.value = r.total || 0
  } finally { loading.value = false }
}

const search = () => { page.value = 1; load() }

const view = (row) => {
  viewContent.value = row.content || ''
  showView.value = true
}

const del = async (row) => {
  await ElMessageBox.confirm('确定删除该资产?', '提示', { type:'warning' })
  await api.deleteAsset(row.id)
  ElMessage.success('已删除')
  load()
}

const saveAsset = async () => {
  form.value.tags = form.value.tagsStr.split(/[,，]/).map(s=>s.trim()).filter(Boolean)
  await api.addAsset(form.value)
  ElMessage.success('保存成功')
  showAdd.value = false
  load()
}

onMounted(load)
</script>
''',

    # ── views/CaseWorkflow.vue ──
    "src/views/CaseWorkflow.vue": '''
<template>
  <div style="max-width:900px;margin:0 auto">
    <el-card>
      <template #header><b>L3 客户案例生成工作流</b></template>
      <el-form :model="form" label-width="90px" style="padding:10px">
        <el-form-item label="客户名称"><el-input v-model="form.client_name" placeholder="如：某药店连锁品牌"/></el-form-item>
        <el-form-item label="所属行业"><el-input v-model="form.industry" placeholder="如：医药、日化、家电"/></el-form-item>
        <el-form-item label="原始素材">
          <el-input v-model="form.raw_material" type="textarea" :rows="6" placeholder="粘贴客户提供的背景素材、过往案例、产品介绍等..."/>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="run" :loading="running" size="large">🚀 运行工作流</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top:16px" v-if="result">
      <template #header><b>生成结果</b></template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="小红书文案" name="xhs">
          <pre style="white-space:pre-wrap;background:#f5f5f5;padding:16px;border-radius:8px">{{result.copies?.xhs || '（未生成）'}}</pre>
        </el-tab-pane>
        <el-tab-pane label="朋友圈文案" name="moments">
          <pre style="white-space:pre-wrap;background:#f5f5f5;padding:16px;border-radius:8px">{{result.copies?.moments || '（未生成）'}}</pre>
        </el-tab-pane>
        <el-tab-pane label="PPT大纲" name="ppt">
          <pre style="white-space:pre-wrap;background:#f5f5f5;padding:16px;border-radius:8px">{{result.copies?.ppt_outline || '（未生成）'}}</pre>
        </el-tab-pane>
        <el-tab-pane label="合规检查" name="compliance">
          <div v-for="(c,i) in (compliance || [])" :key="i" style="padding:8px;margin:4px 0;background:#f5f5f5;border-radius:6px">{{c}}</div>
          <el-empty v-if="!compliance?.length" description="暂未检查"/>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import * as api from '../api/bmn'

const form = ref({ client_name:'', industry:'', raw_material:'' })
const running = ref(false)
const result = ref(null)
const compliance = ref([])
const activeTab = ref('xhs')

const run = async () => {
  if (!form.value.client_name || !form.value.raw_material) {
    ElMessage.warning('请填写客户名称和原始素材')
    return
  }
  running.value = true
  try {
    const r = await api.runCaseStudy(form.value)
    result.value = r.result || {}
    compliance.value = r.compliance || []
    ElMessage.success('工作流执行完成！')
    activeTab.value = 'xhs'
  } catch(e) {
    ElMessage.error(e.message || '执行失败')
  } finally { running.value = false }
}
</script>
''',

}

# ── 写入所有文件 ─────────────────────────────────────
count = 0
for rel_path, content in files.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    # 去掉模板字符串的三重引号标记
    cleaned = content.strip().replace(/^\'&/, '').replace(/^\'&/, '').strip()
    # 保留 JS 代码原样写入
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    print(f"  ✅ {rel_path}")
    count += 1

print(f"\n完成！共写入 {count} 个文件")
print(f"启动前端：")
print(f"  cd {BASE}")
print(f"  npm install")
print(f"  npm run dev")

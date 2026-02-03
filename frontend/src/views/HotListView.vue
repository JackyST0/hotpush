<template>
    <div>
        <!-- Category Tabs -->
        <div class="category-container rounded-xl p-2 mb-6 inline-flex flex-wrap gap-2">
            <button
                v-for="cat in categories"
                :key="cat"
                @click="activeCategory = cat"
                :class="['category-chip', activeCategory === cat ? 'active' : '']"
            >
                {{ cat }}
            </button>
        </div>

        <!-- Loading Progress -->
        <div v-if="loading && fetchProgress.total > 0" class="glass rounded-lg p-5 mb-4">
            <div class="flex items-center justify-between mb-3">
                <span class="text-gray-400 text-xs">
                    <i class="fas fa-sync-alt animate-spin mr-1.5 text-gray-500"></i>
                    正在获取数据源...
                </span>
                <span class="text-white text-xs">
                    {{ fetchProgress.completed }} / {{ fetchProgress.total }}
                </span>
            </div>
            <div class="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                <div
                    class="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-300 ease-out"
                    :style="{ width: fetchProgress.total ? (fetchProgress.completed / fetchProgress.total * 100) + '%' : '0%' }"
                ></div>
            </div>
            <div class="text-xs text-gray-500 mt-4">
                已成功获取 {{ fetchProgress.success }} 个数据源
            </div>
        </div>

        <!-- Failed Sources Alert -->
        <div v-if="!loading && failedSources.length > 0" class="glass rounded-lg p-4 mb-4 border border-amber-500/30">
            <div class="flex items-start space-x-3">
                <div class="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-exclamation-triangle text-amber-400 text-sm"></i>
                </div>
                <div class="flex-1">
                    <p class="text-amber-400 text-sm font-medium mb-1">
                        {{ failedSources.length }} 个数据源加载失败
                    </p>
                    <p class="text-gray-400 text-xs">
                        {{ failedSources.map(s => s.source_name).join('、') }}
                    </p>
                    <p class="text-gray-500 text-xs mt-2">
                        可能原因：需要配置 Cookie、网络问题或数据源暂时不可用
                    </p>
                </div>
            </div>
        </div>

        <!-- Loading Skeleton -->
        <div v-if="loading && hotLists.length === 0" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            <div v-for="i in 6" :key="i" class="glass rounded-xl p-4">
                <div class="flex items-center space-x-3 mb-4">
                    <div class="w-10 h-10 rounded-lg skeleton"></div>
                    <div class="flex-1">
                        <div class="h-4 w-24 skeleton rounded mb-2"></div>
                        <div class="h-3 w-16 skeleton rounded"></div>
                    </div>
                </div>
                <div class="space-y-3">
                    <div v-for="j in 5" :key="j" class="h-3 skeleton rounded" :style="{ width: (80 + Math.random() * 20) + '%' }"></div>
                </div>
            </div>
        </div>

        <!-- Empty State -->
        <div v-if="!loading && filteredHotLists.length === 0" class="flex justify-center py-16">
            <div class="empty-state-container text-center px-12 py-10 rounded-2xl">
                <div class="text-6xl mb-5">📭</div>
                <p class="text-lg font-medium text-white mb-2">暂无数据</p>
                <p class="text-gray-400 text-sm">该分类下暂时没有热搜内容</p>
                <button @click="fetchHotLists" class="action-chip mt-6">
                    <i class="fas fa-sync-alt mr-2"></i>刷新试试
                </button>
            </div>
        </div>

        <!-- Hot Lists Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            <div
                v-for="hotList in filteredHotLists"
                :key="hotList.source"
                class="glass rounded-xl card-hover overflow-hidden"
            >
                <!-- Card Header -->
                <div class="p-4 border-b border-white/5 flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                            <img 
                                v-if="hotList.icon" 
                                :src="hotList.icon" 
                                class="w-6 h-6 rounded"
                                @error="$event.target.style.display='none'"
                            >
                            <i v-else class="fas fa-fire text-amber-400"></i>
                        </div>
                        <h3 class="font-semibold text-white text-sm">{{ hotList.source_name }}</h3>
                    </div>
                    <span class="text-xs text-gray-500">{{ formatTime(new Date()) }}</span>
                </div>

                <!-- Card Content -->
                <ul class="p-4 space-y-2">
                    <li
                        v-for="(item, index) in (hotList.items || []).slice(0, 10)"
                        :key="item.id || index"
                        class="hot-item flex items-start space-x-3 group cursor-pointer"
                        @click="openLink(item.url)"
                    >
                        <span :class="[
                            'flex-shrink-0 w-5 h-5 rounded flex items-center justify-center text-xs',
                            index < 3 ? 'rank-badge' : 'rank-badge-normal text-gray-500'
                        ]">
                            {{ index + 1 }}
                        </span>
                        <span class="text-xs text-gray-400 group-hover:text-white transition line-clamp-2">
                            {{ item.title }}
                        </span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useApi } from '../composables/useApi'
import { useAppStore } from '../stores/app'

const { API_BASE, authToken, getHeaders } = useApi()
const appStore = useAppStore()

// Source icons mapping
const sourceIcons = {
    weibo: '🔥',
    zhihu: '💡',
    bilibili: '📺',
    douyin: '🎵',
    toutiao: '📰',
    baidu: '🔍',
    linuxdo: '🐧',
    v2ex: '💻',
    hackernews: '🔶',
    juejin: '💎',
    douban: '🎬',
    sspai: '📱',
    thepaper: '📋',
    zaobao: '🌏'
}

// State
const hotLists = ref([])
const failedSources = ref([])
const loading = ref(false)
const activeCategory = ref('全部')
const fetchProgress = ref({ completed: 0, total: 0, success: 0 })
let eventSource = null

const categories = ['全部', '热搜榜', '技术', '科技资讯', '视频', '影视', '阅读', '新闻', '自定义']

// Category mapping - 和旧版本保持一致
const categoryMap = {
    '热搜榜': ['weibo', 'zhihu'],
    '技术': ['v2ex', 'hackernews', 'juejin', 'linuxdo', 'nodeweekly', 'ruanyifeng'],
    '科技资讯': ['sspai', 'ifanr', 'pingwest'],
    '视频': ['bilibili'],
    '影视': ['douban_movie'],
    '阅读': ['douban_book'],
    '新闻': ['zaobao', 'thepaper']
}

// 自定义源列表
const customSourceIds = ref([])

// 获取自定义源
const fetchCustomSources = async () => {
    try {
        const response = await fetch(`${API_BASE}/sources/custom`, {
            headers: getHeaders()
        })
        if (response.ok) {
            const data = await response.json()
            customSourceIds.value = (data.sources || []).map(s => s.id)
        }
    } catch (e) {
        console.error('获取自定义源失败:', e)
    }
}

// Computed
const filteredHotLists = computed(() => {
    if (activeCategory.value === '全部') return hotLists.value
    if (activeCategory.value === '自定义') {
        return hotLists.value.filter(h => customSourceIds.value.includes(h.source))
    }
    const sources = categoryMap[activeCategory.value] || []
    return hotLists.value.filter(h => sources.includes(h.source))
})

// Methods
const getSourceIcon = (source) => {
    return sourceIcons[source] || '📰'
}

const fetchHotLists = () => {
    if (eventSource) {
        eventSource.close()
        eventSource = null
    }

    loading.value = true
    hotLists.value = []
    failedSources.value = []
    fetchProgress.value = { completed: 0, total: 0, success: 0 }

    let url = `${API_BASE}/hot/stream`
    if (authToken.value) {
        url += `?token=${authToken.value}`
    }

    eventSource = new EventSource(url)

    eventSource.addEventListener('start', (e) => {
        const data = JSON.parse(e.data)
        fetchProgress.value.total = data.total
    })

    eventSource.addEventListener('hotlist', (e) => {
        const data = JSON.parse(e.data)
        hotLists.value.push(data)
        fetchProgress.value.completed = hotLists.value.length
        fetchProgress.value.success = hotLists.value.length
    })

    eventSource.addEventListener('failed', (e) => {
        const data = JSON.parse(e.data)
        failedSources.value.push(data)
    })

    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data)
        fetchProgress.value = data
    })

    eventSource.addEventListener('done', () => {
        loading.value = false
        if (eventSource) {
            eventSource.close()
            eventSource = null
        }
    })

    eventSource.addEventListener('error', () => {
        loading.value = false
        if (eventSource) {
            eventSource.close()
            eventSource = null
        }
    })
}

const formatTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const openLink = (url) => {
    if (url) window.open(url, '_blank')
}

// Watch for refresh trigger from header
watch(() => appStore.refreshTrigger, (newVal) => {
    // Skip initial value (0)
    if (newVal > 0) {
        fetchHotLists()
    }
})

// Lifecycle
onMounted(() => {
    fetchHotLists()
    fetchCustomSources()
})

onUnmounted(() => {
    if (eventSource) {
        eventSource.close()
    }
})
</script>

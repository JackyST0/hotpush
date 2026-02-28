<template>
    <div>
        <!-- Time Range Selector -->
        <div class="flex items-center justify-between mb-6">
            <div class="category-container rounded-xl p-2 inline-flex gap-2">
                <button
                    v-for="range in timeRanges"
                    :key="range.value"
                    @click="selectedHours = range.value; loadData()"
                    :class="['category-chip', selectedHours === range.value ? 'active' : '']"
                >
                    {{ range.label }}
                </button>
            </div>
        </div>

        <!-- Platform Overview -->
        <div class="glass rounded-xl p-6 mb-6">
            <h3 class="text-white font-semibold mb-4">
                <i class="fas fa-chart-bar text-amber-400 mr-2"></i>各平台热搜数量
            </h3>
            <div v-if="overviewLoading" class="flex items-center justify-center py-8">
                <i class="fas fa-spinner animate-spin text-gray-500 mr-2"></i>
                <span class="text-gray-500 text-sm">加载中...</span>
            </div>
            <div v-else-if="overviewData.length === 0" class="text-center py-8 text-gray-500 text-sm">
                <i class="fas fa-chart-bar text-gray-600 text-3xl mb-3 block"></i>
                暂无数据，等待首次抓取后即可查看趋势
            </div>
            <div v-else class="chart-container" style="height: 280px;">
                <Bar :data="overviewChartData" :options="overviewChartOptions" />
            </div>
        </div>

        <!-- Top Trending Items -->
        <div class="glass rounded-xl p-6 mb-6">
            <h3 class="text-white font-semibold mb-4">
                <i class="fas fa-fire text-orange-400 mr-2"></i>热度排行
            </h3>
            <div v-if="topLoading" class="flex items-center justify-center py-8">
                <i class="fas fa-spinner animate-spin text-gray-500 mr-2"></i>
                <span class="text-gray-500 text-sm">加载中...</span>
            </div>
            <div v-else-if="topItems.length === 0" class="text-center py-8 text-gray-500 text-sm">
                <i class="fas fa-fire text-gray-600 text-3xl mb-3 block"></i>
                暂无数据
            </div>
            <div v-else class="space-y-2">
                <div
                    v-for="(item, index) in topItems"
                    :key="item.item_id"
                    class="flex items-center space-x-3 p-3 rounded-lg hover:bg-white/5 transition cursor-pointer"
                    @click="viewItemTrend(item)"
                >
                    <div :class="[
                        'w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0',
                        index < 3 ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white' : 'bg-white/10 text-gray-400'
                    ]">
                        {{ index + 1 }}
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm text-white truncate">{{ item.title }}</div>
                        <div class="text-xs text-gray-500 mt-0.5">
                            {{ item.source_name }} · 出现 {{ item.appearances }} 次 · 最高第 {{ item.best_rank }} 名
                        </div>
                    </div>
                    <div class="text-xs text-gray-500 flex-shrink-0">
                        平均 #{{ item.avg_rank }}
                    </div>
                </div>
            </div>
        </div>

        <!-- Ranking Trend Chart -->
        <div class="glass rounded-xl p-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-white font-semibold">
                    <i class="fas fa-chart-line text-blue-400 mr-2"></i>排名变化趋势
                </h3>
                <select
                    v-model="selectedSource"
                    @change="loadRankingTrend"
                    class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white outline-none focus:ring-2 focus:ring-amber-500/50"
                >
                    <option value="" disabled>选择平台</option>
                    <option v-for="s in availableSources" :key="s.id" :value="s.id">
                        {{ s.name }}
                    </option>
                </select>
            </div>
            <div v-if="rankingLoading" class="flex items-center justify-center py-8">
                <i class="fas fa-spinner animate-spin text-gray-500 mr-2"></i>
                <span class="text-gray-500 text-sm">加载中...</span>
            </div>
            <div v-else-if="!selectedSource" class="text-center py-8 text-gray-500 text-sm">
                <i class="fas fa-hand-pointer text-gray-600 text-3xl mb-3 block"></i>
                请选择一个平台查看排名趋势
            </div>
            <div v-else-if="rankingData.items.length === 0" class="text-center py-8 text-gray-500 text-sm">
                <i class="fas fa-chart-line text-gray-600 text-3xl mb-3 block"></i>
                该平台暂无趋势数据
            </div>
            <div v-else class="chart-container" style="height: 400px;">
                <Line :data="rankingChartData" :options="rankingChartOptions" />
            </div>
        </div>

        <!-- Item Trend Modal -->
        <div v-if="showItemModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showItemModal = false">
            <div class="glass rounded-2xl p-6 w-full max-w-2xl mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white truncate pr-4">{{ selectedItem?.title }}</h3>
                    <button @click="showItemModal = false" class="text-gray-500 hover:text-white transition flex-shrink-0">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div v-if="itemTrendLoading" class="flex items-center justify-center py-8">
                    <i class="fas fa-spinner animate-spin text-gray-500 mr-2"></i>
                </div>
                <div v-else-if="itemTrendData.length === 0" class="text-center py-8 text-gray-500 text-sm">
                    暂无趋势数据
                </div>
                <div v-else class="chart-container" style="height: 300px;">
                    <Line :data="itemTrendChartData" :options="itemTrendChartOptions" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js'
import { Line, Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler)

const authStore = useAuthStore()

const timeRanges = [
    { label: '6 小时', value: 6 },
    { label: '12 小时', value: 12 },
    { label: '24 小时', value: 24 },
    { label: '3 天', value: 72 },
    { label: '7 天', value: 168 },
]

const selectedHours = ref(24)
const selectedSource = ref('')

const overviewData = ref([])
const overviewLoading = ref(false)
const topItems = ref([])
const topLoading = ref(false)
const rankingData = ref({ items: [], time_points: [] })
const rankingLoading = ref(false)

const showItemModal = ref(false)
const selectedItem = ref(null)
const itemTrendData = ref([])
const itemTrendLoading = ref(false)

const CHART_COLORS = [
    '#f59e0b', '#ef4444', '#3b82f6', '#10b981', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
    '#06b6d4', '#e11d48', '#a855f7', '#22c55e', '#0ea5e9',
]

const availableSources = computed(() => {
    return overviewData.value.map(p => ({
        id: p.source,
        name: p.source_name
    }))
})

async function fetchApi(url) {
    const headers = {}
    if (authStore.token) {
        headers['Authorization'] = `Bearer ${authStore.token}`
    }
    const res = await fetch(url, { headers })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    return res.json()
}

async function loadData() {
    loadOverview()
    loadTopItems()
    if (selectedSource.value) loadRankingTrend()
}

async function loadOverview() {
    overviewLoading.value = true
    try {
        const data = await fetchApi(`/api/trends/overview?hours=${selectedHours.value}`)
        overviewData.value = data.platforms || []
    } catch (e) {
        console.error('Failed to load overview:', e)
    } finally {
        overviewLoading.value = false
    }
}

async function loadTopItems() {
    topLoading.value = true
    try {
        const data = await fetchApi(`/api/trends/top?hours=${selectedHours.value}&limit=15`)
        topItems.value = data.items || []
    } catch (e) {
        console.error('Failed to load top items:', e)
    } finally {
        topLoading.value = false
    }
}

async function loadRankingTrend() {
    if (!selectedSource.value) return
    rankingLoading.value = true
    try {
        const data = await fetchApi(`/api/trends/ranking/${selectedSource.value}?hours=${selectedHours.value}`)
        rankingData.value = data
    } catch (e) {
        console.error('Failed to load ranking trend:', e)
    } finally {
        rankingLoading.value = false
    }
}

async function viewItemTrend(item) {
    selectedItem.value = item
    showItemModal.value = true
    itemTrendLoading.value = true
    try {
        const data = await fetchApi(`/api/trends/item/${item.item_id}?hours=${selectedHours.value}`)
        itemTrendData.value = data.data || []
    } catch (e) {
        console.error('Failed to load item trend:', e)
    } finally {
        itemTrendLoading.value = false
    }
}

const overviewChartData = computed(() => ({
    labels: overviewData.value.map(p => p.source_name),
    datasets: [{
        label: '热搜条目数',
        data: overviewData.value.map(p => p.item_count),
        backgroundColor: overviewData.value.map((_, i) => CHART_COLORS[i % CHART_COLORS.length] + '80'),
        borderColor: overviewData.value.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
        borderWidth: 1,
        borderRadius: 6,
    }]
}))

const overviewChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            titleColor: '#fff',
            bodyColor: '#ddd',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
        }
    },
    scales: {
        x: {
            ticks: { color: '#9ca3af', font: { size: 11 } },
            grid: { color: 'rgba(255,255,255,0.05)' }
        },
        y: {
            ticks: { color: '#9ca3af', font: { size: 11 } },
            grid: { color: 'rgba(255,255,255,0.05)' },
            beginAtZero: true,
        }
    }
}

function formatTime(timeStr) {
    const d = new Date(timeStr)
    const h = d.getHours().toString().padStart(2, '0')
    const m = d.getMinutes().toString().padStart(2, '0')
    if (selectedHours.value > 48) {
        return `${d.getMonth() + 1}/${d.getDate()} ${h}:${m}`
    }
    return `${h}:${m}`
}

const rankingChartData = computed(() => {
    const items = rankingData.value.items || []
    const timePoints = (rankingData.value.time_points || []).map(formatTime)

    return {
        labels: timePoints,
        datasets: items.map((item, i) => ({
            label: item.title.length > 15 ? item.title.substring(0, 15) + '...' : item.title,
            data: item.ranks,
            borderColor: CHART_COLORS[i % CHART_COLORS.length],
            backgroundColor: CHART_COLORS[i % CHART_COLORS.length] + '20',
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5,
            tension: 0.3,
            spanGaps: true,
        }))
    }
})

const rankingChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: { color: '#9ca3af', font: { size: 11 }, boxWidth: 12, padding: 15 }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            titleColor: '#fff',
            bodyColor: '#ddd',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            callbacks: {
                label: (ctx) => `${ctx.dataset.label}: 第 ${ctx.raw} 名`
            }
        }
    },
    scales: {
        x: {
            ticks: { color: '#9ca3af', font: { size: 10 }, maxRotation: 45 },
            grid: { color: 'rgba(255,255,255,0.05)' }
        },
        y: {
            reverse: true,
            min: 1,
            ticks: {
                color: '#9ca3af',
                font: { size: 11 },
                stepSize: 1,
                callback: (val) => `#${val}`
            },
            grid: { color: 'rgba(255,255,255,0.05)' },
            title: { display: true, text: '排名', color: '#6b7280', font: { size: 12 } }
        }
    }
}

const itemTrendChartData = computed(() => ({
    labels: itemTrendData.value.map(d => formatTime(d.snapshot_time)),
    datasets: [{
        label: selectedItem.value?.title || '',
        data: itemTrendData.value.map(d => d.rank),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        tension: 0.3,
        fill: true,
    }]
}))

const itemTrendChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            callbacks: {
                label: (ctx) => `排名: 第 ${ctx.raw} 名`
            }
        }
    },
    scales: {
        x: {
            ticks: { color: '#9ca3af', font: { size: 10 } },
            grid: { color: 'rgba(255,255,255,0.05)' }
        },
        y: {
            reverse: true,
            min: 1,
            ticks: {
                color: '#9ca3af',
                stepSize: 1,
                callback: (val) => `#${val}`
            },
            grid: { color: 'rgba(255,255,255,0.05)' }
        }
    }
}

onMounted(() => {
    loadData()
})
</script>

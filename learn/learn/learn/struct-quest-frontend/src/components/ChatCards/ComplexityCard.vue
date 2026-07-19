<template>
  <div class="complexity-card">
    <!-- 时间复杂度 / 空间复杂度 摘要 -->
    <div class="complexity-summary">
      <div v-if="data.time_complexity" class="comp-item">
        <span class="comp-label">⏱ 时间复杂度</span>
        <span class="comp-value">{{ data.time_complexity }}</span>
      </div>
      <div v-if="data.space_complexity" class="comp-item">
        <span class="comp-label">💾 空间复杂度</span>
        <span class="comp-value">{{ data.space_complexity }}</span>
      </div>
    </div>

    <!-- ECharts 图表 -->
    <div v-if="chartOption" class="chart-wrapper">
      <v-chart :option="chartOption" autoresize style="height:200px" />
    </div>

    <!-- 表格数据 -->
    <div v-if="data.table_data?.length" class="table-wrapper">
      <table class="comp-table">
        <thead>
          <tr>
            <th v-for="(h, hi) in tableHeaders" :key="hi">{{ h }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, ri) in data.table_data" :key="ri">
            <td v-for="(h, hi) in tableHeaders" :key="hi">{{ row[h] || '' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
})

const tableHeaders = computed(() => {
  if (!props.data.table_data?.length) return []
  return Object.keys(props.data.table_data[0] || {})
})

const chartOption = computed(() => {
  const cd = props.data.chart_data
  if (!cd?.labels?.length) return null

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: Object.keys(cd.series || {}), bottom: 0, textStyle: { fontSize: 10 } },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: cd.labels, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value', show: false },
    series: Object.entries(cd.series || {}).map(([name, vals]) => ({
      name,
      type: 'bar',
      data: vals.map((v) => {
        // 尝试提取复杂度级别
        const m = String(v).match(/O\((\w+)\)/i) || String(v).match(/o\((\w+)\)/i)
        if (!m) return 0
        const inner = m[1].toLowerCase().replace(/\s/g, '')
        if (inner === '1') return 1
        if (inner === 'logn' || inner === 'logn') return 2
        if (inner === 'n') return 3
        if (inner.includes('nlogn') || inner.includes('nlogn')) return 4
        if (inner.includes('n²') || inner.includes('n^2') || inner.includes('n2')) return 5
        if (inner.includes('n³') || inner.includes('n^3') || inner.includes('n3')) return 6
        if (inner.includes('2^n') || inner.includes('2**n')) return 7
        return 0
      }),
      barMaxWidth: 40,
    })),
  }
})
</script>

<style scoped>
.complexity-card {
  font-size: 14px;
}

.complexity-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.comp-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f8fafc;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.comp-label {
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
}
.comp-value {
  font-family: 'SF Mono', 'Fira Code', monospace;
  color: #c84c5a;
  font-weight: 700;
}

.chart-wrapper {
  margin-bottom: 14px;
}

.table-wrapper {
  overflow-x: auto;
}

.comp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.comp-table th {
  background: #f1f5f9;
  padding: 8px 10px;
  text-align: left;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
}
.comp-table td {
  padding: 7px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}
.comp-table tr:hover td {
  background: #f8fafc;
}
</style>


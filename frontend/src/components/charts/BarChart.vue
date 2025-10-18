<!-- File: security_mgmt_dev/frontend/src/components/charts/BarChart.vue -->
<template>
  <div style="height:360px"><canvas ref="canvas"></canvas></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { Chart } from 'chart.js/auto'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  title: { type: String, default: '' }
})
const canvas = ref(null)
let chart

function render () {
  if (!canvas.value) return
  if (chart) { chart.destroy(); chart = null }

  const ctx = canvas.value.getContext('2d')
  const gradient = ctx.createLinearGradient(0, 0, 0, 360)
  gradient.addColorStop(0, 'rgba(75, 192, 192, 0.8)')
  gradient.addColorStop(1, 'rgba(75, 192, 192, 0.2)')

  chart = new Chart(canvas.value, {
    type: 'bar',
    data: { 
      labels: props.labels, 
      datasets: [{ 
        label: props.title || 'Series', 
        data: props.series,
        backgroundColor: gradient,
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
        borderRadius: 4,
        hoverBackgroundColor: 'rgba(75, 192, 192, 1)'
      }] 
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false // Hide legend as title is clear enough
        },
        tooltip: {
          backgroundColor: '#2c3e50',
          titleFont: { size: 14 },
          bodyFont: { size: 12 },
          padding: 10,
          cornerRadius: 4,
          displayColors: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: '#e0e0e0'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      }
    }
  })
}
onMounted(render)
onBeforeUnmount(() => { if (chart) chart.destroy() })
watch(() => [props.labels, props.series], render)
</script>

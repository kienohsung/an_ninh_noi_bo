<!-- File: security_mgmt_dev/frontend/src/components/charts/PieChart.vue -->
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

// Helper to generate colors
const generateColors = (numColors) => {
  const colors = []
  for (let i = 0; i < numColors; i++) {
    const hue = (i * 360) / numColors;
    colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
  }
  return colors;
}

function render () {
  if (!canvas.value) return
  if (chart) { chart.destroy(); chart = null }

  chart = new Chart(canvas.value, {
    type: 'pie', // or 'doughnut'
    data: { 
      labels: props.labels, 
      datasets: [{ 
        label: props.title, 
        data: props.series,
        backgroundColor: generateColors(props.labels.length),
        hoverOffset: 4
      }] 
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
            display: true,
            text: props.title
        }
      }
    }
  })
}
onMounted(render)
onBeforeUnmount(() => { if (chart) chart.destroy() })
watch(() => [props.labels, props.series], render)
</script>
